"""
Network utilities: internet check, URL validation, FastAPI file sharing
"""
import os
import re
import shutil
import socket
import subprocess
import webbrowser

import requests
from requests.adapters import HTTPAdapter

from tetodl.utils.tracer import trace

from ..utils.console import console
from ..utils.i18n_keys import Keys

_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}
_session: requests.Session | None = None


def get_session() -> requests.Session:
    """Lazily-initialized shared session with connection pooling."""
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers.update(_DEFAULT_HEADERS)
        adapter = HTTPAdapter(pool_connections=10, pool_maxsize=20)
        _session.mount("https://", adapter)
        _session.mount("http://", adapter)
    return _session


@trace
def check_internet() -> bool:
    """Check if internet connection is available"""
    try:
        with console.spin(Keys.download.youtube.checking_internet):
            r = get_session().get("https://www.google.com", timeout=5)
            result = r.status_code == 200
            return result
    except Exception:
        return False

def _detect_termux() -> bool:
    return bool(os.environ.get("TERMUX_VERSION")) or shutil.which("termux-open") is not None


def _detect_wsl() -> bool:
    return bool(os.environ.get("WSL_DISTRO_NAME")) or os.path.exists("/proc/sys/fs/binfmt_misc/WSLInterop")


def open_url(url: str) -> bool:
    """
    Membuka URL di browser default.
    Menangani Termux, WSL, Windows, dan Linux Native.
    Returns: True jika berhasil dieksekusi, False jika gagal.
    """
    try:
        if _detect_termux():
            subprocess.run(
                ["am", "start", "-a", "android.intent.action.VIEW", "-d", url],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False
            )
            return True

        elif _detect_wsl():
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


def get_best_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(('8.8.8.8', 1))
            return s.getsockname()[0]
    except Exception:
        pass

    local_ranges = ['192.168.255.255', '10.255.255.255', '172.31.255.255']
    for test_ip in local_ranges:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect((test_ip, 1))
                ip = s.getsockname()[0]
                if not ip.startswith("127."):
                    return ip
        except Exception:
            continue

    try:
        ip = socket.gethostbyname(socket.gethostname())
        return ip
    except Exception:
        pass

    return '127.0.0.1'

def find_free_port(start_port=8989, max_tries=10):
    """
    Mencari port kosong mulai dari start_port.
    """
    for port in range(start_port, start_port + max_tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.1)
            if s.connect_ex(('localhost', port)) != 0:
                return port
    return None

def perform_update():
    if not os.path.isdir(".git"):
        console.err(Keys.net.not_git_repo)
        return

    try:
        console.warn(Keys.net.pulling_latest)
        subprocess.check_call(["git", "pull"])
        console.ok(Keys.net.update_successful)
    except subprocess.CalledProcessError:
        console.err(Keys.net.git_pull_failed)
    except FileNotFoundError:
        console.err(Keys.net.git_command_not_found)

def is_forbidden_error(e):
    """Mendeteksi HTTP 403 Forbidden"""
    error_str = str(e).lower()
    return "http error 403" in error_str or "forbidden" in error_str

def is_connection_error(e):
    pass

@trace
def is_valid_youtube_url(url: str) -> bool:
    """Check if URL is a valid YouTube/YouTube Music URL"""
    youtube_patterns = [
        r'https?://(www\.)?(youtube\.com|youtu\.be)/.+',
        r'https?://(www\.)?music\.youtube\.com/.+'
    ]
    result = any(re.match(pattern, url) for pattern in youtube_patterns)
    return result


@trace
def is_youtube_music_url(url: str) -> bool:
    """Check if URL is from YouTube Music"""
    result = 'music.youtube.com' in url
    return result


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
