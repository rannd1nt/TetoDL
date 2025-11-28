"""
Utility functions package
"""

from .colors import (
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

from .file_utils import (
    create_nomedia_file,
    check_file_exists,
    calculate_similarity,
    clean_temp_files
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
    'Spinner',
    'check_internet',
    'is_valid_youtube_url',
    'is_youtube_music_url',
    'classify_youtube_url',
    'is_valid_spotify_url',
    'classify_spotify_url',
    'create_nomedia_file',
    'check_file_exists',
    'calculate_similarity',
    'clean_temp_files'
]