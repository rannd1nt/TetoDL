"""
Core functionality package
"""

from .config import (
    load_config,
    save_config,
    cleanup_ghost_subfolders,
    initialize_config,
    reset_to_defaults,
    toggle_simple_mode,
    toggle_skip_existing,
    toggle_video_resolution,
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
    get_history_stats,
    format_duration,
    truncate_title,
    get_platform_alias,
    display_history
)

from .dependency import (
    verify_dependencies,
    reset_verification
)

__all__ = [
    'load_config',
    'save_config',
    'cleanup_ghost_subfolders',
    'initialize_config',
    'reset_to_defaults',
    'toggle_simple_mode',
    'toggle_skip_existing',
    'toggle_video_resolution',
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
    'format_duration',
    'truncate_title',
    'get_platform_alias',
    'display_history',
    'verify_dependencies',
    'reset_verification'
]