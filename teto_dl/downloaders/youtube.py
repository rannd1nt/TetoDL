"""
YouTube video and audio downloader
"""
import os
import time

try:
    import yt_dlp as yt
except Exception:
    yt = None

from ..constants import FFMPEG_CMD, RuntimeConfig, DOWNLOAD_DELAY
from ..utils.i18n import get_text as _
from ..utils.colors import print_process, print_info, print_success, print_error
from ..utils.spinner import Spinner
from ..utils.network import (
    is_valid_youtube_url, is_youtube_music_url,
    classify_youtube_url, check_internet
)
from ..utils.file_utils import check_file_exists, create_nomedia_file, clean_temp_files
from ..core.history import add_to_history, truncate_title
from ..core.cache import get_cached_metadata, cache_metadata
from ..core.config import get_video_format_string
from ..media.scanner import scan_media_files
from ..media.thumbnail import download_and_process_thumbnail, embed_thumbnail_to_audio
from ..ui.navigation import select_download_folder


def get_audio_extension():
    """Get current audio extension from config"""
    return RuntimeConfig.AUDIO_QUALITY


def build_audio_postprocessors(audio_format, is_youtube_music=False):
    """Build postprocessors list based on audio format"""
    postprocessors = []
    
    if audio_format == "mp3":
        # MP3: Extract and convert to MP3
        postprocessors.append({
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        })
        if is_youtube_music:
            postprocessors.append({
                'key': 'FFmpegMetadata',
                'add_metadata': True,
            })
    
    elif audio_format == "opus":
        # OPUS: Extract and convert to OPUS for best quality
        postprocessors.append({
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'opus',
            'preferredquality': '160',
        })
        if is_youtube_music:
            postprocessors.append({
                'key': 'FFmpegMetadata',
                'add_metadata': True,
            })
    
    elif audio_format == "m4a" and is_youtube_music:
        postprocessors.append({
            'key': 'FFmpegMetadata',
            'add_metadata': True,
        })
    
    return postprocessors


def get_audio_format_string(audio_format):
    """Get format string for yt-dlp based on audio quality setting"""
    if audio_format == "m4a":
        # M4A: Get native m4a format directly
        return 'bestaudio[ext=m4a]/bestaudio'
    else:
        # MP3 and OPUS: Get best audio (usually webm/opus) then convert
        return 'bestaudio/best'


def download_single_video(url, target_dir, use_cache=True, download_type="Single Video"):
    """Download single video file with cache support"""
    try:
        with yt.YoutubeDL({'quiet': True, 'no_warnings': True, 'extract_flat': False}) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            
            print_process(_('download.youtube.checking_existing', title=truncate_title(title, max_chars=30)))
            
            if RuntimeConfig.SKIP_EXISTING_FILES:
                exists, existing_path = check_file_exists(title, target_dir, "video")
                if exists:
                    print_success(_('download.youtube.file_exists', title=truncate_title(title, max_chars=30)))
                    add_to_history(True, title, "video", "YouTube Video", download_type, duration)
                    return True, title, True

        outtmpl = os.path.join(target_dir, "%(title)s.%(ext)s")
        video_format = get_video_format_string()
        
        ydl_opts = {
            'format': video_format,
            'merge_output_format': 'mp4',
            'outtmpl': outtmpl,
            'ffmpeg_location': FFMPEG_CMD,
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            
            if use_cache:
                cached = get_cached_metadata(url)
                if cached:
                    print_info(_('download.youtube.using_cache', title=cached['metadata'].get('title', 'Unknown')))
            
            print_process(_('download.youtube.downloading_item', title=title))
            ydl.download([url])
            
            if use_cache:
                cache_metadata(url, {
                    'title': title,
                    'duration': duration,
                    'uploader': info.get('uploader', '')
                })
            
            add_to_history(True, title, "video", "YouTube Video", download_type, duration)
            
        return True, title, False
        
    except Exception as e:
        print_error(_('download.youtube.error_downloading', type='video', error=str(e)))
        add_to_history(False, f"Error: {str(e)}", "video", "YouTube Video", download_type, 0)
        return False, str(e), False


def download_single_audio(url, target_dir, use_cache=True, is_youtube_music=False, download_type="Single Track"):
    """Download single audio file with cache support and metadata for YouTube Music"""
    audio_format = get_audio_extension()
    
    try:
        with yt.YoutubeDL({'quiet': True, 'no_warnings': True, 'extract_flat': False}) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            
            if RuntimeConfig.SKIP_EXISTING_FILES:
                print_process(_('download.youtube.checking_existing', title=truncate_title(title, max_chars=30)))
                exists, existing_path = check_file_exists(title, target_dir, "audio", audio_format)
                if exists:
                    print_success(_('download.youtube.file_exists', title=truncate_title(title, max_chars=30)))
                    platform = "YouTube Music" if is_youtube_music else "YouTube Audio"
                    add_to_history(True, title, "audio", platform, download_type, duration)
                    return True, title, True

        # Build output template based on format
        if is_youtube_music:
            outtmpl = os.path.join(target_dir, f"%(artist)s - %(title)s.%(ext)s")
        else:
            outtmpl = os.path.join(target_dir, f"%(title)s.%(ext)s")
        
        format_string = get_audio_format_string(audio_format)
        postprocessors = build_audio_postprocessors(audio_format, is_youtube_music)
        
        ydl_opts = {
            'format': format_string,
            'outtmpl': outtmpl,
            'postprocessors': postprocessors,
            'ffmpeg_location': FFMPEG_CMD,
            'quiet': True,
            'no_warnings': True,
            'writethumbnail': False,
        }
        
        with yt.YoutubeDL(ydl_opts) as ydl:
            if use_cache:
                cached = get_cached_metadata(url)
                if cached:
                    print_info(_('download.youtube.using_cache', title=cached['metadata'].get('title', 'Unknown')))
            
            print_process(_('download.youtube.downloading_item', title=title))
            ydl.download([url])
            
            # Process cover art for YouTube Music
            if is_youtube_music and audio_format != "opus":
                print_process(_('download.youtube.processing_cover'))
                thumbnail_path = download_and_process_thumbnail(info, target_dir)
                
                if thumbnail_path and os.path.exists(thumbnail_path):
                    artist = info.get('artist', 'Unknown').replace('/', '&')
                    title_clean = title.replace('/', '&')
                    audio_filename = f"{artist} - {title_clean}.{audio_format}"
                    audio_path = os.path.join(target_dir, audio_filename)
                                        
                    if os.path.exists(audio_path):
                        print_process(_('download.youtube.embedding_cover'))
                        if embed_thumbnail_to_audio(audio_path, thumbnail_path, audio_format):
                            print_success(_('download.youtube.cover_success'))
                        else:
                            print_error(_('download.youtube.cover_failed'))
                    else:
                        print_error(_('download.youtube.file_not_found', filename=audio_filename))
                       
                    clean_temp_files(target_dir, info.get('id', ''))
                else:
                    print_error(_('download.youtube.cover_process_failed'))
                    
            elif is_youtube_music and audio_format == "opus":
                print_info(_('download.youtube.skip_cover_opus'))
            else:
                print_info(_('download.youtube.skip_cover'))
            
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
            add_to_history(True, title, "audio", platform, download_type, duration)
            
            return True, title, False
            
    except Exception as e:
        print_error(_('download.youtube.error_downloading', type='audio', error=str(e)))
        platform = "YouTube Music" if is_youtube_music else "YouTube Audio"
        add_to_history(False, f"Error: {str(e)}", "audio", platform, download_type, 0)
        return False, str(e), False


def download_playlist_sequential(urls, target_dir, download_func, content_type="audio", is_youtube_music=False, content_title="Playlist"):
    """Download multiple URLs sequentially"""
    total = len(urls)
    success_count = 0
    failed_count = 0
    skipped_count = 0
    failed_urls = []
    
    print_process(_('download.youtube.simple_mode_start', type=f'{total} {content_type}'))
    
    for i, url in enumerate(urls, 1):
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
            print_process(_('download.youtube.wait_delay', delay=DOWNLOAD_DELAY))
            time.sleep(DOWNLOAD_DELAY)
    
    print_success(_('download.youtube.summary', 
                    success=success_count, 
                    skipped=skipped_count, 
                    failed=failed_count, 
                    total=total, 
                    type=content_type))
    
    if failed_urls:
        print_info(_('download.youtube.failed_items', count=len(failed_urls), type=content_type))
    
    return success_count, skipped_count, failed_count


def extract_all_urls_from_content(url):
    """Extract all URLs from various YouTube/YouTube Music content types"""
    is_yt_music = is_youtube_music_url(url)
    ydl_opts = {'extract_flat': True, 'quiet': True, 'no_warnings': True}
    
    try:
        with yt.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if 'entries' in info:
                urls = []
                for entry in info['entries']:
                    if entry and entry.get('url'):
                        urls.append(entry['url'])
                    elif entry and entry.get('webpage_url'):
                        webpage_url = entry['webpage_url']
                        if is_yt_music and 'music.youtube.com' not in webpage_url:
                            video_id = entry.get('id')
                            if video_id:
                                webpage_url = f"https://music.youtube.com/watch?v={video_id}"
                        urls.append(webpage_url)
                    elif entry and entry.get('id'):
                        video_id = entry['id']
                        if is_yt_music:
                            video_url = f"https://music.youtube.com/watch?v={video_id}"
                        else:
                            video_url = f"https://www.youtube.com/watch?v={video_id}"
                        urls.append(video_url)
                
                title = info.get('title', 'Unknown Playlist/Album')
                return urls, title, len(urls)
            else:
                url_to_download = info.get('webpage_url') or info.get('url') or url
                
                if is_yt_music and 'music.youtube.com' not in url_to_download:
                    video_id = info.get('id')
                    if video_id:
                        url_to_download = f"https://music.youtube.com/watch?v={video_id}"
                
                title = info.get('title', 'Single Track/Video')
                return [url_to_download], title, 1
                
    except Exception as e:
        print_error(_('download.youtube.extract_failed', error=str(e)))
        return [url], 'Unknown', 1


def get_content_type_display(url_classification):
    """Get display string for content type"""
    platform = url_classification['platform']
    content_type = url_classification['type']
    
    platform_names = {'youtube': 'YouTube', 'youtube_music': 'YouTube Music'}
    type_names = {'video': 'Video', 'playlist': 'Playlist', 'album': 'Album'}
    
    platform_str = platform_names.get(platform, platform)
    type_str = type_names.get(content_type, content_type)
    
    return f"{platform_str} {type_str}"


def download_audio_youtube(url):
    """Main function to download YouTube audio"""
    if not is_valid_youtube_url(url):
        print_error(_('download.youtube.invalid_url'))
        return
    
    url_classification = classify_youtube_url(url)
    content_display = get_content_type_display(url_classification)
    is_youtube_music = url_classification['platform'] == 'youtube_music'

    if not is_youtube_music:
        if not check_internet():
            print_error(_('download.youtube.no_internet'))
            return

    if RuntimeConfig.SIMPLE_MODE:
        print_process(_('download.youtube.simple_mode_start', type='audio'))
        target_dir = RuntimeConfig.MUSIC_ROOT
    else:
        target_dir = select_download_folder(RuntimeConfig.MUSIC_ROOT, "music")
        if not target_dir:
            print_info(_('download.youtube.cancelled'))
            return

    print_process(_('download.youtube.detected', type=content_display))
    
    if is_youtube_music:
        print_process(_('download.youtube.yt_music_detected'))
        print_process(_('download.youtube.thumbnail_crop'))
    else:
        print_process(_('download.youtube.yt_audio_plain'))

    create_nomedia_file(target_dir)

    spinner = Spinner(_('download.youtube.extracting'))
    spinner.start()
    urls, content_title, total_items = extract_all_urls_from_content(url)
    spinner.stop(_('download.youtube.extracted', count=total_items, type='track'))
    
    if total_items > 1:
        print_process(_('download.youtube.found_playlist', count=total_items, type='track', title=content_title))
        download_type = "Album" if url_classification['type'] == 'album' else "Playlist"
                
        success, skipped, failed = download_playlist_sequential(
            urls, target_dir, download_single_audio, "audio", is_youtube_music, content_title
        )
    else:
        if RuntimeConfig.SIMPLE_MODE:
            print_process(_('download.youtube.simple_mode_start', type='audio'))
        else:
            print_process(_('download.youtube.start_download', type='audio', path=target_dir))
        
        download_type = "Single Track"
                
        success, title, skipped = download_single_audio(urls[0], target_dir, is_youtube_music=is_youtube_music, download_type=download_type)
        if success:
            if skipped:
                print_info(_('download.youtube.file_exists', title=title))
            else:
                if is_youtube_music:
                    print_success(_('download.youtube.complete_metadata', title=title))
                else:
                    print_success(_('download.youtube.complete', title=title))
        else:
            print_error(_('download.youtube.failed', title=title))
    
    scan_media_files(target_dir)


def download_video_youtube(url):
    """Main function to download YouTube video"""
    if not is_valid_youtube_url(url):
        print_error(_('download.youtube.invalid_url'))
        return
    if not check_internet():
        print_error(_('download.youtube.no_internet'))
        return

    url_classification = classify_youtube_url(url)
    content_display = get_content_type_display(url_classification)
    print_process(_('download.youtube.detected', type=content_display))

    if RuntimeConfig.SIMPLE_MODE:
        print_process(_('download.youtube.simple_mode_start', type='video'))
        target_dir = RuntimeConfig.VIDEO_ROOT
    else:
        target_dir = select_download_folder(RuntimeConfig.VIDEO_ROOT, "video")
        if not target_dir:
            print_info(_('download.youtube.cancelled'))
            return

    create_nomedia_file(target_dir)

    spinner = Spinner(_('download.youtube.extracting'))
    spinner.start()
    urls, content_title, total_items = extract_all_urls_from_content(url)
    spinner.stop(_('download.youtube.extracted', count=total_items, type='video'))
    
    if total_items > 1:
        print_process(_('download.youtube.found_playlist', count=total_items, type='video', title=content_title))
    
    print_process(_('download.youtube.max_resolution', resolution=RuntimeConfig.MAX_VIDEO_RESOLUTION))
    
    if total_items > 1:
        success, skipped, failed = download_playlist_sequential(
            urls, target_dir, download_single_video, "video"
        )
    else:
        if RuntimeConfig.SIMPLE_MODE:
            print_process(_('download.youtube.simple_mode_start', type='video'))
        else:
            print_process(_('download.youtube.start_download', 
                          type=f'video ({RuntimeConfig.MAX_VIDEO_RESOLUTION})', 
                          path=target_dir))
        
        success, title, skipped = download_single_video(urls[0], target_dir, download_type="Single Video")
        if success:
            if skipped:
                print_info(_('download.youtube.file_exists', title=title))
            else:
                print_success(_('download.youtube.complete', title=title))
        else:
            print_error(_('download.youtube.failed', title=title))
    
    scan_media_files(target_dir)