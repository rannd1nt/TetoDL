"""
General-purpose utility functions for file handling, networking, I/O operations, 
and text processing.
"""
from .display import show_ascii, visit_github, visit_instagram, wait_and_clear_prompt
from .files import clean_temp_files, remove_nomedia_file
from .formatters import (
    Colors,
    clear,
    color,
    colored_info,
    colored_switch,
)
from .hooks import QuietLogger, get_progress_hook
from .i18n import (
    detect_system_language,
    get_available_languages,
    get_current_language,
    get_language_display_name,
    get_text,
    set_language,
)
from .media_scanner import (
    scan_media_files,
)
from .network import (
    check_internet,
    classify_youtube_url,
    is_valid_youtube_url,
    is_youtube_music_url,
)
from .processing import (
    extract_all_urls_from_content,
    extract_video_id,
)

__all__ = [
    'Colors',
    'QuietLogger',
    'check_internet',
    'classify_youtube_url',
    'clean_temp_files',
    'clear',
    'color',
    'colored_info',
    'colored_switch',
    'detect_system_language',
    'extract_all_urls_from_content',
    'extract_video_id',
    'fetch_cover',
    'get_available_languages',
    'get_current_language',
    'get_language_display_name',
    'get_progress_hook',
    'get_text',
    'is_valid_youtube_url',
    'is_youtube_music_url',
    'remove_nomedia_file',
    'scan_media_files',
    'set_language',
    'show_ascii',
    'visit_github',
    'visit_instagram',
    'wait_and_clear_prompt',
]