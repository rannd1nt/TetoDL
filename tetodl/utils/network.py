"""
Network utilities: internet check, URL validation
"""
import re
import os
import socket
import http.server
import socketserver
import shutil
import qrcode
from urllib.parse import quote
from pathlib import Path
import subprocess
import webbrowser
import requests
from ..utils.i18n import get_text as _
from ..utils.styles import print_info, print_error, print_success, console
from ..utils.spinner import Spinner
from ..utils.server_styles import TetoHTTPHandler
from ..constants import IS_TERMUX, IS_WSL

class SilentTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """
    Multi-threaded Server & Silent Log.
    """
    allow_reuse_address = True
    daemon_threads = True
    
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)

    def handle_error(self, request, client_address):
        pass

def check_internet(quiet=False) -> bool:
    """Check if internet connection is available"""
    if not quiet:
        spinner = Spinner(_('download.youtube.checking_internet'))
    try:
        if not quiet:
            spinner.start()
        r = requests.get("https://www.google.com", timeout=5)
        if not quiet:
            spinner.stop()
        return r.status_code == 200
    except Exception:
        if not quiet:
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


def get_best_ip():
    """
    Mencoba mendapatkan IP LAN yang paling valid.
    """
    ip = '127.0.0.1'
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0.1)
    try:
        s.connect(('8.8.8.8', 1))
        ip = s.getsockname()[0]
    except Exception:
        try:
            ip = socket.gethostbyname(socket.gethostname())
        except:
            pass
    finally:
        s.close()
    return ip

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
        console.print(f"\n[dim][Tip] If connection fails, allow port in UFW:[/dim]")
        console.print(f"[dim cyan]  sudo ufw allow {port}/tcp[/dim cyan]")
    
    elif shutil.which("firewall-cmd"):
        console.print(f"\n[dim][Tip] If connection fails, allow port in FirewallD:[/dim]")
        console.print(f"[dim cyan]  sudo firewall-cmd --add-port={port}/tcp --temporary[/dim cyan]")


# --- MAIN SHARING FUNCTION ---

def start_share_server(file_path_str: str, start_port=8989):
    path = Path(file_path_str).resolve()
    
    if not path.exists():
        print_error(f"File/Directory not found: {path}")
        return

    port = find_free_port(start_port)
    if port is None:
        print_error(f"All ports from {start_port} to {start_port+10} are busy.")
        return

    if IS_WSL:
        ip_address = '127.0.0.1'
    else:
        ip_address = get_best_ip()
    using_wsl_bridge = False

    if IS_WSL:
        console.print(f"\n[bold yellow][!] WSL Environment Detected[/bold yellow]")
        print_info("WSL uses a separate network (NAT). Devices on your local Wi-Fi likely CANNOT connect to this IP.")
        print_info("Tip: Move the file to Windows (/mnt/c/...) and share from there.")
        # return

    if ip_address.startswith("127.") and not IS_WSL:
        print_error("Cannot detect valid LAN IP. Are you connected to Wi-Fi/Hotspot?")
        print_info("Sharing via localhost only (Phone won't connect).")

    if path.is_file():
        serve_dir = path.parent
        filename_url = quote(path.name)
        target_url = f"http://{ip_address}:{port}/{filename_url}"
    else:
        serve_dir = path
        target_url = f"http://{ip_address}:{port}/"

    os.chdir(serve_dir)

    qr = qrcode.QRCode(version=1, box_size=1, border=1)
    qr.add_data(target_url)
    qr.make(fit=True)

    print_success("TetoDL Sharing started!")
    console.print()

    if using_wsl_bridge:
        console.print("[bold cyan][WINDOWS BRIDGE ACTIVE][/bold cyan]", justify="center")

    console.print(f"Hosting: [cyan]{path.name}[/cyan]")
    console.print(f"Address: [yellow]{target_url}[/yellow]")
    
    check_firewall_status(port)
    
    console.print()
    qr.print_ascii(invert=True) 
    
    console.print()
    console.print("[dim]Scan QR above with your phone camera.[/dim]")
    console.print("[bold red]Press Ctrl+C to stop server.[/bold red]")

    try:
        with SilentTCPServer(("", port), TetoHTTPHandler) as httpd:
            httpd.serve_forever()
    except OSError as e:
        print_error(f"Network error: {str(e)}")
    except KeyboardInterrupt:
        console.print("\n[yellow]Sharing stopped.[/yellow]")
        raise KeyboardInterrupt

def perform_update():
    if not os.path.isdir(".git"):
        print_error("Not a git repository. Cannot auto-update.")
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