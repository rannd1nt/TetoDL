import argparse
import sys
import os
from ..constants import (
    APP_VERSION, AUDIO_QUALITY_OPTIONS, VALID_CONTAINERS, VALID_CODECS, IS_TERMUX, RuntimeConfig,
    VALID_THUMBNAIL_FORMATS
)
from ..utils.styles import print_error, print_success, print_info
from ..core import config as config_mgr
from ..utils.files import TempManager
from ..utils.network import start_share_server
from ..ui import analytics
from ..utils.display import show_app_info
from . import maintenance

from typing import Tuple, Dict, Any

def init_parser() -> Tuple[bool, Dict[str, Any]]:
    """
    Initialize and handle CLI argument parsing.

    This function is responsible for:
    - Defining all CLI arguments and flags
    - Performing early-dispatch commands (e.g. --version, --info, --history)
    - Validating argument combinations and usage constraints
    - Detecting download mode automatically (audio/video) when applicable
    - Preparing execution context and override configuration for the downloader

    Returns
    -------
    Tuple[bool, Dict[str, Any]]
        A tuple consisting of:

        - handled (bool):
            Indicates whether the CLI command has been fully handled
            within this function.

            * True  → The command was executed here (e.g. config change,
                history view, reset, update, uninstall) and the program
                should terminate afterward.
            * False → The command requires further processing by the
                main application logic.

        - context (Dict[str, Any]):
            A context dictionary containing execution metadata.
            This is only meaningful when `handled` is False.

            Possible keys include:
            - "mode": str
                Execution mode identifier (e.g. "cli_download")
            - "overrides": Dict[str, Any]
                Runtime override values such as URL, media type,
                format, codec, resolution, output path, and flags.
            - "force_recheck": bool
                Indicates whether dependency rechecking is enforced.

    Notes
    -----
    - This function performs both argument parsing and dispatch logic.
    - Argument conflicts and invalid combinations are handled internally
        with user-facing error messages.
    - Auto-detection prioritizes explicit flags over inference logic.
    """

    parser = argparse.ArgumentParser(
        prog="tetodl", 
        description="TetoDL - CLI & TUI Media Downloader"
    )
    
    # --- GLOBAL FLAGS ---
    parser.add_argument('--version', action='store_true', help="Show version")

    # Manual dispatch (-v)
    if len(sys.argv) == 2 and sys.argv[1] == '-v':
        print(f"TetoDL v{APP_VERSION}")
        return True, {}

    # --- 1. DOWNLOAD GROUP ---
    dl_group = parser.add_argument_group('Download Options')
    dl_group.add_argument('url', nargs='?', help='Media URL to download')
    dl_group.add_argument('-a', '--audio', action='store_true', help='Audio only mode')
    dl_group.add_argument('-v', '--video', action='store_true', help='Video only mode')

    # Format Flag
    dl_group.add_argument('-f', '--format', help='Force format (mp3/m4a/opus for audio, mp4/mkv for video)')
    
    # Resolution Flag
    dl_group.add_argument('-r', '--resolution', 
        choices=['480p', '720p', '1080p', '2k', '4k', '8k'],
        help='Max video resolution limit'
    )

    # Codec Flag
    dl_group.add_argument('-c', '--codec', 
        choices=VALID_CODECS,
        help='Set video codec priority (default=speed, h264=compatibility, h265=size)'
    )

    dl_group.add_argument('--search', 
        metavar='QUERY',
        help="Search YouTube interactively and download"
    )
    dl_group.add_argument('-l', '--limit', 
        type=int,
        default=5,
        metavar='NUM',
        help="Number of search results (requires --search)"
    )
    dl_group.add_argument('--cut', 
        metavar='TIME',
        help="Trim media (e.g. '01:30-02:00', '01:30', '-02:00')"
    )
    dl_group.add_argument('--smart-cover', action='store_true',
        help="Force Enable Smart Cover & Metadata (iTunes search)"
    )
    dl_group.add_argument('--no-cover', action='store_true',
        help="Disable all cover art & metadata embedding"
    )
    dl_group.add_argument('--force-crop', action='store_true',
        help="Force crop YouTube thumbnail to 1:1 if iTunes fetch fails"
    )
    dl_group.add_argument('--thumbnail-only', action='store_true',
        help="Download thumbnail/cover art only (No audio/video)"
    )

    # Output / Path Flag
    dl_group.add_argument('-o', '--output', metavar='PATH', help='Custom output directory')


    # --- 2. UTILITY GROUP ---
    util_group = parser.add_argument_group('Utility & Maintenance')

    util_group.add_argument('--info', action='store_true', help="Show current configuration & system info")
    util_group.add_argument('--wrap', action='store_true', help="Show TetoDL Analytics/Wrap")
    util_group.add_argument('--history',
        nargs='?',
        const=20,
        type=int,
        metavar='LIMIT',
        help="Show download history (default last 20)"
    )
    util_group.add_argument('--reverse', action='store_true', help="Reverse order (e.g. show oldest history first)")
    util_group.add_argument('--find',
        metavar='QUERY',
        help="Filter history by title (case-insensitive)"
    )
    util_group.add_argument('--share', 
        metavar='PATH',
        nargs='?',
        const='LATEST',
        help="Host a file/folder via HTTP/QR Code for mobile transfer"
    )
    util_group.add_argument('--share-temp', 
        action='store_true',
        help="Download to temp folder, share, then auto-delete (Requires URL)"
    )
    util_group.add_argument('--recheck', action='store_true', help="Force dependency integrity check")

    # Reset
    util_group.add_argument(
        '--reset',
        nargs="+",
        choices=['history', 'cache', 'config', 'registry', 'all'],
        help='Reset application data (accepts multiple, e.g. "cache history")'
    )
    util_group.add_argument('--update', action='store_true', help='Update TetoDL to latest version (Git required)')
    util_group.add_argument('--uninstall', action='store_true', help='Remove TetoDL from system')


    # --- 3. CONFIGURATION GROUP ---
    cfg_group = parser.add_argument_group('Configuration')
    
    cfg_group.add_argument('--header', 
        metavar='NAME',
        help="Set app header (use 'default', 'classic' or filename in assets/ without .txt)"
    )
    
    cfg_group.add_argument('--progress-style', 
        choices=['minimal', 'classic', 'modern'],
        help="Set progress bar style"
    )
    cfg_group.add_argument('--lang', choices=['en', 'id'], help="Set application language")

    cfg_group.add_argument('--delay', type=float, metavar='SEC', help="Set download delay (seconds)")
    cfg_group.add_argument('--retries', type=int, metavar='NUM', help="Set max download retries")

    cfg_group.add_argument('--media-scanner', choices=['on', 'off'], help="Enable/Disable Android Media Scanner")

    args = parser.parse_args()


    # ===== HANDLING =====

    # 1. Version Check & App Config Info
    if args.version:
        print(f"TetoDL v{APP_VERSION}")
        return True, {}

    if args.info:
        config_mgr.load_config()
        show_app_info()
        return True, {}
    
    # Flags Flow Validations
    has_target = (args.url or args.search)

    # Orphan Flags Check
    processing_flags = [
        args.audio, args.video, args.thumbnail_only,
        args.format, args.resolution, args.codec,
        args.cut, args.limit != 5, 
        args.smart_cover, args.no_cover, args.force_crop,
        args.share_temp
    ]

    if any(processing_flags) and not has_target:
        parser.error("Processing flags require a URL or --search query.")


    # Mode Conflict (Ambiguous Mode)
    modes_selected = sum([bool(args.audio), bool(args.video), bool(args.thumbnail_only)])
    if modes_selected > 1:
        parser.error("Conflicting modes: Choose ONLY ONE of --audio, --video, or --thumbnail-only.")

    # Metadata Flags Conflict
    if args.smart_cover and args.no_cover:
        parser.error("Conflict: Cannot use --smart-cover (Force ON) and --no-cover (Force OFF) together.")

    if args.force_crop and args.no_cover:
        parser.error("Conflict: Cannot use --force-crop with --no-cover.")

    # Feature Constraints
    if args.thumbnail_only:
        if args.cut:
            parser.error("Invalid flag: --cut cannot be used with --thumbnail-only.")
        if args.resolution or args.codec:
            parser.error("Invalid flag: Video settings (--resolution/--codec) cannot be used with --thumbnail-only.")
    
    if args.audio:
        if args.resolution or args.codec:
            print_info("Note: --resolution and --codec are ignored in Audio mode.")
    
    # Limit Dependency
    if args.limit:
        args.limit = abs(args.limit)
        
    if args.limit == 0:
        args.limit = 1

    if args.limit != 5 and not args.search:
        parser.error("The --limit flag requires --search.")


    # --- Utility Flags Handling ---

    # History and Analytics
    if args.history is not None:
        config_mgr.load_config()
        from ..core.history import load_history
        load_history()
        analytics.render_history_view(
            limit=args.history, 
            reverse_order=args.reverse,
            search_query=args.find
        )
        return True, {}

    if args.wrap:
        config_mgr.load_config() 
        analytics.render_analytics_view()
        return True, {}
    
    # Config Flags
    if (args.header or args.progress_style or args.lang or
        args.delay or args.retries or args.media_scanner):
        config_mgr.load_config() 

        config_changed = False
        
        if args.header:
            if config_mgr.set_header_style(args.header):
                print_success(f"Header style changed to: {args.header}")
                config_changed = True

        if args.progress_style:
            if config_mgr.set_progress_style(args.progress_style):
                print_success(f"Progress style changed to: {args.progress_style}")
                config_changed = True
        if args.lang:
            if config_mgr.update_language(args.lang):
                print_success(f"Language set to: {config_mgr.get_language_name(args.lang)}")
                config_changed = True

        if args.delay is not None or args.retries is not None:
            config_mgr.set_network_config(delay=args.delay, retries=args.retries)
            if args.delay: print_success(f"Download delay set to: {args.delay}s")
            if args.retries: print_success(f"Max retries set to: {args.retries}")
            config_changed = True

        if args.media_scanner:
            state = (args.media_scanner == 'on')
            config_mgr.set_media_scanner(state)
            status_text = "Enabled" if state else "Disabled"
            print_success(f"Media Scanner {status_text}.")
            if not IS_TERMUX and state:
                print_info("Media Scanner only affects Android/Termux environments.")
            config_changed = True

        if config_changed:
            return True, {}
    
    # Reset Flag
    if args.reset:
        targets = set(args.reset)
        success = False
        
        if 'all' in targets:
            res = input("Are you sure you want reset ALL? (y/N) > ")
            if res.lower() == 'y':
                config_mgr.perform_full_wipe()
                print_success("Full factory reset successful (All data wiped).")
                return True, {}
            print_info("Operation Cancelled")
            return True, {}

        actions = {
            'history': ('History', config_mgr.clear_history),
            'cache':   ('Cache', config_mgr.clear_cache),
            'config':  ('Config', config_mgr.reset_config),
            'registry':('Registry', config_mgr.wipe_registry)
        }

        for target in targets:
            if target in actions:
                name, func = actions[target]
                success = func()
                
                if success:
                    print_success(f"{name} cleared.")
                else:
                    print_success(f"{name} is already clean or not found.")
        
        return True, {}

    # Handle Share Standalone, Update & Uninstall
    if args.share and not (args.url or args.search):
        target_path = args.share
        
        if args.audio:
            target_path = RuntimeConfig.MUSIC_ROOT
        elif args.video:
            target_path = RuntimeConfig.VIDEO_ROOT
        
        if target_path == 'LATEST':
            config_mgr.load_config()
            from ..core.history import load_history
            load_history()
            
            history = RuntimeConfig.DOWNLOAD_HISTORY
            if not history:
                print_error("No download history found to share.")
                return True, {}
                
            last_download = next((x for x in reversed(history) if x['success']), None)
            
            if last_download and os.path.exists(last_download['file_path']):
                target_path = last_download['file_path']
            else:
                print_error("Last downloaded file no longer exists.")
                return True, {}

        start_share_server(target_path)
        return True, {}
    
    if args.update:
        print_info("Checking for updates...")
        maintenance.perform_update()
        return True, {}
    
    if args.uninstall:
        maintenance.perform_uninstall()
        return True, {}
    
    # --- Download, Search & Processing Handling ---

    # Recheck Context
    context = {}
    if args.recheck:
        context['force_recheck'] = True

    # 6. Download Logic
    if args.url or args.search:
        if args.audio and args.video:
            print_error("Ambiguous mode. Choose -a or -v.")
            return True, {}

        overrides = {
            'simple_mode': True,
        }

        if args.url:
            overrides['url'] = args.url
        elif args.search:
            context['mode'] = 'cli_search'
            context['query'] = args.search
            context['limit'] = args.limit
        
        if args.smart_cover: overrides['smart_cover'] = True
        if args.no_cover: overrides['no_cover'] = True
        if args.force_crop: overrides['force_crop'] = True
        if args.thumbnail_only: overrides['thumbnail_only'] = True

        if args.share_temp:
            overrides['share_after_download'] = True
            
            temp_path = TempManager.get_temp_dir()
            overrides['output_path'] = str(temp_path)
            context['is_temp_session'] = True
        elif args.share:
            overrides['share_after_download'] = True

        # --- TYPE DETECTION CONTROL FLOW ---
        detected_type = None

        # Explicit Flag (-a / -v)
        if args.audio:
            detected_type = 'audio'
        elif args.video:
            detected_type = 'video'
        elif args.thumbnail_only:
            detected_type = 'thumbnail'

        # Format Inference (-f mp3 / -f mp4)
        if detected_type is None and args.format:
            if args.format in AUDIO_QUALITY_OPTIONS:
                detected_type = 'audio'
            elif args.format in VALID_CONTAINERS:
                detected_type = 'video'
            elif args.format in VALID_THUMBNAIL_FORMATS:
                detected_type = 'thumbnail'

        # Implicit Video Flags (-r / -c)
        if detected_type is None:
            if args.resolution or args.codec:
                detected_type = 'video'

        # URL Pattern Fallback
        if detected_type is None and args.url:
            url_lower = args.url.lower()
            if "music.youtube.com" in url_lower or "spotify.com" in url_lower:
                detected_type = 'audio'
            else:
                detected_type = 'video'

        if detected_type is None:
            detected_type = 'video'

        overrides['type'] = detected_type

        # --- FORMAT VS TYPE VALIDATION ---
        if args.format:
            fmt = args.format.lower()
        
            if detected_type == 'thumbnail':
                if fmt not in VALID_THUMBNAIL_FORMATS:
                    parser.error(f"Invalid format '{fmt}' for thumbnail mode. Valid: {', '.join(VALID_THUMBNAIL_FORMATS)}")
            
            elif detected_type == 'audio':
                if fmt not in AUDIO_QUALITY_OPTIONS:
                    if fmt in VALID_CONTAINERS:
                        parser.error(f"Conflict: Mode is Audio, but format '{fmt}' is a video container.")
                    if fmt in VALID_THUMBNAIL_FORMATS:
                        parser.error(f"Conflict: Mode is Audio, but format '{fmt}' is an image.")
                    parser.error(f"Invalid audio format '{fmt}'. Valid: {', '.join(AUDIO_QUALITY_OPTIONS.keys())}")

            elif detected_type == 'video':
                if fmt not in VALID_CONTAINERS:
                    if fmt in AUDIO_QUALITY_OPTIONS:
                        parser.error(f"Conflict: Mode is Video, but format '{fmt}' is audio-only.")
                    if fmt in VALID_THUMBNAIL_FORMATS:
                        parser.error(f"Conflict: Mode is Video, but format '{fmt}' is an image.")
                    parser.error(f"Invalid video format '{fmt}'. Valid: {', '.join(VALID_CONTAINERS)}")
            
            overrides['format'] = fmt

        # --- CODEC & RESOLUTION VALIDATION ---
        if args.codec:
            if detected_type == 'audio':
                print_info(f"Ignoring codec '{args.codec}' in Audio mode.")
            else:
                overrides['codec'] = args.codec

        if args.resolution:
            if detected_type == 'audio':
                print_info(f"Ignoring resolution '{args.resolution}' in Audio mode.")
            else:
                overrides['resolution'] = args.resolution

        # --- PATH OVERRIDE ---
        if args.output:
            if not os.path.exists(args.output):
                try: os.makedirs(args.output)
                except OSError:
                    print_error(f"Error: Cannot create directory {args.output}")
                    return True, {}
            overrides['output_path'] = os.path.abspath(args.output)

        # --- RESOLUTION OVERRIDE ---
        if args.resolution:
            res_map = {
                '480p': '480p', '720p': '720p', '1080p': '1080p', 
                '2k': '1440p', '4k': '2160p', '8k': '4320p'
            }
            overrides['resolution'] = res_map.get(args.resolution, '720p')

        if args.cut:
            from ..utils.time_parser import get_cut_seconds
            
            try:
                start_sec, end_sec = get_cut_seconds(args.cut)
                overrides['cut_range'] = (start_sec, end_sec)
                overrides['cut_raw'] = args.cut
                
            except ValueError as e:
                parser.error(f"Invalid --cut format: {e}")

        if not context.get('mode') == 'cli_search':
            context['mode'] = 'cli_download'
        
        context['overrides'] = overrides
        
        return False, context

    return False, context