"""
Core processing utilities for extraction, validation, and formatting.
Absorbs logic from old 'yt_helpers' and 'extract_video_id'.
"""
import re

from ..constants import RuntimeConfig
from ..utils.network import is_youtube_music_url

try:
    import yt_dlp as yt
except ImportError:
    yt = None

# --- ID EXTRACTION  ---
def extract_video_id(url):
    """Ekstrak YouTube ID tanpa internet (0.00s latency)"""
    try:
        # Support: ?v=ID, &v=ID, /v/ID, /embed/ID, /shorts/ID, youtu.be/ID
        pattern = r'(?:[\?&]v=|\/v\/|\/embed\/|\/shorts\/|youtu\.be\/|\/watch\?v=|^)([0-9A-Za-z_-]{11})'
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    except Exception:
        pass
    return None

# --- ERROR HANDLING ---


# --- FORMAT STRING BUILDERS ---
def get_audio_extension():
    return RuntimeConfig.AUDIO_QUALITY

def get_audio_format_string(audio_format):
    if audio_format == "m4a":
        return 'bestaudio[ext=m4a]/bestaudio'
    return 'bestaudio/best'

def build_audio_postprocessors(audio_format, is_youtube_music=False):
    """Build postprocessors list based on audio format"""
    postprocessors = []
    if audio_format == "mp3":
        postprocessors.append({
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        })
    elif audio_format == "opus":
        postprocessors.append({
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'opus',
            'preferredquality': '160',
        })
    
    if is_youtube_music and (audio_format == "mp3" or audio_format == "m4a"):
        postprocessors.append({'key': 'FFmpegMetadata', 'add_metadata': True})
        
    return postprocessors

# --- URL EXTRACTION ---
def extract_all_urls_from_content(url):
    """Extract URLs from Playlist/Album/Single"""
    is_yt_music = is_youtube_music_url(url)
    ydl_opts = {'extract_flat': True, 'quiet': True, 'no_warnings': True}

    try:
        with yt.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            if 'entries' in info:
                urls = []
                for entry in info['entries']:
                    if entry.get('url'):
                        urls.append(entry['url'])
                    elif entry.get('id'):
                        vid = entry['id']
                        base = "https://music.youtube.com/watch?v=" if is_yt_music else "https://www.youtube.com/watch?v="
                        urls.append(f"{base}{vid}")
                
                title = info.get('title', 'Unknown Playlist')
                return urls, title, len(urls)
            else:
                target_url = info.get('webpage_url') or info.get('url') or url
                title = info.get('title', 'Single Track')
                return [target_url], title, 1
    except Exception:
        return [url], 'Unknown', 1


def get_platform_badge(platform: str, download_type: str = None) -> str:
    """
    Generate badge Content Type yang lebih informatif.
    Format: YT-VID, YT-AUD, YT-MSC, SPOTIFY
    """
    if not platform:
        return "[dim]???[/dim]"

    p_lower = platform.lower()
    
    # 1. SPOTIFY
    if "spotify" in p_lower:
        return "[green]SPOTIFY[/green]"
    
    # 2. YOUTUBE
    if "youtube" in p_lower:
        # YouTube Music
        if "music" in p_lower:
            return "[red]YT-MUSIC[/red]"
        
        # YouTube Audio Only
        if "audio" in p_lower:
            return "[red]YT-AUD[/red]"
            
        # YouTube Video
        if "video" in p_lower:
            return "[red]YT-VID[/red]"
            
        # Fallback
        return "[red]YOUTUBE[/red]"

    # 3. Fallback Unknown Platform
    label = platform[:8].upper()
    return f"[blue]{label}[/blue]"