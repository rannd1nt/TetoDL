'''
Concurrent downloading module for YouTube playlists/albums.
'''

import os
import time
import sys
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional, Callable, Tuple, Union

from ...utils.i18n import get_text as _
from ...utils.styles import print_process, print_info, print_success, print_error, color
from ...utils.processing import extract_video_id
from ...utils.files import create_m3u8_playlist
from ...core.registry import registry
from ...constants import RuntimeConfig

def _worker_task(
    url: str, 
    target_dir: str, 
    download_func: Callable[..., Tuple[bool, str, bool]], 
    content_type: str, 
    is_youtube_music: bool, 
    index: int,
    alt_check_dirs: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Handles the logic for a single download thread.
    
    It first checks the internal registry to see if the content already exists 
    to prevent unnecessary downloads. If the file is missing, it triggers the 
    provided download function and returns the execution status (success, skipped, or failed).
    """
    
    time.sleep(random.uniform(0.1, 1.0))
    
    video_id = extract_video_id(url)
    
    
    if video_id:
        dirs_to_check = [target_dir]
        if alt_check_dirs:
            dirs_to_check.extend(alt_check_dirs)

        for check_dir in dirs_to_check:
            exists, meta = registry.check_existing(video_id, content_type, check_dir)
            
            if exists:
                return {
                    'status': 'success',
                    'skipped': True,
                    'index': index,
                    'title': meta.get('title', 'Unknown'),
                    'file_path': meta.get('file_path'),
                    'url': url
                }

    try:
        if content_type == "audio":
            success, title, skipped = download_func(
                url, target_dir, use_cache=True,
                is_youtube_music=is_youtube_music,
                download_type="Playlist Track",
                quiet=True
            )
        else:
            success, title, skipped = download_func(
                url, target_dir, use_cache=True,
                download_type="Playlist Video",
                quiet=True
            )

        final_path = None
        if success and video_id:
            exists, meta = registry.check_existing(video_id, content_type, target_dir)
            if exists:
                final_path = meta.get('file_path')

        return {
            'status': 'success' if success else 'failed',
            'skipped': skipped,
            'index': index,
            'title': title,
            'file_path': final_path,
            'url': url
        }

    except Exception as e:
        return {
            'status': 'error',
            'index': index,
            'error': str(e),
            'url': url
        }

def download_playlist_concurrent(
    urls: List[str], 
    target_dir: str, 
    download_func: Callable, 
    content_type: str = "audio",
    is_youtube_music: bool = False, 
    content_title: str = "Playlist", 
    allowed_indices: Optional[List[int]] = None,
    alt_check_dirs: Optional[List[str]] = None, 
    quiet: bool = False
) -> Tuple[int, int, int]:
    """
    Orchestrates downloading multiple items simultaneously using a thread pool.
    
    This function manages the worker queue, updates the UI with a real-time 
    progress counter (success/skip/fail stats), and handles graceful shutdowns 
    if the user interrupts the process. It also optionally generates an m3u8 playlist file.
    """
    
    max_workers = 3
    if hasattr(RuntimeConfig, 'ASYNC_WORKERS'):
        max_workers = RuntimeConfig.ASYNC_WORKERS
    
    if max_workers > 5 and not quiet:
        print_info(color("Warning: High concurrency (>5) increases risk of IP Ban.", "y"))

    tasks_queue = []
    for i, url in enumerate(urls):
        display_idx = i + 1
        if allowed_indices is not None and display_idx not in allowed_indices:
            continue
        tasks_queue.append((i, url)) 

    total_items = len(tasks_queue)
    results_store: List[Optional[str]] = [None] * len(urls) 
    
    if not quiet: 
        print_process(f"Async Mode: {max_workers} threads active. Press Ctrl+C to stop.")

    processed = 0
    success_count = 0
    skipped_count = 0
    failed_count = 0

    def print_async_status():
        if quiet: return
        
        status_str = f"[Async] {processed}/{total_items}"
        stats_str = f"OK: {color(str(success_count), 'g')} | Skip: {color(str(skipped_count), 'y')} | Fail: {color(str(failed_count), 'r')}"
        
        prefix = color("[i]", "c")
        msg = f"\r{prefix} {status_str} | {stats_str}" + " " * 20
        
        sys.stdout.write(msg)
        sys.stdout.flush()

    print_async_status()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(
                _worker_task, 
                url, target_dir, download_func, content_type, is_youtube_music, idx, alt_check_dirs
            ): idx 
            for idx, url in tasks_queue
        }

        try:
            for future in as_completed(future_map):
                result = future.result()
                processed += 1
                idx = result['index']
                
                if result['status'] == 'success':
                    if result['skipped']:
                        skipped_count += 1
                    else:
                        success_count += 1
                    
                    if result['file_path']:
                        results_store[idx] = os.path.basename(result['file_path'])
                else:
                    failed_count += 1

                print_async_status()

        except KeyboardInterrupt:
            if not quiet: print()
            print_error("Stopping threads... (Please wait)")
            executor.shutdown(wait=False)
            raise

    if not quiet:
        print()

    ordered_files = [f for f in results_store if f is not None]

    if RuntimeConfig.CREATE_M3U and ordered_files:
        create_m3u8_playlist(target_dir, content_title, ordered_files, quiet)

    if not quiet:
        print_success(_('download.youtube.summary',
                        success=success_count,
                        skipped=skipped_count,
                        failed=failed_count,
                        total=total_items,
                        type=content_type))

    return success_count, skipped_count, failed_count