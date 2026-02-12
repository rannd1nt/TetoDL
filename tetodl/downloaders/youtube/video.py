"""
Core logic for single video processing
"""
import os
import time

try:
    import yt_dlp as yt
except Exception:
    yt = None

from ...constants import FFMPEG_CMD, RuntimeConfig
from ...utils.i18n import get_text as _
from ...utils.styles import print_process, print_info, print_error
from ...utils.spinner import Spinner
from ...utils.network import is_forbidden_error
from ...utils.hooks import QuietLogger, get_progress_hook, get_postprocessor_hook
from ...core.cache import get_cached_metadata, cache_metadata
from ...core.config import get_video_format_string
from ...core.history import add_to_history
from ...media.scanner import scan_media_files

def download_single_video(url, target_dir, use_cache=True, download_type="Single Video", cut_range=None):
    """Download single video file"""

    current_style = getattr(RuntimeConfig, 'PROGRESS_STYLE', 'minimal')
    target_container = getattr(RuntimeConfig, 'VIDEO_CONTAINER', 'mp4')
    target_codec = getattr(RuntimeConfig, 'VIDEO_CODEC', 'default')

    pp_args = []

    if target_codec == 'h264':
        pp_args = [
            '-c:v', 'libx264',
            '-profile:v', 'main',
            '-pix_fmt', 'yuv420p',
            '-c:a', 'aac',
            '-movflags', '+faststart'
        ]
    elif target_codec == 'h265':
        pp_args = [
            '-c:v', 'libx265',
            '-c:a', 'aac'
        ]

    for attempt in range(1, RuntimeConfig.MAX_RETRIES + 1):
        try:
            outtmpl = os.path.join(target_dir, "%(title)s.%(ext)s")
            video_format = get_video_format_string()
            dl_hook = get_progress_hook(current_style)
            pp_hook = get_postprocessor_hook(_('media.encoding', codec=target_codec.upper()))

            ydl_opts = {
                'format': video_format,
                'merge_output_format': target_container,
                'outtmpl': outtmpl,
                'ffmpeg_location': FFMPEG_CMD,
                'quiet': True,
                'no_warnings': True,
                'logger': QuietLogger(),
                'progress_hooks': [dl_hook],
                'postprocessor_hooks': [pp_hook],
                'postprocessor_args': pp_args if pp_args else None
            }

            if cut_range:
                start, end = cut_range
                print_info(f"Trimming video: {start}s to {end}s (This may take longer)")

                ydl_opts['download_ranges'] = lambda info, ydl: [{'start_time': start, 'end_time': end}]
                ydl_opts['force_keyframes_at_cuts'] = True

            with yt.YoutubeDL(ydl_opts) as ydl:
                # Extract info
                info = ydl.extract_info(url, download=False)
                video_id = info.get('id')
                title = info.get('title', 'Unknown')
                duration = info.get('duration', 0)
                uploader = info.get('uploader') or info.get('channel') or "Unknown Channel"

                if use_cache:
                    cached = get_cached_metadata(url)
                    if cached:
                        print_info(_('download.youtube.using_cache', title=cached['metadata'].get('title', 'Unknown')))

                if cut_range:
                    cut_spinner = Spinner(_('download.youtube.downloading_item', title=title) + ", Cutting...")
                    cut_spinner.start()
                    try:
                        ydl.download([url])
                    finally:
                        cut_spinner.stop()
                else:
                    print_process(_('download.youtube.downloading_item', title=title))
                    ydl.download([url])

                # --- Post Processing  ---
                temp_filename = ydl.prepare_filename(info)
                base_name = os.path.splitext(temp_filename)[0]
                video_path = f"{base_name}.mp4"
                final_video_path = os.path.abspath(video_path)

                if use_cache:
                    cache_metadata(url, {
                        'title': title,
                        'duration': duration,
                        'uploader': info.get('uploader', '')
                    })

                metadata = {
                    'artist': uploader,
                    'album': "YouTube Video", 
                    'title': title
                }

                add_to_history(
                    id=video_id,
                    file_path=final_video_path,
                    success=True, 
                    title=title, 
                    content_type='video', 
                    platform="YouTube Video", 
                    download_type=download_type, 
                    duration=duration,
                    metadata=metadata
                )

                if RuntimeConfig.MEDIA_SCANNER_ENABLED:
                    if os.path.exists(final_video_path):
                        scan_media_files(final_video_path)

            return True, title, False

        except Exception as e:
            if is_forbidden_error(e):
                print_error(f"Forbidden 403 Error detected.")
                if attempt < RuntimeConfig.MAX_RETRIES:
                    print_process(f"Retrying, attempt {attempt}/{RuntimeConfig.MAX_RETRIES}...")
                    time.sleep(RuntimeConfig.RETRY_DELAY)
                    continue
                else:
                    print_error(f"Failed after {RuntimeConfig.MAX_RETRIES} attempts due to 403 Forbidden.")
                    return False, str(e), False
            else:
                print_error(_('download.youtube.error_downloading', type='video', error=str(e)))
                return False, str(e), False