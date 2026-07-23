"""
Constants and Path Configuration
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

# ==== BINARY / FROZEN DETECTION ====
IS_BINARY = getattr(sys, 'frozen', False)

# ==== PLATFORM DETECTION ====
IS_TERMUX = os.path.exists("/data/data/com.termux") or "com.termux" in os.environ.get("PREFIX", "")
IS_WINDOWS = os.name == "nt"
IS_VENV = not IS_BINARY and (sys.prefix != sys.base_prefix)

IS_WSL = False
if not IS_WINDOWS and not IS_TERMUX:
    try:
        if hasattr(os, "uname") and "microsoft" in os.uname().release.lower():
            IS_WSL = True
        elif os.path.exists("/proc/version"):
            with open("/proc/version", "r") as f:
                if "microsoft" in f.read().lower():
                    IS_WSL = True
    except (AttributeError, ValueError, OSError):
        pass

APP_NAME = "TetoDL"
APP_VERSION = "2.2.0"
JITTER = (3.0, 5.0)

# ==== BINARY ROOT (PyInstaller) ====
_BINARY_DIR: Path | None
if IS_BINARY:
    _BINARY_DIR = Path(sys.executable).parent
else:
    _BINARY_DIR = None

# ==== PATH SETUP ====
if IS_TERMUX:
    BASE_PATH = Path("/storage/emulated/0/TetoDL")
    CONFIG_DIR = BASE_PATH
    DATA_DIR = BASE_PATH
    CACHE_DIR = BASE_PATH
    TEMP_DIR = CACHE_DIR / "temp"
    FFMPEG_CMD = "/data/data/com.termux/files/usr/bin/ffmpeg"
    SPOTDL_CMD = "/data/data/com.termux/files/usr/bin/spotdl"

elif IS_WINDOWS:
    home = Path.home()
    BASE_PATH = home / "Downloads" / APP_NAME
    CONFIG_DIR = home / ".config" / APP_NAME
    DATA_DIR = home / ".local" / "share" / APP_NAME
    CACHE_DIR = home / ".cache" / APP_NAME
    TEMP_DIR = CACHE_DIR / "temp"
    SPOTDL_CMD = "spotdl"

    # FFmpeg — bundled binary first, fallback to PATH
    if IS_BINARY:
        assert _BINARY_DIR is not None
        bundled_ffmpeg = _BINARY_DIR / "ffmpeg.exe"
        if not bundled_ffmpeg.exists() and hasattr(sys, '_MEIPASS'):
            bundled_ffmpeg = Path(sys._MEIPASS) / "ffmpeg.exe" # pyright: ignore[reportAttributeAccessIssue]
        FFMPEG_CMD = str(bundled_ffmpeg) if bundled_ffmpeg.exists() else "ffmpeg"
    else:
        FFMPEG_CMD = shutil.which("ffmpeg") or "ffmpeg"

else:
    # --- LINUX / WSL ---
    home = Path.home()

    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    CONFIG_DIR = (Path(xdg_config) if xdg_config else home / ".config") / APP_NAME

    xdg_data = os.environ.get("XDG_DATA_HOME")
    DATA_DIR = (Path(xdg_data) if xdg_data else home / ".local" / "share") / APP_NAME

    xdg_cache = os.environ.get("XDG_CACHE_HOME")
    CACHE_DIR = (Path(xdg_cache) if xdg_cache else home / ".cache") / APP_NAME

    TEMP_DIR = CACHE_DIR / "temp"

    WSL_MUSIC_OVERRIDE: Path | None
    WSL_VIDEO_OVERRIDE: Path | None

    if IS_WSL:
        try:
            proc_win = subprocess.run(
                ["cmd.exe", "/c", "echo %USERPROFILE%"],
                capture_output=True, text=True, check=True
            )
            win_path_raw = proc_win.stdout.strip()
            proc_wsl = subprocess.run(
                ["wslpath", win_path_raw],
                capture_output=True, text=True, check=True
            )
            wsl_home_path = Path(proc_wsl.stdout.strip())
            BASE_PATH = wsl_home_path / "Downloads" / "TetoDL"
            WSL_MUSIC_OVERRIDE = wsl_home_path / "Music"
            WSL_VIDEO_OVERRIDE = wsl_home_path / "Videos"
        except Exception as e:
            print(f"WSL Path Error: {e}")
            BASE_PATH = home / "Downloads" / APP_NAME
            WSL_MUSIC_OVERRIDE = None
            WSL_VIDEO_OVERRIDE = None
    else:
        BASE_PATH = home / "Downloads" / "TetoDL"
        WSL_MUSIC_OVERRIDE = None
        WSL_VIDEO_OVERRIDE = None

    # FFmpeg — system path
    ffmpeg_system = shutil.which("ffmpeg")
    if ffmpeg_system:
        FFMPEG_CMD = ffmpeg_system
    elif os.path.exists("/usr/bin/ffmpeg"):
        FFMPEG_CMD = "/usr/bin/ffmpeg"
    else:
        ffmpeg_venv = os.path.join(sys.prefix, "bin", "ffmpeg")
        FFMPEG_CMD = ffmpeg_venv if os.path.exists(ffmpeg_venv) else "ffmpeg"

    # spotdl
    if IS_VENV:
        SPOTDL_CMD = os.path.join(sys.prefix, "bin", "spotdl")
    else:
        user_local_bin = home / ".local" / "bin" / "spotdl"
        if os.path.exists("/usr/bin/spotdl"):
            SPOTDL_CMD = "/usr/bin/spotdl"
        elif user_local_bin.exists():
            SPOTDL_CMD = str(user_local_bin)
        else:
            SPOTDL_CMD = shutil.which("spotdl") or "spotdl"

# ==== YT-DLP OVERRIDE (binary mode) ====
YTDLP_OVERRIDE_DIR = DATA_DIR / "yt-dlp-override"

# ==== CONFIG FILES ====
CONFIG_PATH = str(CONFIG_DIR / "config.json")
CACHE_PATH = str(CACHE_DIR / "cache.json")
YTDLP_CACHE_DIR = str(CACHE_DIR / "ytdlp")
HISTORY_PATH = str(DATA_DIR / "history.json")
REGISTRY_PATH = str(DATA_DIR / "registry.json")

SERVICE_PATH = str(Path.home() / ".config" / "systemd" / "user" / "tetodl.service")

# ==== DEFAULT ROOTS ====
DEFAULT_MUSIC_ROOT = str(BASE_PATH / "music")
DEFAULT_VIDEO_ROOT = str(BASE_PATH / "videos")
DEFAULT_THUMBNAIL_ROOT = str(BASE_PATH / "thumbnails")

# ==== DOWNLOAD SETTINGS ====
DOWNLOAD_DELAY = 2
MAX_RETRIES = 3
RETRY_DELAY = 2

# ==== OTHER CONFIGURATION ====
VALID_RESOLUTIONS = ["4320p", "2160p", "1440p", "1080p", "720p", "480p", "360p", "240p", "144p"]
VALID_CONTAINERS = ["mp4", "mkv"]
VALID_THUMBNAIL_FORMATS = ["jpg", "png", "webp"]
VALID_CODECS = ["default", "h264", "h265"]
HISTORY_DISPLAY_LIMIT = 20

# ==== AUDIO QUALITY OPTIONS ====
AUDIO_QUALITY_OPTIONS = {
    "mp3": {"ext": "mp3", "bitrate": "~192 kbps", "codec": "MP3 (Lossy)"},
    "m4a": {"ext": "m4a", "bitrate": "~128 kbps", "codec": "AAC (M4A)"},
    "opus": {"ext": "opus", "bitrate": "~160-180 kbps", "codec": "Opus (Best Quality)"},
}

# ==== INITIALIZATION ====
def _init_dirs():
    dirs = [CONFIG_DIR, DATA_DIR, CACHE_DIR, TEMP_DIR,
            Path(DEFAULT_MUSIC_ROOT), Path(DEFAULT_VIDEO_ROOT)]
    for d in dirs:
        try:
            d.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError):
            pass

_init_dirs()