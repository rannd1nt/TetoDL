"""
Core application logic managing configuration, session history, dependency, registry, 
and global state.
"""

from .config import (
    load_config,
    save_config,
    cleanup_ghost_subfolders,
    initialize_config,
    reset_to_defaults,
    update_language,
    toggle_simple_mode,
    toggle_skip_existing,
    set_progress_style,
    set_video_resolution,
    get_video_format_string,
    get_fallback_format_string
)

from .cache import (
    load_cache,
    save_cache,
    get_url_hash,
    get_cached_metadata,
    cache_metadata
)

from .history import (
    load_history,
    save_history,
    add_to_history,
    get_history_stats
)

from .dependency import (
    verify_spotify_dependency,
    verify_core_dependencies,
    reset_verification
)

from .registry import (
    RegistryManager,
    registry
)



__all__ = [
    'load_config',
    'save_config',
    'cleanup_ghost_subfolders',
    'initialize_config',
    'reset_to_defaults',
    'toggle_simple_mode',
    'toggle_skip_existing',
    'toggle_media_scanner',
    'set_progress_style',
    'set_video_resolution',
    'update_language',
    'get_video_format_string',
    'get_fallback_format_string',
    'load_cache',
    'save_cache',
    'get_url_hash',
    'get_cached_metadata',
    'cache_metadata',
    'load_history',
    'save_history',
    'add_to_history',
    'get_history_stats',
    'verify_core_dependencies',
    'verify_spotify_dependency',
    'reset_verification',
    'RegistryManager',
    'registry'
]