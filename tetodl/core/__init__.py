# Copyright 2026 rannd1nt
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Core application logic managing configuration, session history, dependency, registry,
and global state.
"""

from .domain.cache import (
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
from .domain.config import (
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
from .domain.history import add_to_history, get_history_stats, load_history, save_history
from .domain.registry import RegistryManager, registry

__all__ = [
    'Cache',
    'CacheStats',
    'RegistryManager',
    'add_to_history',
    'cache_metadata',
    'cleanup_ghost_subfolders',
    'evict_cache',
    'get_cache',
    'get_cache_size',
    'get_cached_metadata',
    'get_fallback_format_string',
    'get_history_stats',
    'get_url_hash',
    'get_video_format_string',
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
    'toggle_simple_mode',
    'toggle_skip_existing',
    'update_language',
    'verify_core_dependencies',
]
