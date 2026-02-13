import argparse
import sys
import os
from typing import Tuple, Dict, Any

from ..constants import (
    APP_VERSION, AUDIO_QUALITY_OPTIONS, VALID_CONTAINERS, VALID_CODECS,
    IS_TERMUX, RuntimeConfig, VALID_THUMBNAIL_FORMATS
)
from ..utils.styles import print_error, print_process, print_success, print_info, color
from ..core import config as config_mgr
from ..utils.files import TempManager
from ..utils.network import start_share_server
from ..ui import analytics
from ..utils.display import show_app_info
from . import maintenance

class CLIHandler:
    """
    Handles Command Line Interface argument parsing and validation.
    """
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            prog="tetodl",
            description=color("TetoDL - Hybrid CLI/TUI Media Suite", 'c')
        )
        self._setup_args()

    def _setup_args(self):
        """Define all CLI arguments and groups."""
        # --- GLOBAL FLAGS ---
        self.parser.add_argument('--version', action='store_true', help="Show version")

        # --- 1. DOWNLOAD GROUP ---
        dl_group = self.parser.add_argument_group('Download Options')
        dl_group.add_argument('url', nargs='?', help='Media URL to download')
        dl_group.add_argument('-a', '--audio', action='store_true', help='Audio only mode')
        dl_group.add_argument('-v', '--video', action='store_true', help='Video only mode')
        dl_group.add_argument('-f', '--format', help='Force format (mp3/m4a/opus | mp4/mkv | jpg/png)')
        
        dl_group.add_argument('-r', '--resolution', 
            choices=['480p', '720p', '1080p', '2k', '4k', '8k'],
            help='Max video resolution limit'
        )
        dl_group.add_argument('-c', '--codec', 
            choices=VALID_CODECS,
            help='Set video codec priority'
        )

        dl_group.add_argument('--search', metavar='QUERY', help="Search YouTube interactively")
        dl_group.add_argument('-l', '--limit', type=int, default=5, metavar='NUM', help="Search limit")
        
        # Processing Flags
        dl_group.add_argument('--cut', metavar='TIME', help="Trim media (e.g. '01:30-02:00')")
        dl_group.add_argument('--items', metavar='LIST', help="Playlist items to download (e.g. '1,2,5-10')")
        dl_group.add_argument('--group', nargs='?', const=True, default=False, metavar='NAME', 
            help="Group Playlist/Album downloads into a subfolder. Optional: Specify folder name.")
        dl_group.add_argument('--m3u', action='store_true', help="Generate .m3u8 playlist file") # [NEW]
        dl_group.add_argument('--smart-cover', action='store_true', help="Force Enable Smart Cover")
        dl_group.add_argument('--no-cover', action='store_true', help="Disable all cover art & metadata")
        dl_group.add_argument('--force-crop', action='store_true', help="Force crop YouTube thumbnail")
        dl_group.add_argument('--lyrics', action='store_true', help="Fetch & embed lyrics (Genius)")
        dl_group.add_argument('--romaji', action='store_true', help="Prioritize Romanized lyrics (Requires --lyrics)")
        dl_group.add_argument('--thumbnail-only', action='store_true', help="Download thumbnail only")

        dl_group.add_argument('-o', '--output', metavar='PATH', help='Custom output directory')

        # --- 2. UTILITY GROUP ---
        util_group = self.parser.add_argument_group('Utility & Maintenance')
        util_group.add_argument('--info', action='store_true', help="Show info")
        util_group.add_argument('--wrap', action='store_true', help="Show Analytics")
        util_group.add_argument('--history', nargs='?', const=20, type=int, metavar='LIMIT', help="Show history")
        util_group.add_argument('--reverse', action='store_true', help="Reverse history")
        util_group.add_argument('--find', metavar='QUERY', help="Filter history")
        util_group.add_argument('--share', metavar='PATH', nargs='?', const='LATEST', help="Host file/folder")
        util_group.add_argument('--zip', action='store_true', help="Archive output into a ZIP file")
        util_group.add_argument('--share-temp', action='store_true', help="Download temp & share")
        util_group.add_argument('--recheck', action='store_true', help="Force integrity check")
        util_group.add_argument('--reset', nargs="+", choices=['history', 'cache', 'config', 'registry', 'all'], help='Reset data')
        util_group.add_argument('--update', action='store_true', help='Update TetoDL')
        util_group.add_argument('--uninstall', action='store_true', help='Remove TetoDL')

        # --- 3. CONFIGURATION GROUP ---
        cfg_group = self.parser.add_argument_group('Configuration')
        cfg_group.add_argument('--header', metavar='NAME', help="Set header")
        cfg_group.add_argument('--progress-style', choices=['minimal', 'classic', 'modern'], help="Set progress style")
        cfg_group.add_argument('--lang', choices=['en', 'id'], help="Set language")
        cfg_group.add_argument('--delay', type=float, metavar='SEC', help="Set delay")
        cfg_group.add_argument('--retries', type=int, metavar='NUM', help="Set retries")
        cfg_group.add_argument('--media-scanner', choices=['on', 'off'], help="Set Media Scanner")

    def _handle_early_dispatch(self, args) -> bool:
        """Handle commands that exit immediately or don't require download context."""
        
        # Version
        if args.version:
            print(f"TetoDL v{APP_VERSION}")
            return True

        # Manual version check
        if len(sys.argv) == 2 and sys.argv[1] == '-v':
            print(f"TetoDL v{APP_VERSION}")
            return True

        # Info
        if args.info:
            config_mgr.load_config()
            show_app_info()
            return True

        # History & Analytics
        if args.history is not None:
            if (args.reverse or args.find) and args.history is None:
                self.parser.error("Flags '--reverse' and '--find' can only be used with '--history'")
            config_mgr.load_config()
            from ..core.history import load_history
            load_history()
            analytics.render_history_view(args.history, args.reverse, args.find)
            return True

        if args.wrap:
            config_mgr.load_config()
            analytics.render_analytics_view()
            return True

        # Update / Uninstall
        if args.update:
            print_info("Checking for updates...")
            maintenance.perform_update()
            return True
        
        if args.uninstall:
            maintenance.perform_uninstall()
            return True

        # Share Standalone
        if args.share and not (args.url or args.search):
            self._handle_standalone_share(args)
            return True

        # Config Changes
        if self._handle_config_changes(args):
            return True

        # Reset
        if args.reset:
            self._handle_reset(args)
            return True

        return False

    def _handle_reset(self, args):
        """Handle data reset operations."""
        targets = args.reset
        maintenance.reset_data(targets)

    def _handle_config_changes(self, args) -> bool:
        """Handle configuration flags."""
        if not (args.header or args.progress_style or args.lang or
                args.delay or args.retries or args.media_scanner):
            return False

        config_mgr.load_config()
        changed = False

        if args.header and config_mgr.set_header_style(args.header):
            print_success(f"Header style: {args.header}")
            changed = True
        
        if args.progress_style and config_mgr.set_progress_style(args.progress_style):
            print_success(f"Progress style: {args.progress_style}")
            changed = True
            
        if args.lang and config_mgr.update_language(args.lang):
            print_success(f"Language: {config_mgr.get_language_name(args.lang)}")
            changed = True
            
        if args.delay is not None or args.retries is not None:
            config_mgr.set_network_config(delay=args.delay, retries=args.retries)
            if args.delay: print_success(f"Delay: {args.delay}s")
            if args.retries: print_success(f"Retries: {args.retries}")
            changed = True

        if args.media_scanner:
            state = (args.media_scanner == 'on')
            config_mgr.set_media_scanner(state)
            status = "Enabled" if state else "Disabled"
            print_success(f"Media Scanner {status}.")
            if not IS_TERMUX and state:
                print_info("Note: Media Scanner only affects Android/Termux.")
            changed = True

        return changed

    def _handle_standalone_share(self, args):
        """Handle share command without download context."""
        
        # 1. Root Path Determination
        root_path = None
        if args.audio: 
            root_path = RuntimeConfig.MUSIC_ROOT
        elif args.video: 
            root_path = RuntimeConfig.VIDEO_ROOT
        
        # 2. Target Path
        target_path = args.share

        # --- Logic Group Resolution ---
        if args.group:
            if not root_path:
                print_error("To share a group folder, please specify mode: -a (Audio) or -v (Video).")
                print_info("Example: tetodl --share -a --group \"My Folder\"")
                return

            if isinstance(args.group, str):
                group_name = args.group
                potential_path = os.path.join(root_path, group_name)
                
                if os.path.exists(potential_path):
                    target_path = potential_path
                else:
                    print_error(f"Group folder not found: '{group_name}'")
                    print_info(f"Searched in: {root_path}")
                    return 
            else:
                print_error("Please specify the folder name to share.") 
                return
        
        # --- Fallback & LATEST ---
        if target_path is None and root_path:
            target_path = root_path

        if target_path == 'LATEST':
            config_mgr.load_config()
            from ..core.history import load_history
            load_history()
            history = RuntimeConfig.DOWNLOAD_HISTORY
            if not history:
                print_error("No download history found.")
                return
            last = next((x for x in reversed(history) if x['success']), None)
            if last and os.path.exists(last['file_path']):
                target_path = last['file_path']
            else:
                print_error("Last downloaded file missing.")
                return

        # 3. Final Execution
        if target_path and os.path.exists(target_path):
            if args.zip:
                if os.path.isdir(target_path):
                    from ..utils.files import create_zip_archive
                    
                    print_process(f"Archiving folder for temporary share: {os.path.basename(target_path)}...")
                    
                    zip_path = create_zip_archive(target_path)
                    
                    if zip_path and os.path.exists(zip_path):
                        try:
                            print_success(f"Serving Temporary Archive: {os.path.basename(zip_path)}")
                            start_share_server(zip_path)
                        except KeyboardInterrupt:
                            print()
                            pass
                        finally:
                            if os.path.exists(zip_path):
                                print_info("Cleaning up temporary archive...")
                                try:
                                    os.remove(zip_path)
                                    print_success("Cleanup complete.")
                                except Exception as e:
                                    print_error(f"Failed to remove temp zip: {e}")
                        
                        return
                    else:
                        print_error("Failed to create zip archive.")
                        return
                else:
                    print_info("Target is a file, skipping zip creation.")

            # Normal Share (Folder Mode)
            if args.group:
                print_success(f"Sharing Group: {os.path.basename(target_path)}")
            
            try:
                start_share_server(target_path)
            except KeyboardInterrupt:
                print()
                pass
        else:
            print_error(f"Cannot share: Path not found.")
            if target_path:
                print_info(f"Path: {target_path}")
            else:
                print_info("Usage: tetodl --share [PATH] or --share -a/-v [--group NAME]")

    def _validate_rules(self, args) -> bool:
        """Perform strict validation rules on arguments."""
        
        # Limit Sanitization
        if args.limit:
            args.limit = abs(args.limit)
        if args.limit == 0:
            args.limit = 1

        has_target = (args.url or args.search)

        # RULE 1: Orphan Flags
        processing_flags = [
            args.audio, args.video, args.thumbnail_only,
            args.format, args.resolution, args.codec,
            args.cut, args.limit != 5, 
            args.smart_cover, args.no_cover, args.force_crop,
            args.share_temp 
        ]
        
        if any(processing_flags) and not has_target:
            # Share temp exception handled in early dispatch check
            if not args.share: 
                self.parser.error("Processing flags require a URL or --search query.")

        # RULE 2: Mode Conflict
        modes = sum([bool(args.audio), bool(args.video), bool(args.thumbnail_only)])
        if modes > 1:
            self.parser.error("Conflicting modes: Choose ONLY ONE of --audio, --video, or --thumbnail-only.")

        # RULE 3: Metadata Conflict & Constraints
        if args.smart_cover and args.no_cover:
            self.parser.error("Conflict: Cannot use --smart-cover and --no-cover together.")
        if args.force_crop and args.no_cover:
            self.parser.error("Conflict: Cannot use --force-crop with --no-cover.")
        if args.romaji and not args.lyrics:
            self.parser.error("Flag --romaji requires --lyrics.")

        # RULE 4: Feature Constraints
        if args.thumbnail_only:
            if args.cut: self.parser.error("Invalid flag: --cut cannot be used with --thumbnail-only.")
            if args.resolution or args.codec: self.parser.error("Invalid flag: Video settings cannot be used with --thumbnail-only.")
        
        if args.audio and (args.resolution or args.codec):
            print_info("Note: --resolution and --codec are ignored in Audio mode.")
        
        # RULE 5: Search Constraints
        if args.limit != 5 and not args.search:
            self.parser.error("The --limit flag requires --search.")
            
        return True

    def _prepare_context(self, args) -> Dict[str, Any]:
        """Prepare the execution context dictionary."""
        context = {}
        if args.recheck:
            context['force_recheck'] = True

        overrides = {'simple_mode': True}

        # Target
        if args.url:
            overrides['url'] = args.url
        elif args.search:
            context['mode'] = 'cli_search'
            context['query'] = args.search
            context['limit'] = args.limit

        # Flags
        if args.smart_cover: overrides['smart_cover'] = True
        if args.no_cover: overrides['no_cover'] = True
        if args.force_crop: overrides['force_crop'] = True
        if args.thumbnail_only: overrides['thumbnail_only'] = True
        if args.group: overrides['group'] = args.group
        if args.lyrics: overrides['lyrics'] = True
        if args.romaji: overrides['romaji'] = True
        if args.zip: overrides['zip'] = True
        if args.m3u: overrides['m3u'] = True

        if args.items:
            from ..utils.processing import parse_playlist_items
            try:
                indices = parse_playlist_items(args.items)
                overrides['playlist_items'] = indices
                overrides['items_raw'] = args.items
            except ValueError as e:
                self.parser.error(str(e))
        
        # Share
        if args.share_temp:
            overrides['share_after_download'] = True
            overrides['output_path'] = str(TempManager.get_temp_dir())
            context['is_temp_session'] = True
        elif args.share:
            overrides['share_after_download'] = True

        # Type Detection
        self._detect_type_and_format(args, overrides)

        # Other Overrides
        if args.codec and overrides['type'] == 'video':
            overrides['codec'] = args.codec

        if args.resolution and overrides['type'] == 'video':
            res_map = {'480p': '480p', '720p': '720p', '1080p': '1080p', '2k': '1440p', '4k': '2160p', '8k': '4320p'}
            overrides['resolution'] = res_map.get(args.resolution, '720p')

        if args.output:
            if not os.path.exists(args.output):
                try: os.makedirs(args.output)
                except OSError: self.parser.error(f"Error: Cannot create directory {args.output}")
            overrides['output_path'] = os.path.abspath(args.output)

        if args.cut:
            from ..utils.time_parser import get_cut_seconds
            try:
                start, end = get_cut_seconds(args.cut)
                overrides['cut_range'] = (start, end)
                overrides['cut_raw'] = args.cut
            except ValueError as e:
                self.parser.error(f"Invalid --cut format: {e}")

        if not context.get('mode') == 'cli_search':
            if args.url:
                context['mode'] = 'cli_download'
        
        context['overrides'] = overrides
        return context

    def _detect_type_and_format(self, args, overrides):
        """Helper to detect download type and validate format."""
        detected_type = None
        
        if args.thumbnail_only: detected_type = 'thumbnail'
        elif args.audio: detected_type = 'audio'
        elif args.video: detected_type = 'video'

        # Inference
        if detected_type is None and args.format:
            if args.format in VALID_THUMBNAIL_FORMATS: detected_type = 'thumbnail'
            elif args.format in AUDIO_QUALITY_OPTIONS: detected_type = 'audio'
            elif args.format in VALID_CONTAINERS: detected_type = 'video'

        if detected_type is None and (args.resolution or args.codec):
            detected_type = 'video'
        
        if detected_type is None and args.url:
            url_lower = args.url.lower()
            if "music.youtube.com" in url_lower or "spotify.com" in url_lower:
                detected_type = 'audio'
            else:
                detected_type = 'video'

        if detected_type is None: detected_type = 'video'
        overrides['type'] = detected_type

        # Format Validation
        if args.format:
            fmt = args.format.lower()
            if detected_type == 'thumbnail':
                if fmt not in VALID_THUMBNAIL_FORMATS:
                    self.parser.error(f"Invalid format '{fmt}' for thumbnail. Valid: {', '.join(VALID_THUMBNAIL_FORMATS)}")
            elif detected_type == 'audio':
                if fmt not in AUDIO_QUALITY_OPTIONS:
                    self.parser.error(f"Invalid audio format '{fmt}'.")
            elif detected_type == 'video':
                if fmt not in VALID_CONTAINERS:
                    self.parser.error(f"Invalid video format '{fmt}'.")
            
            overrides['format'] = fmt

    def parse(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Execute argument parsing flow.
        Returns: (handled, context)
        """
        args = self.parser.parse_args()
        
        if self._handle_early_dispatch(args):
            return True, {}

        self._validate_rules(args)
        context = self._prepare_context(args)
        
        return False, context

cli = CLIHandler()