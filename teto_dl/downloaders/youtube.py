"""
YouTube video and audio downloader
"""
import os
import time

try:
    import yt_dlp as yt
    from yt_dlp.utils import sanitize_filename
except Exception:
    yt = None

from ..constants import (
    FFMPEG_CMD, RuntimeConfig, IS_TERMUX
)
from ..utils.i18n import get_text as _
from ..utils.styles import print_process, print_info, print_success, print_error, clear, color
from ..utils.spinner import Spinner
from ..utils.network import (
    is_valid_youtube_url, classify_youtube_url, check_internet,
    is_forbidden_error
)
from ..utils.hooks import QuietLogger, get_progress_hook, get_postprocessor_hook
from ..utils.files import remove_nomedia_file, clean_temp_files
from ..utils.processing import (
    get_audio_extension, get_audio_format_string, extract_video_id,
    build_audio_postprocessors, extract_all_urls_from_content
)
from ..core.cache import get_cached_metadata, cache_metadata
from ..core.config import get_video_format_string
from ..core.history import add_to_history
from ..core.registry import registry
from ..utils.display import wait_and_clear_prompt
from ..ui.components import header
from ..media.scanner import scan_media_files
from ..media.thumbnail import download_and_process_thumbnail, embed_thumbnail_to_audio, convert_thumbnail_format
from ..ui.navigation import select_download_folder

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


def download_single_audio(url, target_dir, use_cache=True, is_youtube_music=False, download_type="Single Track", cut_range=None):
    """Download single audio file with cache support, metadata, and 403 retry logic"""

    audio_format = get_audio_extension()
    current_style = getattr(RuntimeConfig, 'PROGRESS_STYLE', 'minimal')

    for attempt in range(1, RuntimeConfig.MAX_RETRIES + 1):
        try:
            with yt.YoutubeDL({'quiet': True, 'no_warnings': True, 'extract_flat': False}) as ydl:
                info = ydl.extract_info(url, download=False)
                id = info.get('id')
                title = info.get('title', 'Unknown')
                duration = info.get('duration', 0)
                artist = info.get('artist') or info.get('uploader') or "Unknown Artist"
                album = info.get('album')
                
                if is_youtube_music:
                    history_title = f"{artist} - {title}"
                else:
                    history_title = title

            if is_youtube_music:
                outtmpl = os.path.join(target_dir, f"%(artist)s - %(title)s.%(ext)s")
            else:
                outtmpl = os.path.join(target_dir, f"%(title)s.%(ext)s")

            
            format_string = get_audio_format_string(audio_format)
            postprocessors = build_audio_postprocessors(audio_format, is_youtube_music)
            hook = get_progress_hook(current_style)

            ydl_opts = {
                'format': format_string,
                'outtmpl': outtmpl,
                'postprocessors': postprocessors,
                'ffmpeg_location': FFMPEG_CMD,
                'quiet': True,
                'no_warnings': True,
                'writethumbnail': False,
                'logger': QuietLogger(),
                'progress_hooks': [hook],
            }

            if RuntimeConfig.NO_COVER_MODE:
                ydl_opts['postprocessors'] = [
                    pp for pp in ydl_opts['postprocessors'] 
                    if pp.get('key') != 'FFmpegMetadata'
                ]
                ydl_opts['add_metadata'] = False

            if cut_range:
                start, end = cut_range
                print_info(f"Trimming audio: {start}s to {end}s")
                
                ydl_opts['download_ranges'] = lambda info, ydl: [{'start_time': start, 'end_time': end}]
                ydl_opts['force_keyframes_at_cuts'] = True

            with yt.YoutubeDL(ydl_opts) as ydl:
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

                final_scan_path = None
                
                if RuntimeConfig.NO_COVER_MODE:
                    should_process_cover = False
                else:
                    should_process_cover = (
                        (is_youtube_music or RuntimeConfig.SMART_COVER_MODE)
                        and audio_format != "opus"
                    )

                if should_process_cover:
                    print_process(_('download.youtube.processing_cover'))
                    
                    uploader = info.get('uploader', '')
                    description = info.get('description', '')
                    
                    is_art_track = (
                        info.get('track') is not None or
                        ' - Topic' in uploader or
                        'Auto-generated by YouTube' in description or
                        'Provided to YouTube by' in description
                    )
                    
                    if is_art_track:
                        if not is_youtube_music:
                            print_process(_('download.youtube.processing_art_track'))
                        should_crop = True
                        smart_search = False 
                    else:
                        should_crop = False
                        smart_search = RuntimeConfig.SMART_COVER_MODE

                    thumbnail_path, fetched_metadata = download_and_process_thumbnail(
                        info, 
                        target_dir, 
                        should_crop=should_crop, 
                        smart_mode=smart_search
                    )

                    if thumbnail_path and os.path.exists(thumbnail_path):
                        temp_filename_raw = ydl.prepare_filename(info)
                        base_name = os.path.splitext(temp_filename_raw)[0]
                        audio_path = f"{base_name}.{audio_format}"
                        
                        if os.path.exists(audio_path):
                            print_process(_('download.youtube.embedding_cover'))
                            final_metadata = {}
                            if fetched_metadata:
                                final_metadata = fetched_metadata
                            elif is_art_track or info.get('artist'):
                                final_metadata = {
                                    'artist': info.get('artist') or info.get('uploader', '').replace(' - Topic', ''),
                                    'album': info.get('album') or info.get('title'),
                                    'title': info.get('track') or info.get('title')
                                }

                            if embed_thumbnail_to_audio(audio_path, thumbnail_path, audio_format, final_metadata):
                                print_success(_('download.youtube.cover_success'))
                            else:
                                print_error(_('download.youtube.cover_failed'))
                                final_scan_path = audio_path
                        else:
                            print_error(_('download.youtube.file_not_found', filename=os.path.basename(audio_path)))
                        clean_temp_files(target_dir, info.get('id', ''))
                    else:
                        print_error(_('download.youtube.cover_process_failed'))

                elif audio_format == "opus":
                    print_info(_('download.youtube.skip_cover_opus'))
                else:
                    print_info(_('download.youtube.skip_cover'))

                # --- FINISHING ---
                if final_scan_path is None:
                    temp_filename = ydl.prepare_filename(info)
                    base_name = os.path.splitext(temp_filename)[0]
                    guessed_path = f"{base_name}.{audio_format}"
                    if os.path.exists(guessed_path):
                        final_scan_path = guessed_path

                if use_cache:
                    cache_metadata(url, {
                        'title': title,
                        'duration': duration,
                        'uploader': info.get('uploader', ''),
                        'artist': info.get('artist', ''),
                        'album': info.get('album', ''),
                        'track': info.get('track', ''),
                        'thumbnails': info.get('thumbnails', [])
                    })

                platform = "YouTube Music" if is_youtube_music else "YouTube Audio"
                artist = info.get('artist') or info.get('uploader') or "Unknown Artist"
                if is_youtube_music:
                    history_title = f"{artist} - {title}"
                else:
                    history_title = title
                
                final_saved_path = os.path.abspath(final_scan_path if final_scan_path else guessed_path)

                metadata = {
                    'artist': artist,
                    'album': album,
                    'title': title
                }

                add_to_history(
                    id=id,
                    file_path=final_saved_path,
                    success=True,
                    title=history_title,
                    content_type='audio',
                    platform=platform,
                    download_type=download_type,
                    duration=duration,
                    metadata=metadata
                )

                if RuntimeConfig.MEDIA_SCANNER_ENABLED:
                    if final_scan_path:
                        abs_path = os.path.abspath(final_scan_path)
                        scan_media_files(abs_path)

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
                print_error(_('download.youtube.error_downloading', type='audio', error=str(e)))
                return False, str(e), False


def download_playlist_sequential(urls, target_dir, download_func, content_type="audio", is_youtube_music=False, content_title="Playlist"):
    """Download multiple URLs sequentially"""
    total = len(urls)
    success_count = 0
    failed_count = 0
    skipped_count = 0
    failed_urls = []

    for i, url in enumerate(urls, 1):
        video_id = extract_video_id(url)
        
        if video_id:
            exists, metadata = registry.check_existing(video_id, content_type, target_dir)
            
            if exists:
                print_process(_('download.youtube.progress', current=i, total=total))
                print_info(_('download.youtube.file_exists', title=metadata.get('title', video_id)))
                
                skipped_count += 1
                time.sleep(0.1) 
                
                continue

        print_process(_('download.youtube.progress', current=i, total=total))

        try:
            print_info(_('download.youtube.downloading_url', url=url, type=content_type))
            if content_type == "audio":
                success, result, skipped = download_func(
                    url, target_dir, use_cache=True,
                    is_youtube_music=is_youtube_music,
                    download_type="Playlist Track"
                )
            else:
                success, result, skipped = download_func(url, target_dir, use_cache=True, download_type="Playlist Video")

            if success:
                if skipped:
                    print_info(_('download.youtube.file_exists', title=result))
                    skipped_count += 1
                else:
                    print_success(_('download.youtube.success', title=result))
                    success_count += 1
            else:
                print_error(_('download.youtube.failed', title=result))
                failed_count += 1
                failed_urls.append(url)
        except Exception as e:
            print_error(_('download.youtube.error_downloading', type=content_type, error=str(e)))
            failed_count += 1
            failed_urls.append(url)

        if i < total:
            print_process(_('download.youtube.wait_delay', delay=RuntimeConfig.DOWNLOAD_DELAY))
            time.sleep(RuntimeConfig.DOWNLOAD_DELAY)

    print_success(_('download.youtube.summary',
                    success=success_count,
                    skipped=skipped_count,
                    failed=failed_count,
                    total=total,
                    type=content_type))

    return success_count, skipped_count, failed_count


def get_content_type_display(url_classification):
    """Get display string for content type"""
    platform = url_classification['platform']
    content_type = url_classification['type']

    platform_names = {'youtube': 'YouTube', 'youtube_music': 'YouTube Music'}
    type_names = {'video': 'Video', 'playlist': 'Playlist', 'album': 'Album'}

    platform_str = platform_names.get(platform, platform)
    type_str = type_names.get(content_type, content_type)

    return f"{platform_str} {type_str}"

def download_thumbnail_task(url, target_format='jpg'):
    """
    Standalone task for --thumbnail-only flag.
    Downloads cover art (Smart/YouTube) based on config without downloading media.
    """
    # 1. Setup Directory
    if RuntimeConfig.SIMPLE_MODE:
        target_dir = RuntimeConfig.THUMBNAIL_ROOT
    else:
        target_dir = select_download_folder(RuntimeConfig.THUMBNAIL_ROOT, "thumbnails")
        if not target_dir: return {'success': False, 'reason': 'cancel'}

    if not os.path.exists(target_dir):
        try:
            os.makedirs(target_dir, exist_ok=True)
        except OSError as e:
            print_error(f"Cannot create thumbnail directory: {e}")
            return {'success': False}
    
    clear()
    header()

    if not check_internet():
        print_error(_('download.youtube.no_internet'))
        return {'success': False}

    spinner = Spinner("Extracting information...")
    spinner.start()

    try:
        with yt.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:
        spinner.stop()
        print_error(f"Extraction failed: {e}")
        return {'success': False}

    spinner.stop()

    # Handle Playlist Recursion
    if 'entries' in info:
        print_info(f"Playlist detected: {info.get('title')}")
        entries = list(info['entries'])
        total = len(entries)
        print_process(f"Found {total} items. Processing thumbnails...")
        
        success_count = 0
        for i, entry in enumerate(entries, 1):
            print_process(f"[{i}/{total}] Processing: {entry.get('title')}")
            if _process_single_thumbnail(entry, target_dir, target_format=target_format):
                success_count += 1
        
        print_success(f"Processed {success_count}/{total} thumbnails.")
        wait_and_clear_prompt()
        return {'success': True}
    else:
        success = _process_single_thumbnail(info, target_dir, target_format=target_format)
        wait_and_clear_prompt()
        return {'success': success}

def _process_single_thumbnail(info, target_dir, target_format='jpg'):
    """Internal helper to process logic for a single info dict"""
    title = info.get('title', 'Unknown')
    print_process(f"Processing cover for: {title}")

    # Logic Deteksi Art Track (Sama seperti di audio downloader)
    uploader = info.get('uploader', '')
    description = info.get('description', '')
    
    is_art_track = (
        info.get('track') is not None or
        ' - Topic' in uploader or
        'Auto-generated by YouTube' in description or
        'Provided to YouTube by' in description
    )
    
    should_crop = is_art_track # Default True kalau Art Track
    smart_search = RuntimeConfig.SMART_COVER_MODE and not is_art_track

    # Panggil fungsi inti di thumbnail.py
    thumb_path, metadata = download_and_process_thumbnail(
        info, target_dir, should_crop=should_crop, smart_mode=smart_search
    )

    if thumb_path and os.path.exists(thumb_path):
        # [NEW] Format Conversion
        # Default download_and_process_thumbnail menghasilkan .jpg (atau .square.jpg)
        # Jika user minta png/webp, kita convert lagi.
        
        final_path = thumb_path
        if target_format != 'jpg':
            converted = convert_thumbnail_format(thumb_path, target_format)
            if converted:
                final_path = converted
                # thumb_path asli sudah dihapus oleh fungsi convert

        # Rename Logic
        try:
            final_title = metadata.get('title') if metadata else title
            final_artist = metadata.get('artist') if metadata else info.get('uploader')
            
            # Extension sesuai format
            ext = target_format
            
            if final_artist and final_title:
                new_name = f"{final_artist} - {final_title}.{ext}"
            else:
                new_name = f"{final_title}.{ext}"
            
            safe_name = sanitize_filename(new_name)
            new_path = os.path.join(target_dir, safe_name)
            
            if os.path.exists(new_path): os.remove(new_path)
            os.rename(final_path, new_path)
            
            print_success(f"Saved: {safe_name}")
            return True
        except Exception:
            # Fallback rename failed
            print_error(f"Saved as: {os.path.basename(final_path)}")
            return True
    else:
        print_error("Failed to download thumbnail.")
        return False
    
def download_audio_youtube(url, cut_range=None):
    """Main function to download YouTube audio"""

    # Download Preparation & Strict Checking
    if not is_valid_youtube_url(url):
        print_error(_('download.youtube.invalid_url'))
        wait_and_clear_prompt()
        return {'success': False, 'reason': 'invalid_url'}

    if RuntimeConfig.SIMPLE_MODE:
        target_dir = RuntimeConfig.MUSIC_ROOT
    else:
        target_dir = select_download_folder(RuntimeConfig.MUSIC_ROOT, "music")
        if not target_dir:
            return {'success': False, 'reason': 'cancel'}
    
    clear()
    header()
    
    def is_exists():
        is_playlist = "list=" in url
        if is_playlist: return False
        
        # print_process(_('download.youtube.checking_existing'))
        
        video_id = extract_video_id(url)
        exists, metadata = registry.check_existing(video_id, 'audio', target_dir)
        
        if exists:
            print_success(_('download.youtube.file_exists'))
            print_info(_('download.youtube.exists_title', title=metadata.get('title')))
            print_info(_('download.youtube.exists_path', path=metadata.get('file_path')))
            wait_and_clear_prompt()
            return {'success': True, 'file_path': metadata.get('file_path'), 'skipped': True}
        
        return False
    
    if RuntimeConfig.SKIP_EXISTING_FILES:
        existing_result = is_exists()
        if existing_result:
            return existing_result
    
    if not check_internet():
        print_error(_('download.youtube.no_internet'))
        wait_and_clear_prompt()
        return {'success': False, 'reason': 'no_internet'}
    
    # Start Downloading
    url_classification = classify_youtube_url(url)
    is_youtube_music = url_classification['platform'] == 'youtube_music'

    if is_youtube_music:
        print_info(_('download.youtube.yt_music_detected'))
    else:
        print_info(_('download.youtube.yt_audio_plain'))
        if RuntimeConfig.SMART_COVER_MODE:
            print_info(_('download.youtube.smart_cover_info'))

    if IS_TERMUX:
        remove_nomedia_file(target_dir)

    spinner = Spinner(_('download.youtube.extracting'))
    spinner.start()
    urls, content_title, total_items = extract_all_urls_from_content(url)
    spinner.stop(print_success(_('download.youtube.extracted', count=total_items, type='track'), str_only=True))

    if total_items > 1:
        if cut_range:
            print_info(color("Warning: '--cut' flag is ignored for playlists to prevent errors.", "y"))
            cut_range = None

        print_process(_('download.youtube.found_playlist', count=total_items, type='track', title=content_title))
        download_type = "Album" if url_classification['type'] == 'album' else "Playlist"

        success, skipped, failed = download_playlist_sequential(
            urls, target_dir, download_single_audio, "audio", is_youtube_music, content_title
        )
        return {'success': success > 0, 'is_playlist': True}
    else:
        if RuntimeConfig.SIMPLE_MODE:
            print_process(_('download.youtube.simple_mode_start', type='audio', path=target_dir))
        else:
            print_process(_('download.youtube.start_download', type='audio', path=target_dir))

        download_type = "Single Track"

        success, title, skipped = download_single_audio(
            urls[0],
            target_dir,
            is_youtube_music=is_youtube_music,
            download_type=download_type, 
            cut_range=cut_range
        )

        if success:
            from ..core.history import load_history

            load_history()
            if RuntimeConfig.DOWNLOAD_HISTORY:
                last_entry = RuntimeConfig.DOWNLOAD_HISTORY[-1]
                file_path_result = last_entry.get('file_path')
            if skipped:
                print_info(_('download.youtube.file_exists', title=title))
            else:
                if is_youtube_music:
                    print_success(_('download.youtube.complete_metadata', title=title))
                else:
                    print_success(_('download.youtube.complete', title=title))
        else:
            print_error(_('download.youtube.failed', title=title))
    wait_and_clear_prompt()
    return {
        'success': success,
        'file_path': file_path_result,
        'title': title if 'title' in locals() else None,
        'skipped': skipped if 'skipped' in locals() else False
    }


def download_video_youtube(url, cut_range=None):
    """Main function to download YouTube video"""

    # Download Preparation & Strict Checking
    if not is_valid_youtube_url(url):
        print_error(_('download.youtube.invalid_url'))
        wait_and_clear_prompt()
        return {'success': False, 'reason': 'invalid_url'}
    

    if RuntimeConfig.SIMPLE_MODE:
        target_dir = RuntimeConfig.VIDEO_ROOT
    else:
        target_dir = select_download_folder(RuntimeConfig.VIDEO_ROOT, "video")
        if not target_dir:
            return {'success': False, 'reason': 'cancel'}
        
    clear()
    header()
    
    def is_exists():
        is_playlist = "list=" in url
        if is_playlist: return False
        
        
        video_id = extract_video_id(url)
        exists, metadata = registry.check_existing(video_id, 'video', target_dir)
        
        if exists:
            print_success(_('download.youtube.file_exists'))
            print_info(_('download.youtube.exists_title', title=metadata.get('title')))
            print_info(_('download.youtube.exists_path', path=metadata.get('file_path')))
            return {'success': True, 'file_path': metadata.get('file_path'), 'skipped': True}
        
        return False
    

    if RuntimeConfig.SKIP_EXISTING_FILES:
        existing_result = is_exists()
        if existing_result:
            return existing_result
    
    if not check_internet():
        print_error(_('download.youtube.no_internet'))
        wait_and_clear_prompt()
        return {'success': False, 'reason': 'no_internet'}

    # Start Downloading
    if IS_TERMUX:
        remove_nomedia_file(target_dir)

    spinner = Spinner(_('download.youtube.extracting'))
    spinner.start()
    urls, content_title, total_items = extract_all_urls_from_content(url)
    spinner.stop(print_success(_('download.youtube.extracted', count=total_items, type='video'), str_only=True))

    if total_items > 1:
        if cut_range:
            print_info(color("Warning: '--cut' flag is ignored for playlists to prevent errors.", "y"))
            cut_range = None
        
        print_process(_('download.youtube.found_playlist', count=total_items, type='video', title=content_title))
        print_process(_('download.youtube.max_resolution', resolution=RuntimeConfig.MAX_VIDEO_RESOLUTION))
        
        success, skipped, failed = download_playlist_sequential(
            urls, target_dir, download_single_video, "video"
        )
        return {'success': success > 0, 'is_playlist': True}
    else:
        if RuntimeConfig.SIMPLE_MODE:
            print_process(_('download.youtube.simple_mode_start', type=f'video ({RuntimeConfig.MAX_VIDEO_RESOLUTION})', path=target_dir))
        else:
            print_process(_('download.youtube.start_download',
                            type=f'video ({RuntimeConfig.MAX_VIDEO_RESOLUTION})',
                            path=target_dir))

        download_type = "Single Video"

        success, title, skipped = download_single_video(
            urls[0],
            target_dir,
            download_type=download_type,
            cut_range=cut_range
        )

        if success:
            from ..core.history import load_history
            load_history()
            
            if RuntimeConfig.DOWNLOAD_HISTORY:
                last_entry = RuntimeConfig.DOWNLOAD_HISTORY[-1]
                file_path_result = last_entry.get('file_path')
            
            if skipped:
                print_info(_('download.youtube.file_exists', title=title))
            else:
                print_success(_('download.youtube.complete', title=title))
        else:
            print_error(_('download.youtube.failed', title=title))

    wait_and_clear_prompt()
    return {
        'success': success,
        'file_path': file_path_result,
        'title': title if 'title' in locals() else None,
        'skipped': skipped if 'skipped' in locals() else False
    }