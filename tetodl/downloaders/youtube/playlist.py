"""
Playlist iteration logic
"""
import os
import time
from typing import List, Optional, Callable, Tuple

from ...utils.i18n import get_text as _
from ...utils.styles import print_process, print_info, print_success, print_error
from ...utils.processing import extract_video_id
from ...utils.files import create_m3u8_playlist
from ...core.registry import registry
from ...core.history import load_history
from ...constants import RuntimeConfig

def download_playlist_sequential(
    urls: List[str], 
    target_dir: str, 
    download_func: Callable[..., Tuple[bool, str, bool]], 
    content_type: str = "audio",
    is_youtube_music: bool = False, 
    content_title: str = "Playlist", 
    allowed_indices: Optional[List[int]] = None,
    alt_check_dirs: Optional[List[str]] = None, 
    quiet: bool = False
) -> Tuple[int, int, int]:
    """
    Process a list of URLs sequentially with delay control.

    This function iterates through the provided URLs one by one. It explicitly 
    checks against the registry to avoid redundant downloads and enforces a 
    configurable sleep delay between requests to minimize the risk of rate-limiting. 
    Finally, it compiles the results into an m3u8 playlist if enabled.
    """

    total = len(urls)
    success_count = 0
    failed_count = 0
    skipped_count = 0
    failed_urls: List[str] = []
    ordered_files: List[str] = []

    dirs_to_check = [target_dir]
    if alt_check_dirs:
        dirs_to_check.extend(alt_check_dirs)
    
    for i, url in enumerate(urls, 1):
        if allowed_indices is not None:
            if i not in allowed_indices:
                if not quiet: print_info(f"Skipping item {i} (Not selected)")
                continue
        
        video_id = extract_video_id(url)
        
        found_existing = False
        
        if video_id:
            for check_dir in dirs_to_check:
                exists, metadata = registry.check_existing(video_id, content_type, check_dir)
                if exists:
                    if not quiet: print_process(_('download.youtube.progress', current=i, total=total))
                    if not quiet: print_info(_('download.youtube.file_exists_playlist', title=metadata.get('title', video_id)))
                    found_existing = True
                    if metadata.get('file_path'):
                        ordered_files.append(os.path.basename(metadata.get('file_path')))
                    break
        
        if found_existing:
            skipped_count += 1
            time.sleep(0.1)
            continue

        if not quiet: print_process(_('download.youtube.progress', current=i, total=total))

        try:
            if not quiet: print_info(_('download.youtube.downloading_url', url=url, type=content_type))
            if content_type == "audio":
                success, result, skipped = download_func(
                    url, target_dir, use_cache=True,
                    is_youtube_music=is_youtube_music,
                    download_type="Playlist Track"
                )
            else:
                success, result, skipped = download_func(url, target_dir, use_cache=True, download_type="Playlist Video")

            if success:
                load_history()
                
                if RuntimeConfig.DOWNLOAD_HISTORY:
                    last_entry = RuntimeConfig.DOWNLOAD_HISTORY[-1]
                    # Verify if the last entry matches the current video
                    if last_entry.get('id') == video_id or video_id is None:
                        fpath = last_entry.get('file_path')
                        if fpath:
                            ordered_files.append(os.path.basename(fpath))
                
                if skipped:
                    if not quiet: print_info(_('download.youtube.file_exists', title=result))
                    skipped_count += 1
                else:
                    if not quiet: print_success(_('download.youtube.success', title=result))
                    success_count += 1
            else:
                if not quiet: print_error(_('download.youtube.failed', title=result))
                failed_count += 1
                failed_urls.append(url)
                
        except Exception as e:
            if not quiet: print_error(_('download.youtube.error_downloading', type=content_type, error=str(e)))
            failed_count += 1
            failed_urls.append(url)

        # Delay logic for sequential downloads
        if i < total:
            if not quiet: print_process(_('download.youtube.wait_delay', delay=RuntimeConfig.DOWNLOAD_DELAY))
            time.sleep(RuntimeConfig.DOWNLOAD_DELAY)

    if RuntimeConfig.CREATE_M3U and ordered_files:
        create_m3u8_playlist(target_dir, content_title, ordered_files, quiet)
        
    if not quiet: print_success(_('download.youtube.summary',
                    success=success_count,
                    skipped=skipped_count,
                    failed=failed_count,
                    total=total,
                    type=content_type))

    return success_count, skipped_count, failed_count