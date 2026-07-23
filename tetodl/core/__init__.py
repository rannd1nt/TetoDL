"""
Core application logic managing configuration, session history, dependency, registry, 
and global state.
"""

from .cache import (
    Cache,
    CacheStats,
    cache_metadata,
    evict_cache,
    get_cache,
    get_cache_size,
    get_cached_metadata,
    get_url_hash,
    reset_cache,
)
from .config import (
    cleanup_ghost_subfolders,
    get_fallback_format_string,
    get_video_format_string,
    initialize_config,
    load_config,
    reset_to_defaults,
    save_config,
    set_progress_style,
    set_video_resolution,
    toggle_simple_mode,
    toggle_skip_existing,
    update_language,
)
from .dependency import reset_verification, verify_core_dependencies
from .history import add_to_history, get_history_stats, load_history, save_history
from .image_cache import (
    IMG_TTL,
    clear_img_cache,
    evict_img_cache,
    fetch_image,
    img_cache_size,
)
from .registry import RegistryManager, registry

__all__ = [
    'IMG_TTL',
    'Cache',
    'CacheStats',
    'RegistryManager',
    'add_to_history',
    'cache_metadata',
    'cleanup_ghost_subfolders',
    'clear_img_cache',
    'evict_cache',
    'evict_img_cache',
    'fetch_image',
    'get_cache',
    'get_cache_size',
    'get_cached_metadata',
    'get_fallback_format_string',
    'get_history_stats',
    'get_url_hash',
    'get_video_format_string',
    'img_cache_size',
    'initialize_config',
    'load_config',
    'load_history',
    'registry',
    'reset_cache',
    'reset_to_defaults',
    'reset_verification',
    'save_config',
    'save_history',
    'set_progress_style',
    'set_video_resolution',
    'toggle_media_scanner',
    'toggle_simple_mode',
    'toggle_skip_existing',
    'update_language',
    'verify_core_dependencies',
]