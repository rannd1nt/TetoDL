"""
Dispatch: Handles CLI Execution Logic (Headless Mode).
"""
import os
from tetodl.constants import RuntimeConfig
from tetodl.utils.styles import print_info, print_error, print_neutral, print_success
from tetodl.utils.files import TempManager, move_contents_and_cleanup
from tetodl.utils.network import start_share_server

# Downloaders
from tetodl.downloaders.youtube.handlers import download_audio_youtube, download_video_youtube
from tetodl.downloaders.youtube.tasks import download_thumbnail_task
# Suppress noisy output during CLI run
from tetodl.downloaders.youtube import handlers, tasks

def _apply_runtime_overrides(overrides):
    """Inject CLI overrides into RuntimeConfig."""
    if overrides.get('simple_mode'): RuntimeConfig.SIMPLE_MODE = True
    
    if 'output_path' in overrides:
        path = overrides['output_path']
        RuntimeConfig.MUSIC_ROOT = path
        RuntimeConfig.VIDEO_ROOT = path
        RuntimeConfig.THUMBNAIL_ROOT = path
        
    if 'format' in overrides:
        fmt = overrides['format']
        if overrides.get('type') == 'video': RuntimeConfig.VIDEO_CONTAINER = fmt
        else: RuntimeConfig.AUDIO_QUALITY = fmt
    
    if 'codec' in overrides: RuntimeConfig.VIDEO_CODEC = overrides['codec']
    if 'resolution' in overrides: RuntimeConfig.MAX_VIDEO_RESOLUTION = overrides['resolution']

    if overrides.get('smart_cover'):
        RuntimeConfig.SMART_COVER_MODE = True
        RuntimeConfig.NO_COVER_MODE = False
    if overrides.get('no_cover'):
        RuntimeConfig.SMART_COVER_MODE = False
        RuntimeConfig.NO_COVER_MODE = True
    if overrides.get('force_crop'): RuntimeConfig.FORCE_CROP = True
    if overrides.get('lyrics'): RuntimeConfig.LYRICS_MODE = True
    if overrides.get('romaji'): RuntimeConfig.ROMAJI_MODE = True
    if overrides.get('zip'): RuntimeConfig.ZIP_MODE = True
    if overrides.get('group'): RuntimeConfig.GROUP_MODE = overrides.get('group')

    if overrides.get('m3u'):
        RuntimeConfig.CREATE_M3U = True
        if not RuntimeConfig.GROUP_MODE:
            RuntimeConfig.GROUP_MODE = True
            print_info("Notice: '--m3u' automatically enabled '--group' mode.")

def execute_cli_context(context):
    """
    Main logic for executing a download based on CLI context.
    """
    overrides = context.get('overrides', {})
    is_temp_session = context.get('is_temp_session', False)
    
    # Apply Config
    _apply_runtime_overrides(overrides)

    # Silence TUI elements
    handlers.header = lambda: None
    handlers.clear = lambda: None
    handlers.wait_and_clear_prompt = lambda: None
    tasks.header = lambda: None
    tasks.clear = lambda: None
    tasks.wait_and_clear_prompt = lambda: None
    
    try:
        url = overrides.get('url')
        if not url:
            print_error("Error: No URL provided for download.")
            return
        
        # Thumbnail Only
        if overrides.get('thumbnail_only'):
            if 'smart_cover' not in overrides: RuntimeConfig.SMART_COVER_MODE = False
            fmt = overrides.get('format', 'jpg')
            download_thumbnail_task(url, target_format=fmt)
            return
        
        # Audio / Video Download
        dl_type = overrides.get('type', 'video')
        cut_range = overrides.get('cut_range')
        playlist_items = overrides.get('playlist_items')
        
        group_folder = RuntimeConfig.GROUP_MODE # bool | str
        
        is_share_active = overrides.get('share_after_download', False)
        
        if dl_type == 'video':
            result = download_video_youtube(
                url, cut_range=cut_range, playlist_items=playlist_items,
                group_folder=group_folder, share_mode=is_share_active
            )
        else:
            result = download_audio_youtube(
                url, cut_range=cut_range, playlist_items=playlist_items,
                group_folder=group_folder, share_mode=is_share_active
            )
        
        # Share Logic (Temporary or Normal)
        if overrides.get('share_after_download'):
            is_success = result.get('success')
            is_existing = result.get('skipped') and result.get('file_path') and os.path.exists(result.get('file_path'))

            if result and isinstance(result, dict) and (is_success or is_existing):
                path_to_share = result.get('file_path')
                if path_to_share: path_to_share = os.path.abspath(path_to_share)
                
                if path_to_share and os.path.exists(path_to_share):
                    try:
                        start_share_server(path_to_share)
                    except KeyboardInterrupt:
                        print()
                        pass
                        
                    if result.get('is_staging'):
                        parent_dir = result.get('parent_dir')
                        print_info("Moving files back to parent folder...")
                        moved_files = move_contents_and_cleanup(path_to_share, parent_dir)
                        
                        if moved_files:
                            from tetodl.core.registry import registry
                            for new_path in moved_files:
                                filename = os.path.basename(new_path)
                                old_path = os.path.join(path_to_share, filename)
                                registry.update_path(old_path, new_path)
                            print_success(f"Moved {len(moved_files)} files and updated registry.")
                        else:
                            print_neutral("No files moved (Empty or Error).")
                else:
                    print_error("Cannot share: Path not found.")
            else:
                if not result.get('suppress_error'):
                    if not is_success and not is_existing:
                        print_error("Nothing to share (Download failed and no existing files found).")
    
    except KeyboardInterrupt:
        print_info("Operation cancelled by user.")
    
    finally:
        if is_temp_session:
            print_info("Cleaning up temporary files...")
            TempManager.cleanup()
            print_success("Cleanup complete.")