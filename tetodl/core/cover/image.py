from __future__ import annotations

import hashlib
import os
import time
from pathlib import Path

from tetodl.core.domain.env import env
from tetodl.utils.network import get_session

IMG_TTL = 604800
_IMG_DIR = Path(env.get('cache_dir')) / "cache" / "images"


def _url_key(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()


def _data_path(key: str) -> str:
    return str(_IMG_DIR / f"{key}.img")


def _fresh(path: str, ttl: float) -> bool:
    try:
        return (time.time() - os.path.getmtime(path)) < ttl
    except OSError:
        return False


def fetch_image(url: str, ttl: float = IMG_TTL) -> bytes | None:
    _IMG_DIR.mkdir(parents=True, exist_ok=True)
    key = _url_key(url)
    path = _data_path(key)

    if _fresh(path, ttl):
        try:
            with open(path, "rb") as f:
                return f.read()
        except OSError:
            pass

    try:
        resp = get_session().get(url, timeout=10)
        if resp.status_code != 200:
            return None
        data = resp.content
    except Exception:
        return None

    try:
        with open(path, "wb") as f:
            f.write(data)
    except OSError:
        pass

    return data


def clear_img_cache() -> int:
    n = 0
    for f in _IMG_DIR.glob("*"):
        try:
            f.unlink()
            n += 1
        except OSError:
            pass
    return n


def evict_img_cache(max_age: float | None = None) -> int:
    cutoff = time.time() - (max_age if max_age is not None else IMG_TTL)
    n = 0
    for f in _IMG_DIR.glob("*.img"):
        try:
            if f.stat().st_mtime < cutoff:
                f.unlink()
                n += 1
        except OSError:
            pass
    return n


def img_cache_size() -> str:
    total = 0
    for f in _IMG_DIR.glob("*.img"):
        try:
            total += f.stat().st_size
        except OSError:
            pass
    if total < 1024:
        return f"{total} B"
    if total < 1024 * 1024:
        return f"{total / 1024:.1f} KB"
    return f"{total / (1024 * 1024):.1f} MB"
