"""
Main entry points (handlers) for YouTube download operations
"""
import os
import shutil
from yt_dlp.utils import sanitize_filename

from ...constants import RuntimeConfig, IS_TERMUX
from ...utils.i18n import get_text as _
from ...utils.styles import print_process, print_info, print_success, print_error, clear, color
from ...utils.spinner import Spinner
from ...utils.network import is_valid_youtube_url, classify_youtube_url, check_internet
from ...utils.files import remove_nomedia_file, create_zip_archive
from ...utils.processing import extract_all_urls_from_content, extract_video_id
from ...core.registry import registry
from ...core.config import save_config
from ...ui.components import header
from ...ui.navigation import select_download_folder
from ...utils.display import wait_and_clear_prompt

from .audio import download_single_audio
from .video import download_single_video
from .playlist import download_playlist_sequential

def get_content_type_display(url_classification):
    """Get display string for content type"""
    platform = url_classification['platform']
    content_type = url_classification['type']
    platform_names = {'youtube': 'YouTube', 'youtube_music': 'YouTube Music'}
    type_names = {'video': 'Video', 'playlist': 'Playlist', 'album': 'Album'}
    platform_str = platform_names.get(platform, platform)
    type_str = type_names.get(content_type, content_type)
    return f"{platform_str} {type_str}"

def download_audio_youtube(url, cut_range=None, playlist_items=None, group_folder=False, share_mode=False):
    """Main function to download YouTube audio"""

    # 1. Validasi Awal
    if not is_valid_youtube_url(url):
        print_error(_('download.youtube.invalid_url'))
        wait_and_clear_prompt()
        return {'success': False, 'reason': 'invalid_url'}

    if RuntimeConfig.SIMPLE_MODE:
        target_dir = RuntimeConfig.MUSIC_ROOT
    else:
        target_dir = select_download_folder(RuntimeConfig.MUSIC_ROOT, "music")
        if not target_dir: return {'success': False, 'reason': 'cancel'}
    
    clear(); header()
    
    # 2. Cek Existing (Single File Only, Playlist di-skip disini)
    def is_exists():
        is_playlist = "list=" in url
        if is_playlist: return False
        
        video_id = extract_video_id(url)
        # Registry Check disini pakai target_dir root, aman untuk single
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
        if existing_result: return existing_result
    
    if not check_internet():
        print_error(_('download.youtube.no_internet'))
        wait_and_clear_prompt()
        return {'success': False, 'reason': 'no_internet'}
    
    # 3. Klasifikasi & Info
    url_classification = classify_youtube_url(url)
    is_youtube_music = url_classification['platform'] == 'youtube_music'

    if is_youtube_music: print_info(_('download.youtube.yt_music_detected'))
    else:
        print_info(_('download.youtube.yt_audio_plain'))
        if RuntimeConfig.SMART_COVER_MODE: print_info(_('download.youtube.smart_cover_info'))

    if IS_TERMUX: remove_nomedia_file(target_dir)

    # 4. Extract Info Playlist
    spinner = Spinner(_('download.youtube.extracting'))
    spinner.start()
    urls, content_title, total_items = extract_all_urls_from_content(url)
    spinner.stop(print_success(_('download.youtube.extracted', count=total_items, type='track'), str_only=True))

    if total_items > 1:
        # --- PLAYLIST LOGIC ---
        if cut_range:
            print_info(color("Warning: '--cut' flag is ignored for playlists.", "y"))
            cut_range = None

        print_process(_('download.youtube.found_playlist', count=total_items, type='track', title=content_title))

        # [FIX CRITICAL] Penentuan Folder & Nama M3U
        safe_original_title = sanitize_filename(content_title)
        
        custom_group_name = None
        m3u_playlist_name = content_title # Default: Fresh Ambience
        
        # Cek apakah group_folder berupa String ("Test") atau Bool (True)
        if isinstance(group_folder, str):
            custom_group_name = sanitize_filename(group_folder)
            m3u_playlist_name = group_folder # M3U Name jadi "Test"
        elif group_folder: 
            custom_group_name = safe_original_title
            m3u_playlist_name = content_title # M3U Name tetap "Fresh Ambience"

        final_download_dir = target_dir
        parent_dir_if_staging = None
        alt_check_dirs = []
        is_staging = False
        
        # A. Grouping Mode
        if custom_group_name:
            final_download_dir = os.path.join(target_dir, custom_group_name)
            is_staging = False 
            
            try:
                root_key = os.path.abspath(target_dir)
                folder_name_only = custom_group_name
                
                if root_key not in RuntimeConfig.USER_SUBFOLDERS:
                    RuntimeConfig.USER_SUBFOLDERS[root_key] = []
                
                if folder_name_only not in RuntimeConfig.USER_SUBFOLDERS[root_key]:
                    RuntimeConfig.USER_SUBFOLDERS[root_key].append(folder_name_only)
                    save_config()
            except Exception: pass 
            
        # B. Share Mode (Tanpa Grouping) -> Staging
        elif share_mode:
            is_staging = True
            parent_dir_if_staging = target_dir
            potential_original_path = os.path.join(target_dir, safe_original_title)
            
            if os.path.exists(potential_original_path):
                final_download_dir = os.path.join(target_dir, f"{safe_original_title} (Share)")
                alt_check_dirs.append(potential_original_path)
            else:
                final_download_dir = potential_original_path
            
            alt_check_dirs.append(target_dir)

        # C. Default (Flat)
        else:
            is_staging = False
            final_download_dir = target_dir

        if final_download_dir != target_dir and not os.path.exists(final_download_dir):
            os.makedirs(final_download_dir, exist_ok=True)
        
        success, skipped, failed = download_playlist_sequential(
            urls,
            final_download_dir, 
            download_single_audio,
            "audio",
            is_youtube_music,
            m3u_playlist_name,
            playlist_items,
            alt_check_dirs
        )

        if is_staging and success == 0:
            if os.path.exists(final_download_dir) and not os.listdir(final_download_dir):
                print_info("All items exist in library. Staging folder is empty. Nothing to share.")
                try:
                    shutil.rmtree(final_download_dir)
                except Exception: pass
                
                return {
                    'success': False,
                    'is_playlist': True,
                    'file_path': None,
                    'is_staging': False,
                    'parent_dir': None,
                    'skipped': skipped,
                    'suppress_error': True
                }
            
        final_path_result = final_download_dir

        if RuntimeConfig.ZIP_MODE:
            zip_path = create_zip_archive(final_download_dir)
            if zip_path:
                final_path_result = zip_path
                if is_staging or (share_mode and not group_folder):
                    try:
                        shutil.rmtree(final_download_dir)
                        is_staging = False; parent_dir_if_staging = None 
                    except Exception: pass
                    
        return {
            'success': success > 0,
            'is_playlist': True,
            'file_path': final_path_result,
            'is_staging': is_staging,
            'parent_dir': parent_dir_if_staging,
            'skipped': skipped
        }
    
    else:
        # --- SINGLE TRACK LOGIC ---
        if RuntimeConfig.SIMPLE_MODE:
            print_process(_('download.youtube.simple_mode_start', type='audio', path=target_dir))
        else:
            print_process(_('download.youtube.start_download', type='audio', path=target_dir))

        download_type = "Single Track"
        success, title, skipped = download_single_audio(
            urls[0], target_dir, is_youtube_music=is_youtube_music,
            download_type=download_type, cut_range=cut_range
        )

        file_path_result = None
        if success:
            from ...core.history import load_history
            load_history()
            if RuntimeConfig.DOWNLOAD_HISTORY:
                file_path_result = RuntimeConfig.DOWNLOAD_HISTORY[-1].get('file_path')
            
            if skipped: print_info(_('download.youtube.file_exists', title=title))
            else:
                if is_youtube_music: print_success(_('download.youtube.complete_metadata', title=title))
                else: print_success(_('download.youtube.complete', title=title))
        else:
            print_error(_('download.youtube.failed', title=title))
            
    wait_and_clear_prompt()
    return {
        'success': success,
        'file_path': file_path_result,
        'title': title if 'title' in locals() else None,
        'skipped': skipped if 'skipped' in locals() else False
    }

def download_video_youtube(url, cut_range=None, playlist_items=None, group_folder=False, share_mode=False):
    """Main function to download YouTube video"""

    # 1. Validasi Awal
    if not is_valid_youtube_url(url):
        print_error(_('download.youtube.invalid_url'))
        wait_and_clear_prompt()
        return {'success': False, 'reason': 'invalid_url'}

    if RuntimeConfig.SIMPLE_MODE: target_dir = RuntimeConfig.VIDEO_ROOT
    else:
        target_dir = select_download_folder(RuntimeConfig.VIDEO_ROOT, "video")
        if not target_dir: return {'success': False, 'reason': 'cancel'}
        
    clear(); header()
    
    # 2. Cek Existing (Single)
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
        if existing_result: return existing_result
    
    if not check_internet():
        print_error(_('download.youtube.no_internet'))
        wait_and_clear_prompt()
        return {'success': False, 'reason': 'no_internet'}

    # 3. Klasifikasi
    if IS_TERMUX: remove_nomedia_file(target_dir)

    spinner = Spinner(_('download.youtube.extracting'))
    spinner.start()
    urls, content_title, total_items = extract_all_urls_from_content(url)
    spinner.stop(print_success(_('download.youtube.extracted', count=total_items, type='video'), str_only=True))

    if total_items > 1:
        # --- PLAYLIST VIDEO ---
        if cut_range:
            print_info(color("Warning: '--cut' flag is ignored for playlists.", "y"))
            cut_range = None
        
        print_process(_('download.youtube.found_playlist', count=total_items, type='video', title=content_title))
        print_process(_('download.youtube.max_resolution', resolution=RuntimeConfig.MAX_VIDEO_RESOLUTION))
        
        safe_original_title = sanitize_filename(content_title)
        custom_group_name = None
        m3u_playlist_name = content_title
        
        # Handle String vs Bool Group
        if isinstance(group_folder, str):
            custom_group_name = sanitize_filename(group_folder)
            m3u_playlist_name = group_folder
        elif group_folder:
            custom_group_name = safe_original_title
            m3u_playlist_name = content_title

        final_download_dir = target_dir
        parent_dir_if_staging = None
        alt_check_dirs = []
        is_staging = False
        
        # Grouping Mode
        if custom_group_name:
            final_download_dir = os.path.join(target_dir, custom_group_name)
            is_staging = False
            
            try:
                root_key = os.path.abspath(target_dir)
                folder_name_only = custom_group_name
                if root_key not in RuntimeConfig.USER_SUBFOLDERS:
                    RuntimeConfig.USER_SUBFOLDERS[root_key] = []
                if folder_name_only not in RuntimeConfig.USER_SUBFOLDERS[root_key]:
                    RuntimeConfig.USER_SUBFOLDERS[root_key].append(folder_name_only)
                    save_config()
            except Exception: pass

        # Share Mode (Without Grouping) -> Staging
        elif share_mode:
            is_staging = True
            parent_dir_if_staging = target_dir
            potential_original_path = os.path.join(target_dir, safe_original_title)
            if os.path.exists(potential_original_path):
                final_download_dir = os.path.join(target_dir, f"{safe_original_title} (Share)")
                alt_check_dirs.append(potential_original_path)
            else:
                final_download_dir = potential_original_path
            alt_check_dirs.append(target_dir)
        
        # Default (Flat)
        else:
            is_staging = False
            final_download_dir = target_dir

        if final_download_dir != target_dir and not os.path.exists(final_download_dir):
            os.makedirs(final_download_dir, exist_ok=True)
        
        success, skipped, failed = download_playlist_sequential(
            urls,
            final_download_dir,
            download_single_video,
            "video",
            False,
            m3u_playlist_name,
            playlist_items,
            alt_check_dirs
        )

        if is_staging and success == 0:
            if os.path.exists(final_download_dir) and not os.listdir(final_download_dir):
                print_info("All items exist in library. Staging folder is empty. Nothing to share.")
                try:
                    shutil.rmtree(final_download_dir)
                except Exception: pass
                
                return {
                    'success': False,
                    'is_playlist': True,
                    'file_path': None,
                    'is_staging': False,
                    'parent_dir': None,
                    'skipped': skipped,
                    'suppress_error': True
                }
        
        final_path_result = final_download_dir
        
        if RuntimeConfig.ZIP_MODE:
            zip_path = create_zip_archive(final_download_dir)
            if zip_path:
                final_path_result = zip_path
                if is_staging or (share_mode and not group_folder):
                    try:
                        shutil.rmtree(final_download_dir)
                        is_staging = False; parent_dir_if_staging = None 
                    except Exception: pass

        return {
            'success': success > 0,
            'is_playlist': True,
            'file_path': final_path_result,
            'is_staging': is_staging,
            'parent_dir': parent_dir_if_staging,
            'skipped': skipped
        }

    else:
        # --- SINGLE VIDEO ---
        if RuntimeConfig.SIMPLE_MODE:
            print_process(_('download.youtube.simple_mode_start', type=f'video ({RuntimeConfig.MAX_VIDEO_RESOLUTION})', path=target_dir))
        else:
            print_process(_('download.youtube.start_download',
                            type=f'video ({RuntimeConfig.MAX_VIDEO_RESOLUTION})', path=target_dir))

        download_type = "Single Video"
        success, title, skipped = download_single_video(
            urls[0], target_dir, download_type=download_type, cut_range=cut_range
        )

        file_path_result = None
        if success:
            from ...core.history import load_history
            load_history()
            if RuntimeConfig.DOWNLOAD_HISTORY:
                file_path_result = RuntimeConfig.DOWNLOAD_HISTORY[-1].get('file_path')
            
            if skipped: print_info(_('download.youtube.file_exists', title=title))
            else: print_success(_('download.youtube.complete', title=title))
        else:
            print_error(_('download.youtube.failed', title=title))

    wait_and_clear_prompt()
    return {
        'success': success, 'file_path': file_path_result,
        'title': title if 'title' in locals() else None,
        'skipped': skipped if 'skipped' in locals() else False
    }