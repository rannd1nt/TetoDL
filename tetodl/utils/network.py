"""
Network utilities: internet check, URL validation, FastAPI file sharing
"""
import re
import os
import socket
import shutil
from urllib.parse import quote
from pathlib import Path
import subprocess
import webbrowser
import requests
from ..utils.i18n_keys import Keys
from tetodl.utils.tracer import trace
from .formatters import console as rich_console
from ..utils.console import console
from ..constants import IS_TERMUX, IS_WSL

@trace
def check_internet() -> bool:
    """Check if internet connection is available"""
    try:
        with console.spin(Keys.download.youtube.checking_internet):
            r = requests.get("https://www.google.com", timeout=5)
            result = r.status_code == 200
            return result
    except Exception:
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

def check_firewall_status(port):
    """
    Memberikan HINTS kepada user jika terdeteksi di Distro yang ketat.
    """
    if IS_WSL:
        return

    if shutil.which("ufw"):
        rich_console.print("\n[dim][Tip] If connection fails, allow port in UFW:[/dim]")
        rich_console.print(f"[dim cyan]  sudo ufw allow {port}/tcp[/dim cyan]")
    
    elif shutil.which("firewall-cmd"):
        rich_console.print("\n[dim][Tip] If connection fails, allow port in FirewallD:[/dim]")
        rich_console.print(f"[dim cyan]  sudo firewall-cmd --add-port={port}/tcp --temporary[/dim cyan]")


# --- MAIN SHARING FUNCTION (FastAPI) ---

def start_share_server(file_path_str: str, start_port=8989):
    import qrcode
    import uvicorn
    from fastapi import FastAPI
    from ..utils.share import create_share_router

    path = Path(file_path_str).resolve()
    
    if not path.exists():
        console.err(Keys.net.file_dir_not_found(path=str(path)))
        return

    port = find_free_port(start_port)
    if port is None:
        console.err(Keys.net.ports_busy(start=start_port, end=start_port+10))
        return

    if IS_WSL:
        ip_address = '127.0.0.1'
    else:
        ip_address = get_best_ip()

    if IS_WSL:
        rich_console.print("\n[bold yellow][!] WSL Environment Detected[/bold yellow]")
        console.warn(Keys.net.wsl_nat_warning)
        console.warn(Keys.net.wsl_share_tip)

    if ip_address.startswith("127.") and not IS_WSL:
        console.err(Keys.net.no_lan_ip)
        console.warn(Keys.net.localhost_only)

    if path.is_file():
        serve_dir = path.parent
        filename_url = quote(path.name)
        target_url = f"http://{ip_address}:{port}/{filename_url}"
    else:
        serve_dir = path
        target_url = f"http://{ip_address}:{port}/"

    # Build FastAPI app with share router
    app = FastAPI()
    router = create_share_router(str(serve_dir))
    app.include_router(router)

    qr = qrcode.QRCode(version=1, box_size=1, border=1)
    qr.add_data(target_url)
    qr.make(fit=True)

    console.ok(Keys.net.sharing_started)
    rich_console.print()

    rich_console.print(f"Hosting: [cyan]{path.name}[/cyan]")
    rich_console.print(f"Address: [yellow]{target_url}[/yellow]")
    
    check_firewall_status(port)
    
    rich_console.print()
    qr.print_ascii(invert=True) 
    
    rich_console.print()
    rich_console.print("[dim]Scan QR above with your phone camera.[/dim]")
    rich_console.print("[bold red]Press Ctrl+C to stop server.[/bold red]")

    try:
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="error")
    except KeyboardInterrupt:
        rich_console.print("\n[yellow]Sharing stopped.[/yellow]")
        raise KeyboardInterrupt

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
