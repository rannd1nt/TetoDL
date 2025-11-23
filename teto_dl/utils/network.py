"""
Network utilities: internet check, URL validation
"""
import re
import requests


def check_internet() -> bool:
    """Check if internet connection is available"""
    try:
        r = requests.get("https://www.google.com", timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def is_valid_youtube_url(url: str) -> bool:
    """Check if URL is a valid YouTube/YouTube Music URL"""
    youtube_patterns = [
        r'https?://(www\.)?(youtube\.com|youtu\.be)/.+',
        r'https?://(www\.)?music\.youtube\.com/.+'
    ]
    return any(re.match(pattern, url) for pattern in youtube_patterns)


def is_youtube_music_url(url: str) -> bool:
    """Check if URL is from YouTube Music"""
    return 'music.youtube.com' in url


def classify_youtube_url(url: str) -> dict:
    """
    Classify YouTube/YouTube Music URL in detail
    Returns: {'type': 'video'|'playlist'|'album', 'platform': 'youtube'|'youtube_music'}
    """
    result = {'type': 'video', 'platform': 'youtube'}
    
    # Check platform
    if is_youtube_music_url(url):
        result['platform'] = 'youtube_music'
    
    # Check content type
    if '&list=' in url or '?list=' in url or '/playlist' in url:
        result['type'] = 'playlist'
    elif '/album/' in url and 'music.youtube.com' in url:
        result['type'] = 'album'
    elif '/watch?v=' in url or 'youtu.be/' in url:
        result['type'] = 'video'
    
    return result


def is_valid_spotify_url(url: str) -> bool:
    """Check if URL is a valid Spotify URL"""
    return re.match(r'https?://open\.spotify\.com/.+', url) is not None


def classify_spotify_url(url: str) -> str:
    """
    Classify Spotify URL into 'playlist', 'album', 'track', or 'unknown'
    """
    if 'open.spotify.com/playlist/' in url:
        return "Playlist"
    elif 'open.spotify.com/album/' in url:
        return "Album"
    elif 'open.spotify.com/track/' in url:
        return "Single Track"
    else:
        return "Unknown"