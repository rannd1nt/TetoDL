"""
Platform-specific modules responsible for extracting media metadata and handling 
download streams (e.g., YouTube, Spotify).
"""
from .youtube import (
    download_audio_youtube, 
    download_video_youtube, 
    get_content_type_display,
    download_thumbnail_task
)

from .spotify import download_spotify

__all__ = [
    'download_thumbnail_task',
    'download_audio_youtube',
    'download_video_youtube',
    'download_spotify',
    'get_content_type_display'
]