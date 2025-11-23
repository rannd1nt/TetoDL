"""
Download history tracking system
"""
import os
import json
from datetime import datetime
from ..constants import HISTORY_PATH, RuntimeConfig
from ..utils.colors import print_error, print_info, clear


def load_history():
    """Load download history from file"""
    if not os.path.exists(HISTORY_PATH):
        RuntimeConfig.DOWNLOAD_HISTORY = []
        return
    
    try:
        with open(HISTORY_PATH, "r") as f:
            RuntimeConfig.DOWNLOAD_HISTORY = json.load(f)
    except Exception:
        RuntimeConfig.DOWNLOAD_HISTORY = []


def save_history():
    """Save download history to file"""
    try:
        with open(HISTORY_PATH, "w") as f:
            json.dump(RuntimeConfig.DOWNLOAD_HISTORY, f, indent=2)
    except Exception:
        print_error("Gagal menyimpan history.")

def reset_history():
    """Clear all download history"""
    try:
        if os.path.exists(HISTORY_PATH):
            os.remove(HISTORY_PATH)
        RuntimeConfig.DOWNLOAD_HISTORY = []
        return True
    except Exception as e:
        print_error(f"Gagal menghapus history: {e}")
        return False
    
def add_to_history(success, title, content_type, platform, download_type, duration):
    """Add entry to download history"""
    
    if platform == 'Spotify':
        if download_type == 'Single Track':
            title = 'SptfyTrack'
        elif download_type == 'Playlist':
            title = 'SptfyPlaylist'
        elif download_type == 'Album':
            title = 'SptfyAlbum'
        else:
            title = 'Spotify'

    entry = {
        'success': success,
        'title': title,
        'content_type': content_type,
        'platform': platform,
        'download_type': download_type,
        'duration': duration,
        'timestamp': datetime.now().strftime("%d-%m-%y %H:%M:%S"),
        'date_display': datetime.now().strftime("%d %b %y")
    }
    
    RuntimeConfig.DOWNLOAD_HISTORY.append(entry)
    save_history()


def get_history_stats():
    """Get cumulative statistics from history"""
    stats = {
        'yt_video': 0,
        'yt_audio': 0, 
        'yt_music': 0,
        'spotify': 0,
        'total_duration': 0
    }
    
    for entry in RuntimeConfig.DOWNLOAD_HISTORY:
        if entry['success']:
            platform = entry['platform']
            if platform == 'YouTube Video':
                stats['yt_video'] += 1
            elif platform == 'YouTube Audio':
                stats['yt_audio'] += 1
            elif platform == 'YouTube Music':
                stats['yt_music'] += 1
            elif platform == 'Spotify':
                stats['spotify'] += 1
            
            stats['total_duration'] += entry.get('duration', 0)
    
    return stats


def format_duration(seconds):
    """Format duration in seconds to hours, minutes, seconds"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours} Jam, {minutes} menit, {secs} detik"
    elif minutes > 0:
        return f"{minutes} menit, {secs} detik"
    else:
        return f"{secs} detik"


def truncate_title(title, max_words=3, max_chars=15):
    """Truncate title to maximum X words or Y characters, whichever comes first"""
    title = title.strip()
    
    if len(title) <= max_chars:
        return title
    
    words = title.split()
    
    if len(words) <= max_words:
        if len(title) <= max_chars:
            return title
        else:
            return title[:max_chars-3] + "..."
    else:
        truncated_by_words = ' '.join(words[:max_words])
        
        if truncated_by_words[-1] in [',', '.', '-', ':', ';', '!', '?']:
            truncated_by_words = truncated_by_words[:-1]
        
        if len(truncated_by_words) <= max_chars:
            return truncated_by_words + "..."
        else:
            return truncated_by_words[:max_chars-3] + "..."


def get_platform_alias(platform, download_type):
    """Get shorter platform alias"""
    if platform == 'YouTube Video':
        if download_type == 'Single Video':
            return 'YTVidTrack'
        elif download_type == 'Playlist Video':
            return 'YTVidPlaylist'
        else:
            return 'YTVid'
    
    elif platform == 'YouTube Audio':
        if download_type == 'Single Track':
            return 'YTAudTrack'
        elif download_type in ['Playlist Track', 'Album']:
            return 'YTAudPlaylist'
        else:
            return 'YTAud'
    
    elif platform == 'YouTube Music':
        if download_type == 'Single Track':
            return 'YTMusicTrack'
        elif download_type == 'Playlist Track':
            return 'YTMusicPlaylist'
        elif download_type == 'Album':
            return 'YTMusicAlbum'
        else:
            return 'YTMusic'
    
    elif platform == 'Spotify':
        if download_type == 'Single Track':
            return 'SpotifyTrack'
        elif download_type == 'Playlist':
            return 'SpotifyPlaylist'
        elif download_type == 'Album':
            return 'SpotifyAlbum'
        else:
            return 'Spotify'
    
    return platform


def display_history():
    """Display download history with nice formatting"""
    clear()
    print("=== Download History ===\n")
    
    # Display statistics
    stats = get_history_stats()
    print(f"YTVid: {stats['yt_video']}  |  YTAud: {stats['yt_audio']}  |  YTMusic: {stats['yt_music']}  |  Spotify: {stats['spotify']}")
    print(f"\nTotal Durasi: {format_duration(stats['total_duration'])}\n")
    print("-" * 52)
    
    if not RuntimeConfig.DOWNLOAD_HISTORY:
        print_info("Belum ada riwayat download.")
        return
    
    # Display latest entries
    for entry in reversed(RuntimeConfig.DOWNLOAD_HISTORY[-20:]):  # Show last 20
        success_symbol = "[✓]" if entry['success'] else "[✗]"
        title = truncate_title(entry['title'])
        platform_alias = get_platform_alias(entry['platform'], entry['download_type'])
        date = entry['date_display']
        
        line = f"{success_symbol} - {title} - {platform_alias} - {date}"
        print(line)
    
    print(f"\nTotal: {len(RuntimeConfig.DOWNLOAD_HISTORY)} entries")