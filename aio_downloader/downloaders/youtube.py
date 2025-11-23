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
from ..media.thumbnail import download_and_process_thumbnail, embed_thumbnail_to_mp3
from ..ui.navigation import select_download_folder


def download_single_video(url, target_dir, use_cache=True, download_type="Single Video"):
    """Download single video file with cache support"""
    try:
        with yt.YoutubeDL({'quiet': True, 'no_warnings': True, 'extract_flat': False}) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            
            print_process(f"Memeriksa file existing: {title}")
            
            if RuntimeConfig.SKIP_EXISTING_FILES:
                exists, existing_path = check_file_exists(title, target_dir, "video")
                if exists:
                    print_success(f"File sudah ada, skip: {truncate_title(title, max_chars=30)}")
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
                    print_info(f"Menggunakan cache untuk: {cached['metadata'].get('title', 'Unknown')}")
            
            print_process(f"Mendownload: {title}")
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
        print_error(f"Error downloading video: {str(e)}")
        add_to_history(False, f"Error: {str(e)}", "video", "YouTube Video", download_type, 0)
        return False, str(e), False


def download_single_audio(url, target_dir, use_cache=True, is_youtube_music=False, download_type="Single Track"):
    """Download single audio file with cache support and metadata for YouTube Music"""
    try:
        with yt.YoutubeDL({'quiet': True, 'no_warnings': True, 'extract_flat': False}) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            
            if RuntimeConfig.SKIP_EXISTING_FILES:
                print_process(f"Memeriksa file existing: {truncate_title(title, max_chars=30)}")
                exists, existing_path = check_file_exists(title, target_dir, "audio")
                if exists:
                    print_success(f"File sudah ada, skip: {truncate_title(title, max_chars=30)}")
                    platform = "YouTube Music" if is_youtube_music else "YouTube Audio"
                    add_to_history(True, title, "audio", platform, download_type, duration)
                    return True, title, True

        outtmpl = os.path.join(target_dir, "%(artist)s - %(title)s.%(ext)s")
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': outtmpl,
            'postprocessors': [],
            'ffmpeg_location': FFMPEG_CMD,
            'quiet': True,
            'no_warnings': True,
            'writethumbnail': False,
        }
        
        ydl_opts['postprocessors'].append({
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        })
        
        if is_youtube_music:
            ydl_opts['postprocessors'].append({
                'key': 'FFmpegMetadata',
                'add_metadata': True,
            })
        
        with yt.YoutubeDL(ydl_opts) as ydl:
            if use_cache:
                cached = get_cached_metadata(url)
                if cached:
                    print_info(f"Menggunakan cache untuk: {cached['metadata'].get('title', 'Unknown')}")
            
            print_process(f"Mendownload: {title}")
            ydl.download([url])
            
            if is_youtube_music:
                print_process("Memproses cover art...")
                thumbnail_path = download_and_process_thumbnail(info, target_dir)
                
                if thumbnail_path and os.path.exists(thumbnail_path):
                    artist = info.get('artist', 'Unknown').replace('/', '&')
                    title_clean = title.replace('/', '&')
                    mp3_filename = f"{artist} - {title_clean}.mp3"
                    mp3_path = os.path.join(target_dir, mp3_filename)
                                        
                    if os.path.exists(mp3_path):
                        print_process("Mengembed cover art...")
                        if embed_thumbnail_to_mp3(mp3_path, thumbnail_path):
                            print_success("Cover art berhasil diembed")
                        else:
                            print_error("Gagal mengembed cover art ke MP3")
                    else:
                        print_error(f"File MP3 tidak ditemukan: {mp3_filename}")
                       
                    clean_temp_files(target_dir, info.get('id', ''))
                else:
                    print_error("Gagal memproses cover art")
            else:
                print_info("Skipping cover art processing")
            
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
        print_error(f"Error downloading audio: {str(e)}")
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
    
    print_process(f"Memulai download {total} {content_type} (sequential)...")
    
    for i, url in enumerate(urls, 1):
        print_process(f"Progress: {i}/{total}")
        
        try:
            print_info(f"Downloading URL: {url} as {content_type}.")
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
                    print_info(f"Skipped (sudah ada): {result}")
                    skipped_count += 1
                else:
                    print_success(f"Berhasil: {result}")
                    success_count += 1
            else:
                print_error(f"Gagal: {result}")
                failed_count += 1
                failed_urls.append(url)
        except Exception as e:
            print_error(f"Error: {str(e)}")
            failed_count += 1
            failed_urls.append(url)
        
        if i < total:
            print_process(f"Menunggu {DOWNLOAD_DELAY} detik sebelum download berikutnya...")
            time.sleep(DOWNLOAD_DELAY)
    
    print_success(f"Ringkasan: {success_count} berhasil, {skipped_count} skipped, {failed_count} gagal dari total {total} {content_type}")
    
    if failed_urls:
        print_info(f"{len(failed_urls)} {content_type} gagal didownload")
    
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
        print_error(f"Gagal extract konten: {e}")
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
        print_error("URL YouTube/YouTube Music tidak valid.")
        return
    
    url_classification = classify_youtube_url(url)
    content_display = get_content_type_display(url_classification)
    is_youtube_music = url_classification['platform'] == 'youtube_music'

    if not is_youtube_music:
        if not check_internet():
            print_error("Tidak ada koneksi internet.")
            return

    if RuntimeConfig.SIMPLE_MODE:
        print_process(f"Simple Mode: Download langsung ke {RuntimeConfig.MUSIC_ROOT}")
        target_dir = RuntimeConfig.MUSIC_ROOT
    else:
        target_dir = select_download_folder(RuntimeConfig.MUSIC_ROOT, "music")
        if not target_dir:
            print_info("Dibatalkan.")
            return

    print_process(f"{content_display} terdeteksi")
    
    if is_youtube_music:
        print_process("YouTube Music terdeteksi - Mengunduh dengan metadata dan cover art...")
        print_process("Thumbnail akan di-crop ke square ratio 1:1...")
    else:
        print_process("YouTube Audio biasa - Tidak ada metadata dan cover art")

    create_nomedia_file(target_dir)

    spinner = Spinner("Mengekstrak konten playlist...")
    spinner.start()
    urls, content_title, total_items = extract_all_urls_from_content(url)
    spinner.stop(f"Berhasil mengekstrak {total_items} track")
    
    if total_items > 1:
        print_process(f"Ditemukan {total_items} track dalam playlist/album: {content_title}")
        download_type = "Album" if url_classification['type'] == 'album' else "Playlist"
                
        success, skipped, failed = download_playlist_sequential(
            urls, target_dir, download_single_audio, "audio", is_youtube_music, content_title
        )
    else:
        if RuntimeConfig.SIMPLE_MODE:
            print_process("Simple Mode: Memulai download audio...")
        else:
            print_process(f"Mulai download audio → {target_dir}")
        
        download_type = "Single Track"
                
        success, title, skipped = download_single_audio(urls[0], target_dir, is_youtube_music=is_youtube_music, download_type=download_type)
        if success:
            if skipped:
                print_info(f"File sudah ada, skip: {title}")
            else:
                if is_youtube_music:
                    print_success(f"Download berhasil dengan metadata: {title}")
                else:
                    print_success(f"Download berhasil: {title}")
        else:
            print_error(f"Download gagal: {title}")
    
    scan_media_files(target_dir)


def download_video_youtube(url):
    """Main function to download YouTube video"""
    if not is_valid_youtube_url(url):
        print_error("URL tidak valid.")
        return
    if not check_internet():
        print_error("Tidak ada koneksi internet.")
        return

    url_classification = classify_youtube_url(url)
    content_display = get_content_type_display(url_classification)
    print_process(f"{content_display} URL terdeteksi")

    if RuntimeConfig.SIMPLE_MODE:
        print_process(f"Simple Mode: Download langsung ke {RuntimeConfig.VIDEO_ROOT}")
        target_dir = RuntimeConfig.VIDEO_ROOT
    else:
        target_dir = select_download_folder(RuntimeConfig.VIDEO_ROOT, "video")
        if not target_dir:
            print_info("Dibatalkan.")
            return

    create_nomedia_file(target_dir)

    spinner = Spinner("Mengekstrak konten playlist...")
    spinner.start()
    urls, content_title, total_items = extract_all_urls_from_content(url)
    spinner.stop(f"Berhasil mengekstrak {total_items} video")
    
    if total_items > 1:
        print_process(f"Ditemukan {total_items} video dalam playlist: {content_title}")
    
    print_process(f"Max video resolution: {RuntimeConfig.MAX_VIDEO_RESOLUTION}")
    
    if total_items > 1:
        success, skipped, failed = download_playlist_sequential(
            urls, target_dir, download_single_video, "video"
        )
    else:
        if RuntimeConfig.SIMPLE_MODE:
            print_process("Simple Mode: Memulai download video...")
        else:
            print_process(f"Mulai download video ({RuntimeConfig.MAX_VIDEO_RESOLUTION}) → {target_dir}")
        
        success, title, skipped = download_single_video(urls[0], target_dir, download_type="Single Video")
        if success:
            if skipped:
                print_info(f"File sudah ada, skip: {title}")
            else:
                print_success(f"Download berhasil: {title}")
        else:
            print_error(f"Download gagal: {title}")
    
    scan_media_files(target_dir)