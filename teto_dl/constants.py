"""
Constants and Path Configuration
"""
import os
import sys
import subprocess
from pathlib import Path

# ==== PLATFORM DETECTION ====
IS_TERMUX = os.path.exists("/data/data/com.termux") or "com.termux" in os.environ.get("PREFIX", "")
IS_WINDOWS = os.name == "nt"
IS_VENV = (sys.prefix != sys.base_prefix)

IS_WSL = False
if not IS_WINDOWS and not IS_TERMUX:
    try:
        # Check 1: uname release (Standard method)
        if hasattr(os, "uname") and "microsoft" in os.uname().release.lower():
            IS_WSL = True
        # Check 2: /proc/version (Fallback method, more robust)
        elif os.path.exists("/proc/version"):
            with open("/proc/version", "r") as f:
                if "microsoft" in f.read().lower():
                    IS_WSL = True
    except (AttributeError, ValueError, OSError):
        pass

APP_NAME = "TetoDL"
APP_VERSION = "1.1.1"

# ==== PATH SETUP ====
if IS_TERMUX:
    # --- ANDROID (Termux) ---
    BASE_PATH = Path("/storage/emulated/0/TetoDL")

    CONFIG_DIR = BASE_PATH
    DATA_DIR = BASE_PATH
    CACHE_DIR = BASE_PATH

    # Binary Paths
    FFMPEG_CMD = "/data/data/com.termux/files/usr/bin/ffmpeg"
    SPOTDL_CMD = "/data/data/com.termux/files/usr/bin/spotdl"

elif IS_WINDOWS:
    # --- PLAIN WINDOWS  ---
    home = Path.home()
    BASE_PATH = home / "Downloads" / APP_NAME
    CONFIG_DIR = home / ".config" / APP_NAME
    DATA_DIR = home / ".local" / "share" / APP_NAME
    CACHE_DIR = home / ".cache" / APP_NAME
    FFMPEG_CMD = "ffmpeg"
    SPOTDL_CMD = "spotdl"

else:
    # --- LINUX ---
    home = Path.home()

    # Config
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    CONFIG_DIR = (Path(xdg_config) if xdg_config else home / ".config") / APP_NAME

    # Data
    xdg_data = os.environ.get("XDG_DATA_HOME")
    DATA_DIR = (Path(xdg_data) if xdg_data else home / ".local" / "share") / APP_NAME
    
    # Cache
    xdg_cache = os.environ.get("XDG_CACHE_HOME")
    CACHE_DIR = (Path(xdg_cache) if xdg_cache else home / ".cache") / APP_NAME

    # Temp
    TEMP_DIR = CACHE_DIR / "temp"

    if IS_WSL:
        # Coba ambil path Windows User Profile secara dinamis
        try:
            # Command ini mengambil path windows (C:\Users\Name) lalu convert ke wsl path (/mnt/c/Users/Name)
            # stderr dibuang agar tidak mengotori terminal jika gagal
            win_home_raw = subprocess.check_output(
                ["wslpath", "$(cmd.exe /c 'echo %USERPROFILE%' 2>/dev/null)"], 
                shell=True, stderr=subprocess.DEVNULL
            ).decode().strip()
            
            # Jika berhasil, arahkan ke Downloads Windows
            win_home = Path(win_home_raw)
            BASE_PATH = win_home / "Downloads" / "TetoDL"
            
            WSL_MUSIC_OVERRIDE = win_home / "Music"
            WSL_VIDEO_OVERRIDE = win_home / "Videos"
        except Exception:
            BASE_PATH = home / "Downloads" / APP_NAME
            WSL_MUSIC_OVERRIDE = None
            WSL_VIDEO_OVERRIDE = None
    else:
        # Native Linux
        BASE_PATH = home / "Downloads" / "TetoDL"
        WSL_MUSIC_OVERRIDE = None
        WSL_VIDEO_OVERRIDE = None

    if os.path.exists("/usr/bin/ffmpeg"):
        FFMPEG_CMD = "/usr/bin/ffmpeg"
    else:
        ffmpeg_venv = os.path.join(sys.prefix, "bin", "ffmpeg")
        FFMPEG_CMD = ffmpeg_venv if os.path.exists(ffmpeg_venv) else "ffmpeg"

    if IS_VENV:
        SPOTDL_CMD = os.path.join(sys.prefix, "bin", "spotdl")
    else:
        user_local_bin = home / ".local" / "bin" / "spotdl"
        if os.path.exists("/usr/bin/spotdl"):
            SPOTDL_CMD = "/usr/bin/spotdl"
        elif user_local_bin.exists():
            SPOTDL_CMD = str(user_local_bin)
        else:
            SPOTDL_CMD = "spotdl"

# ==== CONFIG FILES ====
CONFIG_PATH = str(CONFIG_DIR / "config.json")
CACHE_PATH = str(CACHE_DIR / "cache.json")
HISTORY_PATH = str(DATA_DIR / "history.json")
REGISTRY_PATH = str(DATA_DIR / "registry.json")

# ==== DEFAULT ROOTS ====
DEFAULT_MUSIC_ROOT = str(BASE_PATH / "music")
DEFAULT_VIDEO_ROOT = str(BASE_PATH / "videos")
DEFAULT_THUMBNAIL_ROOT = str(BASE_PATH / "thumbnails")

# ==== DOWNLOAD SETTINGS ====
DOWNLOAD_DELAY = 2
MAX_RETRIES = 3
RETRY_DELAY = 2

# ==== OTHER CONFIGURATION ====
VALID_RESOLUTIONS = ["4320p", "2160p", "1440p", "1080p", "720p", "480p"]
VALID_CONTAINERS = ["mp4", "mkv"]
VALID_THUMBNAIL_FORMATS = ["jpg", "png", "webp"]
VALID_CODECS = ["default", "h264", "h265"]
HISTORY_DISPLAY_LIMIT = 20

# ==== AUDIO QUALITY OPTIONS ====
AUDIO_QUALITY_OPTIONS = {
    "mp3": {
        "ext": "mp3",
        "bitrate": "~192 kbps",
        "codec": "MP3 (Lossy)"
    },
    "m4a": {
        "ext": "m4a",
        "bitrate": "~128 kbps",
        "codec": "AAC (M4A)"
    },
    "opus": {
        "ext": "opus",
        "bitrate": "~160-180 kbps",
        "codec": "Opus (Best Quality)"
    }
}

# ==== RUNTIME VARIABLES ====
class RuntimeConfig:
    """Runtime configuration that can be modified"""
    MUSIC_ROOT = DEFAULT_MUSIC_ROOT
    VIDEO_ROOT = DEFAULT_VIDEO_ROOT
    THUMBNAIL_ROOT = DEFAULT_THUMBNAIL_ROOT
    

    DOWNLOAD_HISTORY = []
    USER_SUBFOLDERS = {}
    
    SIMPLE_MODE = False
    SMART_COVER_MODE = True
    THUMBNAIL_FORMAT = "jpg"
    NO_COVER_MODE = False
    FORCE_CROP = False
    SKIP_EXISTING_FILES = True
    MAX_VIDEO_RESOLUTION = "720p"
    AUDIO_QUALITY = "m4a"
    VIDEO_CONTAINER = "mp4"
    VIDEO_CODEC = "default"

    HEADER_STYLE = "default"
    PROGRESS_STYLE = "minimal"
    

    MEDIA_SCANNER_ENABLED = False
    DOWNLOAD_DELAY = 2
    MAX_RETRIES = 3
    RETRY_DELAY = 2

    # Dependency verification
    VERIFIED_DEPENDENCIES = False
    SPOTIFY_AVAILABLE = False
    
    # Spotify Credentials
    SPOTIFY_CLIENT_ID = None
    SPOTIFY_CLIENT_SECRET = None

    # Language
    LANGUAGE = "en"

# ==== INITIALIZATION ====
try:
    if not IS_WINDOWS: 
        if not IS_TERMUX:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            TEMP_DIR.mkdir(parents=True, exist_ok=True)
        
        try:
            os.makedirs(DEFAULT_MUSIC_ROOT, exist_ok=True)
            os.makedirs(DEFAULT_VIDEO_ROOT, exist_ok=True)
        except OSError:
            pass

except PermissionError:
    print(f"\n[ERROR] Permission Denied.")
    print("Please check write permissions for configuration and download directories.")
    sys.exit(1)