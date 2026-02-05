import argparse
import sys
import os
from ..constants import APP_VERSION, AUDIO_QUALITY_OPTIONS, VALID_CONTAINERS, VALID_CODECS, IS_TERMUX
from ..utils.styles import print_error, print_success, print_info
from ..core import config as config_mgr
from ..utils.display import show_app_info
from . import maintenance

def init_parser():
    """
    Handling CLI Argument & Dispatch dengan Auto-Detect Type.
    Menggunakan standard flag --reset.
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
    dl_group.add_argument('-v', '--video', action='store_true', help='Video mode')

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

    # Output / Path Flag
    dl_group.add_argument('-o', '--output', metavar='PATH', help='Custom output directory')


    # --- 2. UTILITY GROUP ---
    util_group = parser.add_argument_group('Utility & Maintenance')

    util_group.add_argument('--info', action='store_true', help="Show current configuration & system info")
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
    
    # 2. Config Handling
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
    
    # 3. Reset Handling
    if args.reset:
        targets = set(args.reset)
        success = False
        
        if 'all' in targets:
            config_mgr.perform_full_wipe()
            print_success("Full factory reset successful (All data wiped).")
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

    # 4. Handle Update & Uninstall
    if args.update:
        print_info("Checking for updates...")
        maintenance.perform_update()
        return True, {}
    
    if args.uninstall:
        maintenance.perform_uninstall()
        return True, {}
    
    # 5. Recheck Context
    context = {}
    if args.recheck:
        context['force_recheck'] = True

    # 6. Download Logic
    if args.url:
        if args.audio and args.video:
            print_error("Ambiguous mode. Choose -a or -v.")
            return True, {}

        # Siapkan Overrides
        overrides = {
            'simple_mode': True,
            'url': args.url
        }

        # --- TYPE DETECTION CONTROL FLOW ---
        detected_type = None

        # Explicit Flag (-a / -v)
        if args.audio:
            detected_type = 'audio'
        elif args.video:
            detected_type = 'video'

        # Format Inference (-f mp3 / -f mp4)
        if detected_type is None and args.format:
            if args.format in AUDIO_QUALITY_OPTIONS:
                detected_type = 'audio'
            elif args.format in VALID_CONTAINERS:
                detected_type = 'video'

        # Implicit Video Flags (-r / -c)
        if detected_type is None:
            if args.resolution or args.codec:
                detected_type = 'video'

        # URL Pattern Fallback
        if detected_type is None:
            url_lower = args.url.lower()
            if "music.youtube.com" in url_lower or "spotify.com" in url_lower:
                detected_type = 'audio'
            else:
                detected_type = 'video'
        
        overrides['type'] = detected_type

        # --- FORMAT VS TYPE VALIDATION ---
        if args.format:
            is_audio_fmt = args.format in AUDIO_QUALITY_OPTIONS
            is_video_fmt = args.format in VALID_CONTAINERS
            
            if detected_type == 'audio' and is_video_fmt:
                print_error(f"Conflict: Mode is Audio, but format '{args.format}' is a video container.")
                return True, {}
            
            if detected_type == 'video' and is_audio_fmt:
                print_error(f"Conflict: Mode is Video, but format '{args.format}' is audio-only.")
                return True, {}

            overrides['format'] = args.format

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

        context['mode'] = 'cli_download'
        context['overrides'] = overrides
        
        return False, context

    return False, context