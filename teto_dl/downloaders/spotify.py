"""
Spotify downloader
"""
import os
import sys
import time
import threading
import subprocess
from ..constants import RuntimeConfig, SPOTDL_CMD, FFMPEG_CMD, IS_TERMUX
from ..utils.styles import (
    print_process, print_info, print_success,
    print_error, Colors
)
from ..utils.network import (
    is_valid_spotify_url, classify_spotify_url, check_internet
)
from ..utils.files import remove_nomedia_file
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
        return

    # Scan target folder to ensure no .nomedia
    if IS_TERMUX:
        remove_nomedia_file(target_dir)

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

    base_args = [
        url,
        "--output", os.path.join(target_dir, "{artist} - {title}.{output-ext}"),
        "--format", RuntimeConfig.AUDIO_QUALITY
    ]

    if FFMPEG_CMD and "/" in FFMPEG_CMD and not FFMPEG_CMD.strip() == "ffmpeg":
         base_args.extend(["--ffmpeg", FFMPEG_CMD])

    commands_to_try = []

    if IS_TERMUX:
        commands_to_try.append([sys.executable, "-m", "spotdl"] + base_args)
        commands_to_try.append([SPOTDL_CMD] + base_args)
    else:
        commands_to_try.append([SPOTDL_CMD] + base_args)
        commands_to_try.append([sys.executable, "-m", "spotdl"] + base_args)

    success = False
    last_error = ""

    for cmd in commands_to_try:
        try:
            print(f"\n[DEBUG] Running command: {' '.join(cmd)}")
            res = subprocess.run(cmd, capture_output=False, text=True)

            if res.returncode == 0:
                success = True
                break
            else:
                if "not found" in res.stderr or "No module" in res.stderr:
                    continue
                else:
                    last_error = res.stderr
                    break

        except FileNotFoundError:
            continue
        except Exception as e:
            last_error = str(e)
            continue


    done = True
    time.sleep(0.2)
    print("\r" + " " * 50 + "\r", end="")  # Hapus spinner

    if success:
        print_success("Download Spotify selesai.")

        # History & Scan
        url_type = classify_spotify_url(url)

        add_to_history(True, f"Spotify {url_type}", "audio", "Spotify", url_type, 0)
        if RuntimeConfig.MEDIA_SCANNER_ENABLED:
            scan_media_files(target_dir)

    else:
        print_error("Download gagal.")
        if last_error:
            print_info("Detail Error:")
            print(last_error.strip())
        else:
            print_info("Gagal menemukan metode eksekusi SpotDL yang valid.")
            print_info(f"Path Binary: {SPOTDL_CMD}")
            print_info(f"Python Interpreter: {sys.executable}")

        url_type = classify_spotify_url(url)
        add_to_history(False, f"Spotify {url_type} Error", "audio", "Spotify", url_type, 0)