from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Literal

EnvKey = Literal[
    "is_termux", "is_wsl", "is_windows", "is_binary", "is_venv",
    "config_dir", "data_dir", "cache_dir", "temp_dir", "base_path",
    "ffmpeg_cmd", "spotdl_cmd",
    "ytdlp_override_dir", "ytdlp_cache_dir",
    "history_path", "registry_path", "config_path", "cache_path",
    "service_path",
    "default_music_root", "default_video_root", "default_thumbnail_root",
]

APP_NAME = "TetoDL"
APP_VERSION = "2.2.3"


@dataclass
class _EnvData:
    is_termux: bool = False
    is_wsl: bool = False
    is_windows: bool = False
    is_binary: bool = False
    is_venv: bool = False
    config_dir: str = ""
    data_dir: str = ""
    cache_dir: str = ""
    temp_dir: str = ""
    base_path: str = ""
    ffmpeg_cmd: str = "ffmpeg"
    spotdl_cmd: str = "spotdl"
    ytdlp_override_dir: str = ""
    ytdlp_cache_dir: str = ""
    history_path: str = ""
    registry_path: str = ""
    config_path: str = ""
    cache_path: str = ""
    service_path: str = ""
    default_music_root: str = ""
    default_video_root: str = ""
    default_thumbnail_root: str = ""


class Env:
    def __init__(self):
        self._data = _EnvData()
        self._cache_path: str | None = None
        self._detected = False

    def get(self, key: EnvKey):
        if not self._detected:
            self._load_or_detect()
        return getattr(self._data, key)

    def reset(self):
        if self._cache_path and os.path.exists(self._cache_path):
            os.remove(self._cache_path)
        self._detected = False

    def recheck(self) -> bool:
        old: _EnvData | None = None
        if self._cache_path and os.path.exists(self._cache_path):
            try:
                with open(self._cache_path) as f:
                    old = _EnvData(**json.load(f))
            except Exception:
                pass

        self.reset()
        self._load_or_detect()

        if old is None:
            return True

        changed = []
        for field in _EnvData.__dataclass_fields__:
            old_val = getattr(old, field)
            new_val = getattr(self._data, field)
            if old_val != new_val:
                changed.append((field, old_val, new_val))

        if changed:
            for field, old_val, new_val in changed:
                print(f"    {field}: {old_val} -> {new_val}")

        return True

    def initdir(self):
        data = self._data
        dirs = [
            data.config_dir, data.data_dir, data.cache_dir, data.temp_dir,
            data.default_music_root, data.default_video_root,
        ]
        for d in dirs:
            try:
                os.makedirs(d, exist_ok=True)
            except (OSError, PermissionError):
                pass

    def _load_or_detect(self):
        home = Path.home()
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        cfg_dir = (Path(xdg_config) if xdg_config else home / ".config") / APP_NAME
        self._cache_path = str(cfg_dir / "env.cache.json")

        if os.path.exists(self._cache_path):
            try:
                with open(self._cache_path) as f:
                    raw = json.load(f)
                self._data = _EnvData(**raw)
                self._detected = True
                self.initdir()
                return
            except Exception:
                pass

        self._data = self._detect()
        self._detected = True
        self._write_cache()
        self.initdir()

    def _write_cache(self):
        try:
            dir_path = os.path.dirname(self._cache_path) # pyright: ignore[reportArgumentType, reportCallIssue]
            os.makedirs(dir_path, exist_ok=True)
            with open(self._cache_path, "w") as f: # pyright: ignore[reportArgumentType, reportCallIssue]
                json.dump(asdict(self._data), f)
        except Exception:
            pass

    def _detect(self) -> _EnvData:
        d = _EnvData()
        home = Path.home()

        is_binary = getattr(sys, "frozen", False)
        is_termux = os.path.exists("/data/data/com.termux") or "com.termux" in os.environ.get("PREFIX", "")
        is_windows = os.name == "nt"
        is_venv = not is_binary and (sys.prefix != sys.base_prefix)

        is_wsl = False
        if not is_windows and not is_termux:
            try:
                if hasattr(os, "uname") and "microsoft" in os.uname().release.lower():
                    is_wsl = True
                elif os.path.exists("/proc/version"):
                    with open("/proc/version") as f:
                        if "microsoft" in f.read().lower():
                            is_wsl = True
            except (AttributeError, ValueError, OSError):
                pass

        d.is_termux = is_termux
        d.is_wsl = is_wsl
        d.is_windows = is_windows
        d.is_binary = is_binary
        d.is_venv = is_venv

        binary_dir: Path | None
        if is_binary:
            binary_dir = Path(sys.executable).parent
        else:
            binary_dir = None

        if is_termux:
            base_path = Path("/storage/emulated/0/TetoDL")
            config_dir = base_path
            data_dir = base_path
            cache_dir = base_path
            temp_dir = cache_dir / "temp"
            ffmpeg_cmd = "/data/data/com.termux/files/usr/bin/ffmpeg"
            spotdl_cmd = "/data/data/com.termux/files/usr/bin/spotdl"
            wsl_music_override = None
            wsl_video_override = None

        elif is_windows:
            base_path = home / "Downloads" / APP_NAME
            config_dir = home / ".config" / APP_NAME
            data_dir = home / ".local" / "share" / APP_NAME
            cache_dir = home / ".cache" / APP_NAME
            temp_dir = cache_dir / "temp"
            spotdl_cmd = "spotdl"
            wsl_music_override = None
            wsl_video_override = None

            if is_binary:
                assert binary_dir is not None
                bundled = binary_dir / "ffmpeg.exe"
                if not bundled.exists() and hasattr(sys, "_MEIPASS"):
                    bundled = Path(sys._MEIPASS) / "ffmpeg.exe" # pyright: ignore[reportAttributeAccessIssue]
                ffmpeg_cmd = str(bundled) if bundled.exists() else "ffmpeg"
            else:
                ffmpeg_cmd = shutil.which("ffmpeg") or "ffmpeg"

        else:
            xdg_config = os.environ.get("XDG_CONFIG_HOME")
            config_dir = (Path(xdg_config) if xdg_config else home / ".config") / APP_NAME
            xdg_data = os.environ.get("XDG_DATA_HOME")
            data_dir = (Path(xdg_data) if xdg_data else home / ".local" / "share") / APP_NAME
            xdg_cache = os.environ.get("XDG_CACHE_HOME")
            cache_dir = (Path(xdg_cache) if xdg_cache else home / ".cache") / APP_NAME
            temp_dir = cache_dir / "temp"
            if is_wsl:
                try:
                    proc_win = subprocess.run(
                        ["cmd.exe", "/c", "echo %USERPROFILE%"],
                        capture_output=True, text=True, check=True,
                    )
                    win_path_raw = proc_win.stdout.strip()
                    proc_wsl = subprocess.run(
                        ["wslpath", win_path_raw],
                        capture_output=True, text=True, check=True,
                    )
                    wsl_home_path = Path(proc_wsl.stdout.strip())
                    base_path = wsl_home_path / "Downloads" / "TetoDL"
                    wsl_music_override = wsl_home_path / "Music"
                    wsl_video_override = wsl_home_path / "Videos"
                except Exception as e:
                    print(f"WSL Path Error: {e}")
                    base_path = home / "Downloads" / APP_NAME
            else:
                base_path = home / "Downloads" / "TetoDL"

            ffmpeg_system = shutil.which("ffmpeg")
            if ffmpeg_system:
                ffmpeg_cmd = ffmpeg_system
            elif os.path.exists("/usr/bin/ffmpeg"):
                ffmpeg_cmd = "/usr/bin/ffmpeg"
            else:
                ffmpeg_venv = os.path.join(sys.prefix, "bin", "ffmpeg")
                ffmpeg_cmd = ffmpeg_venv if os.path.exists(ffmpeg_venv) else "ffmpeg"

            if is_venv:
                spotdl_cmd = os.path.join(sys.prefix, "bin", "spotdl")
            else:
                user_local_bin = home / ".local" / "bin" / "spotdl"
                if os.path.exists("/usr/bin/spotdl"):
                    spotdl_cmd = "/usr/bin/spotdl"
                elif user_local_bin.exists():
                    spotdl_cmd = str(user_local_bin)
                else:
                    spotdl_cmd = shutil.which("spotdl") or "spotdl"

        d.config_dir = str(config_dir)
        d.data_dir = str(data_dir)
        d.cache_dir = str(cache_dir)
        d.temp_dir = str(temp_dir)
        d.base_path = str(base_path)
        d.ffmpeg_cmd = ffmpeg_cmd
        d.spotdl_cmd = spotdl_cmd
        d.ytdlp_override_dir = str(data_dir / "yt-dlp-override")
        d.ytdlp_cache_dir = str(cache_dir / "ytdlp")
        d.config_path = str(config_dir / "config.json")
        d.cache_path = str(cache_dir / "cache.json")
        d.history_path = str(data_dir / "history.json")
        d.registry_path = str(data_dir / "registry.json")
        d.service_path = str(Path.home() / ".config" / "systemd" / "user" / "tetodl.service")
        d.default_music_root = str(base_path / "music")
        d.default_video_root = str(base_path / "videos")
        d.default_thumbnail_root = str(base_path / "thumbnails")

        return d


env = Env()
