"""
Media processing package
"""

from .thumbnail import (
    crop_thumbnail_to_square,
    download_and_process_thumbnail,
    embed_thumbnail_to_mp3
)

from .scanner import scan_media_files

__all__ = [
    'crop_thumbnail_to_square',
    'download_and_process_thumbnail',
    'embed_thumbnail_to_mp3',
    'scan_media_files'
]