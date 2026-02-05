"""
Network utilities: internet check, URL validation
"""
import re
import os
import subprocess
import webbrowser
import requests
from ..utils.i18n import get_text as _
from ..utils.styles import print_info, print_error, print_success
from ..utils.spinner import Spinner
from ..constants import IS_TERMUX, IS_WSL


def check_internet() -> bool:
    """Check if internet connection is available"""
    spinner = Spinner(_('download.youtube.checking_internet'))
    try:
        spinner.start()
        r = requests.get("https://www.google.com", timeout=5)
        spinner.stop()
        return r.status_code == 200
    except Exception:
        spinner.stop()
        return False

def open_url(url: str) -> bool:
    """
    Membuka URL di browser default.
    Menangani Termux, WSL, Windows, dan Linux Native.
    Returns: True jika berhasil dieksekusi, False jika gagal.
    """
    try:
        if IS_TERMUX:
            subprocess.run(
                ["am", "start", "-a", "android.intent.action.VIEW", "-d", url],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False
            )
            return True

        elif IS_WSL:
            subprocess.run(
                ["explorer.exe", url], 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL,
                check=False
            )
            return True

        else:
            try:
                subprocess.run(
                    ["xdg-open", url],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True
                )
                return True
            except (OSError, subprocess.CalledProcessError):
                webbrowser.open(url)
                return True

    except Exception:
        return False

def perform_update():
    # Cek apakah ini git repo
    if not os.path.isdir(".git"):
        print_error("Not a git repository. Cannot auto-update.")
        # print_info("If you installed via AUR, please use 'yay -Syu'.")
        return

    try:
        print_info("Pulling latest changes from remote...")
        subprocess.check_call(["git", "pull"])
        print_success("Update successful! Please restart TetoDL.")
    except subprocess.CalledProcessError:
        print_error("Git pull failed. Please check your internet or git status.")
    except FileNotFoundError:
        print_error("Git command not found. Please install git.")

def is_forbidden_error(e):
    """Mendeteksi HTTP 403 Forbidden"""
    error_str = str(e).lower()
    return "http error 403" in error_str or "forbidden" in error_str

def is_connection_error(e):
    pass

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