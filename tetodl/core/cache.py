"""
Multi-layer cache system: in-memory LRU + disk file-per-key with TTL.
"""

import atexit
import gc
import hashlib
import json
import shutil
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..constants import CACHE_DIR
from ..utils.console import console

# ── data types ──────────────────────────────────────────────────────────

@dataclass
class CacheStats:
    mem_entries: int = 0
    disk_entries: int = 0
    disk_bytes: int = 0


class _MemEntry:
    __slots__ = ("created", "ttl", "value")
    def __init__(self, value: Any, created: float, ttl: float) -> None:
        self.value = value
        self.created = created
        self.ttl = ttl


# ── per-namespace configuration ─────────────────────────────────────────

_CACHE_CFG: dict[str, dict[str, Any]] = {
    "yt_metadata": {"default_ttl": 604800, "max_mem": 256},
    "yt_match":    {"default_ttl": 2592000, "max_mem": 128},
    "lyrics":      {"default_ttl": 2592000, "max_mem": 64},
    "cover":       {"default_ttl": 604800, "max_mem": 64},
}

_caches: dict[str, "Cache"] = {}
_caches_lock = threading.Lock()


# ── memory layer (LRU + TTL) ────────────────────────────────────────────

class _MemoryCache:
    def __init__(self, maxsize: int, default_ttl: float) -> None:
        self._data: OrderedDict[str, _MemEntry] = OrderedDict()
        self._maxsize = maxsize
        self._default_ttl = default_ttl
        self._lock = threading.Lock()

    def get(self, key: str) -> Any:
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return None
            if (time.time() - entry.created) >= entry.ttl:
                del self._data[key]
                return None
            self._data.move_to_end(key)
            return entry.value

    def set(self, key: str, value: Any, ttl: float | None = None) -> None:
        with self._lock:
            if len(self._data) >= self._maxsize:
                self._data.popitem(last=False)
            self._data[key] = _MemEntry(
                value=value,
                created=time.time(),
                ttl=ttl if ttl is not None else self._default_ttl,
            )
            self._data.move_to_end(key)

    def __len__(self) -> int:
        with self._lock:
            return len(self._data)

    def clear(self) -> None:
        with self._lock:
            self._data.clear()


# ── disk layer (file-per-key, atomic write, TTL) ────────────────────────

class _DiskCache:
    def __init__(self, namespace: str, default_ttl: float) -> None:
        self._base = CACHE_DIR / "cache" / namespace
        self._default_ttl = default_ttl
        self._lock = threading.Lock()
        self._base.mkdir(parents=True, exist_ok=True)

    # ─ helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _key_to_path(base: Path, key: str) -> Path:
        h = hashlib.md5(key.encode()).hexdigest()
        return base / f"{h}.json"

    @staticmethod
    def _read_entry(path: Path) -> dict | None:
        try:
            with open(path) as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return None

    @staticmethod
    def _is_stale(entry: dict) -> bool:
        return (time.time() - entry["c"]) >= entry["t"]

    def _write_atomic(self, path: Path, payload: dict) -> None:
        tmp = path.with_suffix(".tmp")
        try:
            with open(tmp, "w") as f:
                json.dump(payload, f, separators=(",", ":"))
            tmp.replace(path)
        except OSError:
            tmp.unlink(missing_ok=True)
            raise

    # ─ public api ───────────────────────────────────────────────────

    def has(self, key: str) -> bool:
        return self._key_to_path(self._base, key).is_file()

    def get(self, key: str) -> Any:
        path = self._key_to_path(self._base, key)
        entry = self._read_entry(path)
        if entry is None:
            return None
        if self._is_stale(entry):
            path.unlink(missing_ok=True)
            return None
        return entry["v"]

    def set(self, key: str, value: Any, ttl: float | None = None) -> None:
        path = self._key_to_path(self._base, key)
        payload = {
            "v": value,
            "c": time.time(),
            "t": ttl if ttl is not None else self._default_ttl,
        }
        with self._lock:
            self._write_atomic(path, payload)

    def delete(self, key: str) -> None:
        self._key_to_path(self._base, key).unlink(missing_ok=True)

    def evict(self, max_age: float | None = None) -> int:
        cutoff = time.time() - (max_age if max_age is not None else self._default_ttl)
        removed = 0
        for path in self._base.glob("*.json"):
            entry = self._read_entry(path)
            if entry is None or entry["c"] < cutoff:
                try:
                    path.unlink()
                    removed += 1
                except OSError:
                    pass
        return removed

    def clear(self) -> int:
        n = 0
        for path in self._base.glob("*.json"):
            try:
                path.unlink()
                n += 1
            except OSError:
                pass
        return n

    @property
    def stats(self) -> CacheStats:
        entries = 0
        total = 0
        for path in self._base.glob("*.json"):
            entries += 1
            try:
                total += path.stat().st_size
            except OSError:
                pass
        return CacheStats(disk_entries=entries, disk_bytes=total)


# ── unified facade ──────────────────────────────────────────────────────

class Cache:
    """Hybrid memory + disk cache with TTL.

    Reads hit memory first (O(1)), fall back to disk (O(1) file read),
    then warm memory for subsequent lookups.
    Writes go to memory immediately and mark dirty for lazy disk flush.
    """

    def __init__(
        self,
        *,
        namespace: str,
        max_mem: int = 128,
        default_ttl: float = 86400,
    ) -> None:
        self._namespace = namespace
        self._disk = _DiskCache(namespace, default_ttl)
        self._mem = _MemoryCache(max_mem, default_ttl)
        self._dirty: set[str] = set()

    # ─ public api ───────────────────────────────────────────────────

    def get(self, key: str) -> Any:
        val = self._mem.get(key)
        if val is not None:
            return val
        val = self._disk.get(key)
        if val is not None:
            self._mem.set(key, val)
        return val

    def set(self, key: str, value: Any, ttl: float | None = None) -> None:
        self._mem.set(key, value, ttl)
        self._dirty.add(key)

    def flush(self) -> None:
        for key in list(self._dirty):
            entry = self._mem._data.get(key)
            if entry is not None:
                self._disk.set(key, entry.value, entry.ttl)
        self._dirty.clear()

    def evict(self, max_age: float | None = None) -> int:
        self._mem.clear()
        return self._disk.evict(max_age)

    def clear(self) -> None:
        self._mem.clear()
        self._disk.clear()
        self._dirty.clear()

    @property
    def stats(self) -> CacheStats:
        ds = self._disk.stats
        ds.mem_entries = len(self._mem)
        return ds


# ── factory ─────────────────────────────────────────────────────────────

def get_cache(namespace: str) -> Cache:
    cache = _caches.get(namespace)
    if cache is not None:
        return cache
    with _caches_lock:
        cache = _caches.get(namespace)
        if cache is None:
            cfg = _CACHE_CFG.get(namespace, {})
            cache = Cache(
                namespace=namespace,
                max_mem=cfg.get("max_mem", 128),
                default_ttl=cfg.get("default_ttl", 86400),
            )
            _caches[namespace] = cache
    return cache


# ── backward-compatible exports ────────────────────────────────────────

def get_url_hash(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()


def get_cached_metadata(url: str) -> dict | None:
    try:
        return get_cache("yt_metadata").get(url)
    except Exception:
        return None


def cache_metadata(url: str, metadata: dict, ttl: float | None = None) -> None:
    try:
        get_cache("yt_metadata").set(url, metadata, ttl)
    except Exception:
        pass


def get_cache_size() -> str:
    total = 0
    for ns in _CACHE_CFG:
        d = CACHE_DIR / "cache" / ns
        if d.is_dir():
            total += sum(
                f.stat().st_size for f in d.glob("*") if f.is_file()
            )
    img_dir = CACHE_DIR / "cache" / "images"
    if img_dir.is_dir():
        total += sum(f.stat().st_size for f in img_dir.glob("*") if f.is_file())
    if total < 1024:
        return f"{total} B"
    if total < 1024 * 1024:
        return f"{total / 1024:.1f} KB"
    return f"{total / (1024 * 1024):.1f} MB"


def reset_cache() -> bool:
    root = CACHE_DIR / "cache"
    try:
        if root.is_dir():
            shutil.rmtree(root)
        with _caches_lock:
            _caches.clear()
        gc.collect()
        return True
    except OSError:
        console.err("Failed to reset cache")
        return False


def evict_cache(max_age: float | None = None) -> int:
    total = 0
    for ns in list(_caches):
        total += _caches[ns].evict(max_age)
    for ns in _CACHE_CFG:
        if ns not in _caches:
            c = _DiskCache(ns, _CACHE_CFG[ns].get("default_ttl", 86400))
            total += c.evict(max_age)
    from .image_cache import evict_img_cache
    total += evict_img_cache(max_age)
    return total


# ── flush on exit ───────────────────────────────────────────────────────

def _flush_all() -> None:
    for cache in _caches.values():
        try:
            cache.flush()
        except Exception:
            pass


atexit.register(_flush_all)
