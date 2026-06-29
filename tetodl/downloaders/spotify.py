"""
Spotify downloader
"""
import os
import sys
import subprocess
from ..constants import RuntimeConfig, SPOTDL_CMD, FFMPEG_CMD, IS_TERMUX
from ..utils.console import console
from ..utils.i18n_keys import Keys
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
        console.err(Keys.spot.invalid_url)
        return
    if not check_internet():
        console.err(Keys.spot.no_internet)
        return

    if RuntimeConfig.SIMPLE_MODE:
        console.proc(Keys.spot.simple_mode_download(path=RuntimeConfig.MUSIC_ROOT))
        target_dir = RuntimeConfig.MUSIC_ROOT
    else:
        target_dir = select_download_folder(RuntimeConfig.MUSIC_ROOT, "music")
        if not target_dir:
            console.warn(Keys.spot.cancelled)
            return

    url_type = classify_spotify_url(url)
    if url_type != "Unknown":
        console.proc(Keys.spot.type_detected(type=url_type))
    else:
        console.err(Keys.spot.classification_failed)
        return

    # Scan target folder to ensure no .nomedia
    if IS_TERMUX:
        remove_nomedia_file(target_dir)

    console.proc(Keys.spot.downloading)

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
            console.debug(Keys.spot.command_debug(command=' '.join(cmd)))
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




    if success:
        console.ok(Keys.spot.download_complete)

        # History & Scan
        url_type = classify_spotify_url(url)

        add_to_history(True, f"Spotify {url_type}", "audio", "Spotify", url_type, 0)
        if RuntimeConfig.MEDIA_SCANNER_ENABLED:
            scan_media_files(target_dir)

    else:
        console.err(Keys.spot.download_failed)
        if last_error:
            console.warn(Keys.spot.error_details)
            print(last_error.strip())
        else:
            console.warn(Keys.spot.no_valid_spotdl_method)
            console.warn(Keys.spot.spotdl_binary_path(path=SPOTDL_CMD))
            console.warn(Keys.spot.python_interpreter(interpreter=sys.executable))

        url_type = classify_spotify_url(url)
        add_to_history(False, f"Spotify {url_type} Error", "audio", "Spotify", url_type, 0)