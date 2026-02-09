"""
Handlers for media post-processing, including format conversion, metadata tagging, 
and thumbnail management.
"""

from .thumbnail import (
    crop_thumbnail_to_square,
    convert_thumbnail_format,
    download_and_process_thumbnail,
    embed_thumbnail_to_audio
)

from .scanner import scan_media_files

__all__ = [
    'crop_thumbnail_to_square',
    'convert_thumbnail_format',
    'download_and_process_thumbnail',
    'embed_thumbnail_to_audio',
    'scan_media_files'
]