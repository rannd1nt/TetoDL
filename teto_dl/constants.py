"""
Constants and Path Configuration
"""
import os

# ==== BASE PATHS ====
BASE_PATH = "/storage/emulated/0/TetoDL"
CONFIG_PATH = os.path.join(BASE_PATH, "config.json")
CACHE_PATH = os.path.join(BASE_PATH, "cache.json")
HISTORY_PATH = os.path.join(BASE_PATH, "history.json")

# ==== DEFAULT ROOTS ====
DEFAULT_MUSIC_ROOT = os.path.join(BASE_PATH, "music")
DEFAULT_VIDEO_ROOT = os.path.join(BASE_PATH, "videos")

# ==== EXTERNAL COMMANDS ====
FFMPEG_CMD = "/data/data/com.termux/files/usr/bin/ffmpeg"
SPOTDL_CMD = "/data/data/com.termux/files/usr/bin/spotdl"

# ==== DOWNLOAD SETTINGS ====
DOWNLOAD_DELAY = 2  # Delay antara download (seconds)

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

# ==== RUNTIME VARIABLES (will be loaded from config) ====
class RuntimeConfig:
    """Runtime configuration that can be modified"""
    MUSIC_ROOT = DEFAULT_MUSIC_ROOT
    VIDEO_ROOT = DEFAULT_VIDEO_ROOT
    USER_SUBFOLDERS = {
        "music": [],
        "video": []
    }
    SIMPLE_MODE = False
    SKIP_EXISTING_FILES = True
    MAX_VIDEO_RESOLUTION = "720p"  # Default: 720p
    DOWNLOAD_HISTORY = []
    AUDIO_QUALITY = "m4a"  # Default: m4a
    
    # Dependency verification
    VERIFIED_DEPENDENCIES = False
    SPOTIFY_AVAILABLE = False
    
    # Language setting
    LANGUAGE = "id"  # Default: Indonesian

# Create base directory if not exists
os.makedirs(BASE_PATH, exist_ok=True)