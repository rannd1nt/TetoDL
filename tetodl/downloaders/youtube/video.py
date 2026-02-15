"""
Core logic for single video processing
"""
import os
import glob
from typing import Optional, Tuple, Union, List

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

def download_single_video(
    url: str, 
    target_dir: str, 
    use_cache: bool = True, 
    download_type: str = "Single Video", 
    cut_range: Optional[Tuple[float, float]] = None, 
    quiet: bool = False
) -> Tuple[bool, str, bool]:
    """
    Manages the download and post-processing of a single video file.

    This function configures `yt-dlp` based on runtime preferences (codec/container).
    It supports advanced trimming via `cut_range`, allowing users to download specific 
    segments (e.g., '-1:02:12' for beginning-to-timestamp or '1:2:12-' for timestamp-to-end)
    without downloading the entire file first.
    """

    current_style = getattr(RuntimeConfig, 'PROGRESS_STYLE', 'minimal')
    target_container = getattr(RuntimeConfig, 'VIDEO_CONTAINER', 'mp4')
    target_codec = getattr(RuntimeConfig, 'VIDEO_CODEC', 'default')

    pp_args: List[str] = []

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

    try:
        outtmpl = os.path.join(target_dir, "%(title)s.%(ext)s")
        video_format = get_video_format_string()
        dl_hook = [] if quiet else [get_progress_hook(current_style)]
        pp_hook = [] if quiet else [get_postprocessor_hook(_('media.encoding', codec=target_codec.upper()))]

        ydl_opts = {
            'format': video_format,
            'merge_output_format': target_container,
            'outtmpl': outtmpl,
            'ffmpeg_location': FFMPEG_CMD,
            'quiet': True,
            'no_warnings': True,
            'logger': QuietLogger(),
            'progress_hooks': dl_hook,
            'postprocessor_hooks': pp_hook,
            'postprocessor_args': pp_args if pp_args else None,
            'retries': RuntimeConfig.MAX_RETRIES,
            'fragment_retries': RuntimeConfig.MAX_RETRIES,
            'file_access_retries': RuntimeConfig.MAX_RETRIES,
            'extractor_retries': 3,
        }


        if cut_range:
            start, end = cut_range
            if not quiet: print_info(f"Trimming video: {start}s to {end}s (This may take longer)")

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
                    if not quiet: print_info(_('download.youtube.using_cache', title=cached['metadata'].get('title', 'Unknown')))

            temp_filename_template = ydl.prepare_filename(info)
            base_name_clean = os.path.splitext(temp_filename_template)[0]
            # Pattern video bisa beda ekstensi sebelum merge
            possible_part_files = [
                f"{base_name_clean}.{target_container}.part",
                f"{base_name_clean}.mp4.part",
                f"{base_name_clean}.webm.part",
                f"{base_name_clean}.part"
            ]

            # Download Phase
            try:
                if cut_range:
                    if not quiet:
                        cut_spinner = Spinner(_('download.youtube.downloading_item', title=title) + ", Cutting...")
                        cut_spinner.start()
                    try:
                        ydl.download([url])
                    finally:
                        if not quiet:
                            cut_spinner.stop()
                else:
                    if not quiet: print_process(_('download.youtube.downloading_item', title=title))
                    ydl.download([url])
            
            except (KeyboardInterrupt, Exception) as e:
                if not quiet: print() 
                if isinstance(e, KeyboardInterrupt):
                    if not quiet: print_error("Download cancelled by user.")
                else:
                    if not quiet: print_error(_('download.youtube.error_downloading', type='video', error=str(e)))
                
                if not quiet: print_process("Cleaning up partial files...\r")
                
                for p_file in possible_part_files:
                    if os.path.exists(p_file):
                        try: os.remove(p_file)
                        except OSError: pass

                try:
                    for f in glob.glob(f"{base_name_clean}*"):
                        if f.endswith('.part') or f.endswith('.ytdl'):
                            try: os.remove(f)
                            except OSError: pass
                except Exception: pass

                if isinstance(e, KeyboardInterrupt):
                    raise e
                
                return False, str(e), False

            # --- Post Processing  ---
            video_path = f"{base_name_clean}.{target_container}"
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
        if not quiet: print_error(_('download.youtube.error_downloading', type='video', error=str(e)))
        return False, str(e), False