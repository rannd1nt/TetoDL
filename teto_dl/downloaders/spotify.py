"""
Spotify downloader
"""
import os
import sys
import time
import threading
import subprocess
from ..constants import RuntimeConfig
from ..utils.colors import (
    print_process, print_info, print_success, 
    print_error, Colors
)
from ..utils.network import (
    is_valid_spotify_url, classify_spotify_url, check_internet
)
from ..utils.file_utils import create_nomedia_file
from ..core.history import add_to_history
from ..media.scanner import scan_media_files
from ..ui.navigation import select_download_folder


def download_spotify(url):
    """Download Spotify tracks, playlists, or albums"""
    if not is_valid_spotify_url(url):
        print_error("URL Spotify tidak valid.")
        return
    if not check_internet():
        print_error("Tidak ada koneksi internet atau internet kurang stabil.")
        return

    if RuntimeConfig.SIMPLE_MODE:
        print_process(f"Simple Mode: Download langsung ke {RuntimeConfig.MUSIC_ROOT}")
        target_dir = RuntimeConfig.MUSIC_ROOT
    else:
        target_dir = select_download_folder(RuntimeConfig.MUSIC_ROOT, "music")
        if not target_dir:
            print_info("Dibatalkan.")
            return

    url_type = classify_spotify_url(url)
    if url_type != "Unknown":
        print_process(f"Spotify {url_type} terdeteksi")
    else:
        print_error("URL Classification gagal, URL tidak diketahui.")

    # Scan target folder to ensure no .nomedia
    create_nomedia_file(target_dir)

    done = False
    def spinner():
        symbols = ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"]
        idx = 0
        while not done:
            print(f"\r{Colors.BLUE}[i]{Colors.WHITE} Downloading... {symbols[idx]}", end="", flush=True)
            idx = (idx + 1) % len(symbols)
            time.sleep(0.1)
    
    spin_thread = threading.Thread(target=spinner, daemon=True)
    spin_thread.start()

    cmd = [
        "python3", "-m", "spotdl",
        url,
        "--output", os.path.join(target_dir, "{artist} - {title}.{output-ext}")
    ]
    
    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
    except Exception as e:
        done = True
        print("\n" + " " * 50)  # Clear spinner line
        print_error(f"Gagal menjalankan spotdl: {e}")
        input("\nTekan Enter untuk kembali ke menu...")
        return

    done = True
    time.sleep(0.2)
    print("\r" + " " * 50 + "\r", end="")  # Clear spinner line

    if res.returncode == 0:
        print_success("Download Spotify selesai.")
        
        # For Spotify, we can't easily get individual metadata
        # So we add a generic entry to history
        url_type = classify_spotify_url(url)
        add_to_history(True, f"Spotify {url_type}", "audio", "Spotify", url_type, 0)
        
        # Scan media if download is complete
        scan_media_files(target_dir)
        
    else:
        print_error("Download gagal.")
        url_type = classify_spotify_url(url)
        add_to_history(False, f"Spotify {url_type} Error", "audio", "Spotify", url_type, 0)
        print(res.stderr.strip())