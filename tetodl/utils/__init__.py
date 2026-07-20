"""
General-purpose utility functions for file handling, networking, I/O operations, 
and text processing.
"""
from .processing import (
    extract_all_urls_from_content,
    extract_video_id,
)

from .formatters import (
    Colors,
    color,
    colored_info,
    colored_switch,
    clear,
)

from .network import (
    check_internet,
    is_valid_youtube_url,
    is_youtube_music_url,
    classify_youtube_url,
)

from .media_scanner import (
    scan_media_files,
)

from .files import (
    remove_nomedia_file,
    clean_temp_files
)

from .display import (
    show_ascii,
    visit_instagram,
    visit_github,
    wait_and_clear_prompt
)

from .i18n import (
    get_text,
    detect_system_language,
    set_language,
    get_available_languages,
    get_language_display_name,
    get_current_language,
)

from .hooks import (
    QuietLogger,
    get_progress_hook
)


__all__ = [
    'Colors',
    'color',
    'colored_info',
    'colored_switch',
    'clear',
    'show_ascii',
    'visit_instagram',
    'visit_github',
    'wait_and_clear_prompt',
    'check_internet',
    'is_valid_youtube_url',
    'is_youtube_music_url',
    'classify_youtube_url',
    'remove_nomedia_file',
    'clean_temp_files',
    'fetch_cover',
    'QuietLogger',
    'get_progress_hook',
    'get_text',
    'detect_system_language',
    'set_language',
    'get_available_languages',
    'get_language_display_name',
    'get_current_language',
    'scan_media_files',
]