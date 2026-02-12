"""
General-purpose utility functions for file handling, networking, I/O operations, 
and text processing.
"""
from .processing import (
    extract_all_urls_from_content,
    extract_video_id,
)

from .styles import (
    Colors,
    color,
    colored_info,
    colored_switch,
    print_process,
    print_info,
    print_success,
    print_debug,
    print_error,
    print_neutral
)

from .spinner import Spinner

from .network import (
    check_internet,
    is_valid_youtube_url,
    is_youtube_music_url,
    classify_youtube_url,
    is_valid_spotify_url,
    classify_spotify_url
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

from .metadata_fetcher import (
    MetadataFetcher
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
    'print_process',
    'print_info',
    'print_success',
    'print_debug',
    'print_error',
    'print_neutral',
    'show_ascii',
    'visit_instagram',
    'visit_github',
    'wait_and_clear_prompt',
    'Spinner',
    'check_internet',
    'is_valid_youtube_url',
    'is_youtube_music_url',
    'classify_youtube_url',
    'is_valid_spotify_url',
    'classify_spotify_url',
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
    'get_current_language'
]