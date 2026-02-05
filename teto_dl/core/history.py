"""
Download history tracking system
"""
import os
import json
from collections import Counter
from datetime import datetime

from ..constants import HISTORY_PATH, RuntimeConfig
from ..core.registry import registry
from ..utils.styles import console


# --- LOAD, SAVE, RESET, ADD  ---

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
    except Exception as e:
        console.print(f"[red]Gagal menyimpan history: {e}[/red]")

def reset_history():
    """Clear all download history"""
    try:
        if os.path.exists(HISTORY_PATH):
            os.remove(HISTORY_PATH)
        RuntimeConfig.DOWNLOAD_HISTORY = []
        return True
    except Exception as e:
        console.print(f"[red]Gagal menghapus history: {e}[/red]")
        return False

def add_to_history(
        id, file_path, success, title, content_type, platform,
        download_type, duration, metadata=None
    ):
    """Add entry to download history"""

    entry = {
        'id': id,
        'file_path': file_path,
        'success': success,
        'title': title, 
        'content_type': content_type,
        'platform': platform,
        'download_type': download_type,
        'duration': duration,
        'timestamp': datetime.now().isoformat(),
        'date_display': datetime.now().strftime("%d %b %y, %H.%M")
    }

    if id:
        RuntimeConfig.DOWNLOAD_HISTORY = [
            x for x in RuntimeConfig.DOWNLOAD_HISTORY 
            if x.get('id') != id
        ]

    RuntimeConfig.DOWNLOAD_HISTORY.append(entry)
    save_history()

    if success and id and file_path:
        if metadata is None: metadata = {}

        registry.register_download(
            video_id=id,
            file_path=file_path,
            content_type=content_type,
            metadata={
                'artist': metadata.get('artist'),
                'album': metadata.get('album'),
                'title': title
            }
        )
        

    
def calculate_stats():
    """Mengolah raw data dari registry.json menjadi statistik."""
    stats = {
        'total_files': 0,
        'total_audio': 0,
        'total_video': 0,
        'artists': Counter(),
        'albums': Counter(),
        'most_played_path': None,
        'most_played_count': 0
    }

    raw_data = registry.data

    for video_id, content_types in raw_data.items():
        for c_type, data in content_types.items():
            count = data.get('c', 1)
            artist = data.get('a', 'Unknown')
            album = data.get('l')
            title = data.get('t', 'Unknown')
            
            stats['total_files'] += 1
            if 'audio' in c_type:
                stats['total_audio'] += 1
            else:
                stats['total_video'] += 1

            if artist and "Unknown" not in artist:
                stats['artists'][artist] += count

            if album and "Unknown" not in album and "YouTube" not in album:
                full_album_key = f"{artist} - {album}"
                stats['albums'][full_album_key] += count

            if count > stats['most_played_count']:
                stats['most_played_count'] = count
                stats['most_played_path'] = f"{artist} - {title}"

    return stats

def get_history_stats():
    stats = {
        'yt_video': 0, 'yt_audio': 0, 'yt_music': 0,
        'spotify': 0, 'total_duration': 0
    }
    
    for entry in RuntimeConfig.DOWNLOAD_HISTORY:
        if entry.get('success', True): 
            p = entry.get('platform', '')
            if 'Video' in p: stats['yt_video'] += 1
            elif 'Audio' in p: stats['yt_audio'] += 1
            elif 'Music' in p: stats['yt_music'] += 1
            elif 'Spotify' in p: stats['spotify'] += 1
            
            stats['total_duration'] += entry.get('duration', 0)
    
    return stats

