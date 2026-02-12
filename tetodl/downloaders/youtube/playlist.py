"""
Playlist iteration logic
"""
import os
import time
from ...utils.i18n import get_text as _
from ...utils.styles import print_process, print_info, print_success, print_error, color
from ...utils.processing import extract_video_id
from ...utils.files import create_m3u8_playlist
from ...core.registry import registry
from ...constants import RuntimeConfig

def download_playlist_sequential(
        urls, target_dir, download_func, content_type="audio",
        is_youtube_music=False, content_title="Playlist", allowed_indices=None,
        alt_check_dirs=None
    ):
    """Download multiple URLs sequentially"""

    total = len(urls)
    success_count = 0
    failed_count = 0
    skipped_count = 0
    failed_urls = []
    ordered_files = []

    dirs_to_check = [target_dir]
    if alt_check_dirs:
        dirs_to_check.extend(alt_check_dirs)
    
    for i, url in enumerate(urls, 1):
        if allowed_indices is not None:
            if i not in allowed_indices:
                print_info(f"Skipping item {i} (Not selected)")
                continue
        
        video_id = extract_video_id(url)
        
        found_existing = False
        
        if video_id:
            for check_dir in dirs_to_check:
                exists, metadata = registry.check_existing(video_id, content_type, check_dir)
                if exists:
                    print_process(_('download.youtube.progress', current=i, total=total))
                    print_info(_('download.youtube.file_exists_playlist', title=metadata.get('title', video_id)))
                    found_existing = True
                    if metadata.get('file_path'):
                        ordered_files.append(os.path.basename(metadata.get('file_path')))
                    break
        
        if found_existing:
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
                from ...core.history import load_history
                load_history()
                if RuntimeConfig.DOWNLOAD_HISTORY:
                    last_entry = RuntimeConfig.DOWNLOAD_HISTORY[-1]
                    if last_entry.get('id') == video_id or video_id is None:
                        fpath = last_entry.get('file_path')
                        if fpath:
                            ordered_files.append(os.path.basename(fpath))
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

    if RuntimeConfig.CREATE_M3U and ordered_files:
        create_m3u8_playlist(target_dir, content_title, ordered_files)
        
    print_success(_('download.youtube.summary',
                    success=success_count,
                    skipped=skipped_count,
                    failed=failed_count,
                    total=total,
                    type=content_type))

    return success_count, skipped_count, failed_count