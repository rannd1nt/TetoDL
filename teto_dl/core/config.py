"""
Configuration management system
"""
import os
import json
from ..constants import (
    CONFIG_PATH, RuntimeConfig, 
    DEFAULT_MUSIC_ROOT, DEFAULT_VIDEO_ROOT
)
from ..utils.colors import print_error, print_info
from ..utils.file_utils import create_nomedia_file


def load_config():
    """Load configuration from file"""
    if not os.path.exists(CONFIG_PATH):
        return
    
    try:
        with open(CONFIG_PATH, "r") as f:
            cfg = json.load(f)
        
        RuntimeConfig.MUSIC_ROOT = cfg.get("music_root", RuntimeConfig.MUSIC_ROOT)
        RuntimeConfig.VIDEO_ROOT = cfg.get("video_root", RuntimeConfig.VIDEO_ROOT)
        RuntimeConfig.USER_SUBFOLDERS = cfg.get("user_subfolders", RuntimeConfig.USER_SUBFOLDERS)
        RuntimeConfig.SIMPLE_MODE = cfg.get("simple_mode", RuntimeConfig.SIMPLE_MODE)
        RuntimeConfig.MAX_VIDEO_RESOLUTION = cfg.get("max_video_resolution", RuntimeConfig.MAX_VIDEO_RESOLUTION)
        RuntimeConfig.SKIP_EXISTING_FILES = cfg.get("skip_existing_files", RuntimeConfig.SKIP_EXISTING_FILES)
        RuntimeConfig.VERIFIED_DEPENDENCIES = cfg.get("verified_dependencies", RuntimeConfig.VERIFIED_DEPENDENCIES)
        RuntimeConfig.SPOTIFY_AVAILABLE = cfg.get("spotify_available", RuntimeConfig.SPOTIFY_AVAILABLE)
        RuntimeConfig.LANGUAGE = cfg.get("language", RuntimeConfig.LANGUAGE)
        
        # Load language after loading config
        from ..utils.i18n import set_language
        set_language(RuntimeConfig.LANGUAGE)
    except Exception:
        pass


def save_config():
    """Save current configuration to file"""
    cfg = {
        "music_root": RuntimeConfig.MUSIC_ROOT,
        "video_root": RuntimeConfig.VIDEO_ROOT,
        "user_subfolders": RuntimeConfig.USER_SUBFOLDERS,
        "simple_mode": RuntimeConfig.SIMPLE_MODE,
        "max_video_resolution": RuntimeConfig.MAX_VIDEO_RESOLUTION,
        "skip_existing_files": RuntimeConfig.SKIP_EXISTING_FILES,
        "verified_dependencies": RuntimeConfig.VERIFIED_DEPENDENCIES,
        "spotify_available": RuntimeConfig.SPOTIFY_AVAILABLE,
        "language": RuntimeConfig.LANGUAGE
    }
    
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        print_error("Gagal menyimpan config.")


def cleanup_ghost_subfolders():
    """
    Remove subfolders from config that no longer exist in filesystem
    """
    cleaned = False
    
    # Clean music subfolders
    valid_music_folders = []
    for folder in RuntimeConfig.USER_SUBFOLDERS.get("music", []):
        folder_path = os.path.join(RuntimeConfig.MUSIC_ROOT, folder)
        if os.path.exists(folder_path):
            valid_music_folders.append(folder)
        else:
            print_info(f"Menghapus subfolder ghost 'music/{folder}' dari config")
            cleaned = True
    
    # Clean video subfolders  
    valid_video_folders = []
    for folder in RuntimeConfig.USER_SUBFOLDERS.get("video", []):
        folder_path = os.path.join(RuntimeConfig.VIDEO_ROOT, folder)
        if os.path.exists(folder_path):
            valid_video_folders.append(folder)
        else:
            print_info(f"Menghapus subfolder ghost 'video/{folder}' dari config")
            cleaned = True
    
    # Update config if there are changes
    if cleaned:
        RuntimeConfig.USER_SUBFOLDERS["music"] = valid_music_folders
        RuntimeConfig.USER_SUBFOLDERS["video"] = valid_video_folders
        save_config()


def initialize_config():
    """Initialize configuration and create necessary directories"""
    load_config()
    
    # Create root directories
    os.makedirs(RuntimeConfig.MUSIC_ROOT, exist_ok=True)
    os.makedirs(RuntimeConfig.VIDEO_ROOT, exist_ok=True)
    
    # Ensure root folders don't have .nomedia
    create_nomedia_file(RuntimeConfig.MUSIC_ROOT)
    create_nomedia_file(RuntimeConfig.VIDEO_ROOT)
    
    # Cleanup ghost subfolders
    cleanup_ghost_subfolders()


def reset_to_defaults():
    """Reset configuration to default values"""
    RuntimeConfig.MUSIC_ROOT = DEFAULT_MUSIC_ROOT
    RuntimeConfig.VIDEO_ROOT = DEFAULT_VIDEO_ROOT
    
    os.makedirs(RuntimeConfig.MUSIC_ROOT, exist_ok=True)
    os.makedirs(RuntimeConfig.VIDEO_ROOT, exist_ok=True)
    
    create_nomedia_file(RuntimeConfig.MUSIC_ROOT)
    create_nomedia_file(RuntimeConfig.VIDEO_ROOT)
    
    save_config()


def toggle_simple_mode(enabled: bool):
    """Toggle simple mode"""
    RuntimeConfig.SIMPLE_MODE = enabled # pyright: ignore[reportAttributeAccessIssue]
    save_config()


def toggle_skip_existing(enabled: bool):
    """Toggle skip existing files"""
    RuntimeConfig.SKIP_EXISTING_FILES = enabled # pyright: ignore[reportAttributeAccessIssue]
    save_config()


def toggle_video_resolution():
    """Toggle between 720p and 1080p for max video resolution"""
    if RuntimeConfig.MAX_VIDEO_RESOLUTION == "720p":
        RuntimeConfig.MAX_VIDEO_RESOLUTION = "1080p" # pyright: ignore[reportAttributeAccessIssue]
    else:
        RuntimeConfig.MAX_VIDEO_RESOLUTION = "720p"
    
    save_config()
    return RuntimeConfig.MAX_VIDEO_RESOLUTION


def get_video_format_string():
    """Get format string based on max resolution setting"""
    if RuntimeConfig.MAX_VIDEO_RESOLUTION == "1080p":
        return 'bestvideo[height<=1080]+bestaudio/best'
    else:  # 720p default
        return 'bestvideo[height<=720]+bestaudio/best'


def get_fallback_format_string():
    """Get fallback format string based on max resolution setting"""
    if RuntimeConfig.MAX_VIDEO_RESOLUTION == "1080p":
        return 'best[height<=1080][ext=mp4]'
    else:  # 720p default
        return 'best[height<=720][ext=mp4]'


def clear_cache():
    """Clear cache file"""
    from ..constants import CACHE_PATH
    try:
        if os.path.exists(CACHE_PATH):
            os.remove(CACHE_PATH)
            return True
    except Exception:
        pass
    return False


def clear_history():
    """Clear history file"""
    from ..constants import HISTORY_PATH
    try:
        if os.path.exists(HISTORY_PATH):
            os.remove(HISTORY_PATH)
            RuntimeConfig.DOWNLOAD_HISTORY = []
            return True
    except Exception:
        pass
    return False


def toggle_language():
    """Toggle between Indonesian and English"""
    from ..utils.i18n import set_language, get_current_language
    
    current = get_current_language()
    new_lang = "en" if current == "id" else "id"
    
    if set_language(new_lang):
        RuntimeConfig.LANGUAGE = new_lang # pyright: ignore[reportAttributeAccessIssue]
        save_config()
        return new_lang
    return current


def get_language_name(lang_code: str) -> str:
    """Get language display name"""
    names = {
        "id": "Indonesia",
        "en": "English"
    }
    return names.get(lang_code, lang_code)