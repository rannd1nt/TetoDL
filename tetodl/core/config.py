"""
Configuration management system
"""
import os
import json
from ..constants import (
    CONFIG_PATH, VALID_CONTAINERS, VALID_RESOLUTIONS, REGISTRY_PATH,
    DEFAULT_MUSIC_ROOT, DEFAULT_VIDEO_ROOT, RuntimeConfig, VALID_CODECS
)
from ..utils.styles import print_error
from ..utils.i18n import set_language, detect_system_language


def load_config():
    """Load app configuration"""
    if not os.path.exists(CONFIG_PATH):
        sys_lang = detect_system_language()
        RuntimeConfig.LANGUAGE = sys_lang
        set_language(sys_lang)
        return

    try:
        with open(CONFIG_PATH, "r") as f:
            cfg = json.load(f)

        RuntimeConfig.MUSIC_ROOT = cfg.get("music_root", str(RuntimeConfig.MUSIC_ROOT))
        RuntimeConfig.VIDEO_ROOT = cfg.get("video_root", str(RuntimeConfig.VIDEO_ROOT))
        RuntimeConfig.USER_SUBFOLDERS = cfg.get("user_subfolders", RuntimeConfig.USER_SUBFOLDERS)
        RuntimeConfig.SIMPLE_MODE = cfg.get("simple_mode", RuntimeConfig.SIMPLE_MODE)
        RuntimeConfig.MAX_VIDEO_RESOLUTION = cfg.get("max_video_resolution", RuntimeConfig.MAX_VIDEO_RESOLUTION)
        RuntimeConfig.VIDEO_CONTAINER = cfg.get("video_container", RuntimeConfig.VIDEO_CONTAINER)
        RuntimeConfig.VIDEO_CODEC = cfg.get("video_codec", "default")
        RuntimeConfig.AUDIO_QUALITY = cfg.get("audio_quality", RuntimeConfig.AUDIO_QUALITY)
        RuntimeConfig.PROGRESS_STYLE = cfg.get("progress_style", "minimal")
        RuntimeConfig.HEADER_STYLE = cfg.get("header_style", "default")
        RuntimeConfig.SKIP_EXISTING_FILES = cfg.get("skip_existing_files", RuntimeConfig.SKIP_EXISTING_FILES)
        RuntimeConfig.VERIFIED_DEPENDENCIES = cfg.get("verified_dependencies", RuntimeConfig.VERIFIED_DEPENDENCIES)
        RuntimeConfig.SMART_COVER_MODE = cfg.get("smart_cover_mode", RuntimeConfig.SMART_COVER_MODE)
        RuntimeConfig.DOWNLOAD_DELAY = cfg.get("download_delay", 2)
        RuntimeConfig.MAX_RETRIES = cfg.get("max_retries", 3)
        RuntimeConfig.MEDIA_SCANNER_ENABLED = cfg.get("media_scanner_enabled", False)
        RuntimeConfig.SPOTIFY_AVAILABLE = cfg.get("spotify_available", RuntimeConfig.SPOTIFY_AVAILABLE)
        
        saved_lang = cfg.get("language")
        if saved_lang:
            RuntimeConfig.LANGUAGE = saved_lang
        else:
            RuntimeConfig.LANGUAGE = detect_system_language()

        set_language(RuntimeConfig.LANGUAGE)
    except Exception:
        sys_lang = detect_system_language()
        RuntimeConfig.LANGUAGE = sys_lang
        set_language(sys_lang)


def save_config():
    """Save current configuration to file"""
    cfg = {
        "music_root": str(RuntimeConfig.MUSIC_ROOT),
        "video_root": str(RuntimeConfig.VIDEO_ROOT),
        "user_subfolders": RuntimeConfig.USER_SUBFOLDERS,
        "simple_mode": RuntimeConfig.SIMPLE_MODE,
        "max_video_resolution": RuntimeConfig.MAX_VIDEO_RESOLUTION,
        "audio_quality": RuntimeConfig.AUDIO_QUALITY,
        "video_container": RuntimeConfig.VIDEO_CONTAINER,
        "video_codec": RuntimeConfig.VIDEO_CODEC,
        "progress_style": RuntimeConfig.PROGRESS_STYLE,
        "header_style": RuntimeConfig.HEADER_STYLE,
        "skip_existing_files": RuntimeConfig.SKIP_EXISTING_FILES,
        "download_delay": RuntimeConfig.DOWNLOAD_DELAY,
        "max_retries": RuntimeConfig.MAX_RETRIES,
        "media_scanner_enabled": RuntimeConfig.MEDIA_SCANNER_ENABLED,
        "smart_cover_mode": RuntimeConfig.SMART_COVER_MODE,
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
    
    current_roots = list(RuntimeConfig.USER_SUBFOLDERS.keys())

    for root_path in current_roots:
        # Clear Config Legacy
        if root_path in ["music", "video"]:
            if not os.path.exists(root_path):
                del RuntimeConfig.USER_SUBFOLDERS[root_path]
                cleaned = True
            continue

        if not os.path.exists(root_path):
            continue

        current_subs = RuntimeConfig.USER_SUBFOLDERS[root_path]
        valid_subs = []
        is_modified = False

        for sub in current_subs:
            full_path = os.path.join(root_path, sub)
            if os.path.exists(full_path):
                valid_subs.append(sub)
            else:
                is_modified = True
                cleaned = True

        if is_modified:
            RuntimeConfig.USER_SUBFOLDERS[root_path] = valid_subs
            
            if not valid_subs:
                del RuntimeConfig.USER_SUBFOLDERS[root_path]
                cleaned = True

    if cleaned:
        save_config()


def initialize_config():
    """Initialize configuration and create necessary directories"""
    from ..utils.files import remove_nomedia_file
    load_config()

    # Create root directories
    os.makedirs(RuntimeConfig.MUSIC_ROOT, exist_ok=True)
    os.makedirs(RuntimeConfig.VIDEO_ROOT, exist_ok=True)

    # Ensure root folders don't have .nomedia
    remove_nomedia_file(RuntimeConfig.MUSIC_ROOT)
    remove_nomedia_file(RuntimeConfig.VIDEO_ROOT)

    # Cleanup ghost subfolders
    cleanup_ghost_subfolders()


def reset_to_defaults():
    """Reset configuration to default values"""
    from ..utils.files import remove_nomedia_file

    RuntimeConfig.MUSIC_ROOT = DEFAULT_MUSIC_ROOT
    RuntimeConfig.VIDEO_ROOT = DEFAULT_VIDEO_ROOT

    os.makedirs(RuntimeConfig.MUSIC_ROOT, exist_ok=True)
    os.makedirs(RuntimeConfig.VIDEO_ROOT, exist_ok=True)

    remove_nomedia_file(RuntimeConfig.MUSIC_ROOT)
    remove_nomedia_file(RuntimeConfig.VIDEO_ROOT)

    save_config()


def toggle_simple_mode(enabled: bool):
    """Toggle simple mode"""
    RuntimeConfig.SIMPLE_MODE = enabled # pyright: ignore[reportAttributeAccessIssue]
    save_config()

def toggle_smart_cover(enabled: bool):
    """Toggle Smart Cover Mode"""
    RuntimeConfig.SMART_COVER_MODE = enabled
    save_config()

def toggle_skip_existing(enabled: bool):
    """Toggle skip existing files"""
    RuntimeConfig.SKIP_EXISTING_FILES = enabled # pyright: ignore[reportAttributeAccessIssue]
    save_config()


def toggle_video_container(container):
    """Set video container (mp4 or mkv)"""
    if container in VALID_CONTAINERS:
        RuntimeConfig.VIDEO_CONTAINER = container
        save_config()
        return True
    return False

def set_video_resolution(resolution):
    """Set specific video resolution"""
    if resolution in VALID_RESOLUTIONS:
        RuntimeConfig.MAX_VIDEO_RESOLUTION = resolution
        save_config()
        return True
    return False

def set_video_codec(codec):
    """Set video codec preference"""
    if codec in VALID_CODECS:
        RuntimeConfig.VIDEO_CODEC = codec
        save_config()
        return True
    return False

def toggle_audio_quality(new_quality):
    """Toggle audio quality setting"""
    from ..constants import RuntimeConfig, AUDIO_QUALITY_OPTIONS

    if new_quality in AUDIO_QUALITY_OPTIONS:
        RuntimeConfig.AUDIO_QUALITY = new_quality
        save_config()
        return new_quality
    return RuntimeConfig.AUDIO_QUALITY

def set_progress_style(style_name):
    """Set progress bar style (minimal, classic, modern)"""
    valid_styles = ["minimal", "classic", "modern"]
    if style_name in valid_styles:
        RuntimeConfig.PROGRESS_STYLE = style_name
        save_config()
        return style_name
    return RuntimeConfig.PROGRESS_STYLE

def set_header_style(style_name):
    """Set header style (filename without extension or 'classic')"""
    RuntimeConfig.HEADER_STYLE = style_name
    save_config()
    return True

def set_network_config(delay=None, retries=None):
    if delay is not None:
        RuntimeConfig.DOWNLOAD_DELAY = float(delay)
    if retries is not None:
        RuntimeConfig.MAX_RETRIES = int(retries)
    save_config()
    return True

def set_media_scanner(enable: bool):
    RuntimeConfig.MEDIA_SCANNER_ENABLED = enable
    save_config()
    return True
    
def get_audio_quality_info():
    """Get current audio quality information"""
    from ..constants import RuntimeConfig, AUDIO_QUALITY_OPTIONS
    return AUDIO_QUALITY_OPTIONS.get(RuntimeConfig.AUDIO_QUALITY, AUDIO_QUALITY_OPTIONS["m4a"])

def get_video_format_string():
    """Get format string based on max resolution setting dynamicly"""
    max_height = RuntimeConfig.MAX_VIDEO_RESOLUTION.replace('p', '')
    
    return f'bestvideo[height<={max_height}]+bestaudio/best[height<={max_height}]'

def get_fallback_format_string():
    """Get fallback format string based on max resolution setting"""
    max_height = RuntimeConfig.MAX_VIDEO_RESOLUTION.replace('p', '')
    return f'best[height<={max_height}][ext=mp4]'


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

def reset_config():
    """Delete configuration file (Factory Reset)"""
    try:
        if os.path.exists(CONFIG_PATH):
            os.remove(CONFIG_PATH)
            return True
    except Exception:
        pass
    return False

def wipe_registry():
    """Delete registry database (Nuclear Option)"""
    try:
        if os.path.exists(REGISTRY_PATH):
            os.remove(REGISTRY_PATH)
            return True
    except Exception:
        pass
    return False

def perform_full_wipe():
    """Delete EVERYTHING"""
    c = clear_cache()
    h = clear_history()
    cfg = reset_config()
    reg = wipe_registry()
    return c and h and cfg and reg

def update_language(lang_code: str):
    """Set specific language and save config"""
    
    if set_language(lang_code):
        RuntimeConfig.LANGUAGE = lang_code
        save_config()
        return True
    return False


def get_language_name(lang_code: str) -> str:
    """Get language display name"""
    names = {
        "id": "Indonesia",
        "en": "English"
    }
    return names.get(lang_code, lang_code)