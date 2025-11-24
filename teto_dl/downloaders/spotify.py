"""
Spotify downloader - Fixed & Refactored
"""
import os
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

    # Select target directory
    if RuntimeConfig.SIMPLE_MODE:
        print_process(f"Simple Mode: Download langsung ke {RuntimeConfig.MUSIC_ROOT}")
        target_dir = RuntimeConfig.MUSIC_ROOT
    else:
        target_dir = select_download_folder(RuntimeConfig.MUSIC_ROOT, "music")
        if not target_dir:
            print_info("Dibatalkan.")
            return

    # Classify URL type
    url_type = classify_spotify_url(url)
    if url_type != "Unknown":
        print_process(f"Spotify {url_type} terdeteksi")
    else:
        print_error("URL Classification gagal, URL tidak diketahui.")
        return

    # Ensure target directory exists
    try:
        os.makedirs(target_dir, exist_ok=True)
        create_nomedia_file(target_dir)
    except Exception as e:
        print_error(f"Gagal membuat folder: {e}")
        return

    # Spinner thread
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
        "spotdl",
        "download",
        url,
        "--output", os.path.join(target_dir, "{artist} - {title}.{output-ext}"),
        "--format", "mp3",
        "--bitrate", "192k"
    ]
    
    try:
        res = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True,
            cwd=target_dir
        )
    except FileNotFoundError:
        done = True
        print("\n" + " " * 50)
        print_error("spotdl tidak ditemukan. Pastikan sudah terinstall.")
        print_info("Install dengan: pip install spotdl")
        input("\nTekan Enter untuk kembali ke menu...")
        return
    except Exception as e:
        done = True
        print("\n" + " " * 50)
        print_error(f"Gagal menjalankan spotdl: {e}")
        input("\nTekan Enter untuk kembali ke menu...")
        return

    done = True
    time.sleep(0.2)
    print("\r" + " " * 50 + "\r", end="")  # Clear spinner line

    # Check result
    if res.returncode == 0:
        print_success("Download Spotify selesai.")
        
        # Add to history
        url_type = classify_spotify_url(url)
        add_to_history(True, f"Spotify {url_type}", "audio", "Spotify", url_type, 0)
        
        # Scan media files
        scan_media_files(target_dir)
        
    else:
        print_error("Download gagal.")
        
        # Show error details
        error_output = res.stderr.strip()
        if error_output:
            # Filter out warnings
            lines = error_output.split('\n')
            actual_errors = [
                line for line in lines 
                if 'UserWarning' not in line 
                and 'RuntimeWarning' not in line
                and 'pkg_resources' not in line
                and line.strip()
            ]
            
            if actual_errors:
                print_error("Detail error:")
                for line in actual_errors[:5]:  # Show max 5 lines
                    print(f"  {line}")
        
        # Add failed entry to history
        url_type = classify_spotify_url(url)
        add_to_history(False, f"Spotify {url_type} Error", "audio", "Spotify", url_type, 0)
        
        input("\nTekan Enter untuk kembali ke menu...")