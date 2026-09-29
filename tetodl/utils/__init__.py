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
General-purpose utility functions for file handling, networking, I/O operations, 
and text processing.
"""
from typing import Any

from .formatters import (
    Colors,
    clear,
    color,
    colored_info,
    colored_switch,
)
from .i18n import (
    detect_system_language,
    get_available_languages,
    get_current_language,
    get_language_display_name,
    get_text,
    set_language,
)
from .media_scanner import scan_media_files

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'clean_temp_files': ('.files', 'clean_temp_files'),
    'remove_nomedia_file': ('.files', 'remove_nomedia_file'),
    'show_ascii': ('.display', 'show_ascii'),
    'visit_github': ('.display', 'visit_github'),
    'visit_instagram': ('.display', 'visit_instagram'),
    'wait_and_clear_prompt': ('.display', 'wait_and_clear_prompt'),
    'QuietLogger': ('.hooks', 'QuietLogger'),
    'get_progress_hook': ('.hooks', 'get_progress_hook'),
    'check_internet': ('.network', 'check_internet'),
    'classify_youtube_url': ('.network', 'classify_youtube_url'),
    'is_valid_youtube_url': ('.network', 'is_valid_youtube_url'),
    'is_youtube_music_url': ('.network', 'is_youtube_music_url'),
    'extract_all_urls_from_content': ('.processing', 'extract_all_urls_from_content'),
    'extract_video_id': ('.processing', 'extract_video_id'),
}

__all__ = [
    'Colors',
    'QuietLogger', # type: ignore
    'check_internet', # type: ignore
    'classify_youtube_url', # type: ignore
    'clean_temp_files', # type: ignore
    'clear',
    'color',
    'colored_info',
    'colored_switch',
    'detect_system_language',
    'extract_all_urls_from_content', # type: ignore
    'extract_video_id', # type: ignore
    'get_available_languages',
    'get_current_language',
    'get_language_display_name',
    'get_progress_hook', # type: ignore
    'get_text',
    'is_valid_youtube_url', # type: ignore
    'is_youtube_music_url', # type: ignore
    'remove_nomedia_file', # type: ignore
    'scan_media_files',
    'set_language',
    'show_ascii', # type: ignore
    'visit_github', # type: ignore
    'visit_instagram', # type: ignore
    'wait_and_clear_prompt', # type: ignore
]


def __getattr__(name: str) -> Any:
    if name in _LAZY_IMPORTS:
        import importlib
        mod_name, attr_name = _LAZY_IMPORTS[name]
        mod = importlib.import_module(mod_name, __package__)
        val = getattr(mod, attr_name)
        globals()[name] = val
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")