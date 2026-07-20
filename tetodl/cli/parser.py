import argparse
import sys
import os
from typing import Tuple, Optional, Literal, cast

from ..constants import (
    APP_VERSION, AUDIO_QUALITY_OPTIONS, VALID_CONTAINERS, VALID_CODECS,
    IS_TERMUX, VALID_THUMBNAIL_FORMATS
)
from ..core import config as cfg
from ..utils.console import console
from ..utils.i18n_keys import Keys
from ..utils.formatters import color
from ..core import config as config_mgr
from ..core.models import DownloadSession, CliResult, CliDownload, CliSearch, CliMenu, CliExit
from ..utils.files import TempManager
from ..utils.network import start_share_server
from ..utils.display import show_app_info
from ..core import maintenance

_DEBUG_MODES = frozenset({'all', 'errors', 'concise'})

class CLIHandler:
    """
    Handles Command Line Interface argument parsing and validation.
    """
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            prog="tetodl",
            description=color("TetoDL - Hybrid CLI/TUI Media Suite\n\n", 'c') +
                        "Commands:\n" +
                        "  [URL]              Download media\n" +
                        "  debug (all|errors|concise)  Run with tracing\n" +
                        "  daemon             Manage Background API Server (Run 'tetodl daemon --help')",
            formatter_class=argparse.RawTextHelpFormatter
        )
        self._setup_args()

    def _setup_args(self):
        """Define all CLI arguments and groups."""
        # --- GLOBAL FLAGS ---
        self.parser.add_argument('--version', action='store_true', help="Show version")
        self.parser.add_argument('--debug', action='store_true',
            help="Enable debugging & tracing output (equivalent to 'tetodl debug all').\n"
                 "Combine with --quiet for trace-only output.")

        # --- 1. DOWNLOAD GROUP ---
        dl_group = self.parser.add_argument_group('Download Options')
        dl_group.add_argument('url', nargs='?', help='Media URL to download')
        dl_group.add_argument('-a', '--audio', action='store_true', help='Audio only mode')
        dl_group.add_argument('-v', '--video', action='store_true', help='Video only mode')
        dl_group.add_argument('-f', '--format', help='Force format (mp3/m4a/opus | mp4/mkv | jpg/png)')
        
        dl_group.add_argument('-r', '--resolution', 
            choices=['144p', '240p', '360p', '480p', '720p', '1080p', '2k', '4k', '8k'],
            help='Max video resolution limit'
        )
        dl_group.add_argument('-c', '--codec', 
            choices=VALID_CODECS,
            help='Set video codec priority'
        )

        dl_group.add_argument('--async', dest='async_mode', action='store_true', help="Enable concurrent downloads (YouTube playlists/albums)")
        dl_group.add_argument('--search', metavar='QUERY', help="Search YouTube interactively")
        dl_group.add_argument('-l', '--limit', type=int, default=5, metavar='NUM', help="Search limit")
        dl_group.add_argument('--quiet', action='store_true', help="Suppress download log and progress output")
        
        # Processing Flags
        dl_group.add_argument('--cut', metavar='TIME', help="Trim media (e.g. '01:30-02:00')")
        dl_group.add_argument('--items', metavar='LIST', help="Playlist items to download (e.g. '1,2,5-10')")
        dl_group.add_argument('--group', nargs='?', const=True, default=False, metavar='NAME', 
            help="Group Playlist/Album downloads into a subfolder. Optional: Specify folder name.")
        dl_group.add_argument('--m3u', action='store_true', help="Generate .m3u8 playlist file")
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

    def _handle_daemon_subcommand(self):
        daemon_parser = argparse.ArgumentParser(
            prog="tetodl daemon",
            description=color("TetoDL Background API Daemon Manager", 'c')
        )
        
        action_group = daemon_parser.add_mutually_exclusive_group()
        action_group.add_argument('-d', '--display', action='store_true', help="Show daemon access URL and QR code")
        action_group.add_argument('-r', '--run', action='store_true', help="Run the API daemon locally")
        action_group.add_argument('-s', '--setup', action='store_true', help="Setup and register systemd service")
        action_group.add_argument('-rm', '--remove', action='store_true', help="Remove systemd service")
        
        daemon_parser.add_argument('--host', default="0.0.0.0", help="Bind IP Address (default: 0.0.0.0)")
        daemon_parser.add_argument('--port', type=int, default=7370, help="Bind Port (default: 7370)")

        args = daemon_parser.parse_args(sys.argv[2:])

        if args.display:
            from ..daemon.display import display_daemon_url
            display_daemon_url()
        elif args.setup:
            from ..daemon.service import setup_systemd
            setup_systemd(args.host, args.port)
        elif args.run:
            from ..daemon.api import run_server
            console.warn(Keys.cli.starting_api_server(host=args.host, port=args.port))
            run_server(args.host, args.port)
        elif args.remove:
            from ..daemon.service import remove_systemd
            remove_systemd()
        else:
            daemon_parser.print_help()
            
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
            from ..ui import analytics as _a
            _a.render_history_view(args.history, args.reverse, args.find)
            return True

        if args.wrap:
            config_mgr.load_config()
            from ..ui import analytics as _a
            _a.render_analytics_view()
            return True

        # Update / Uninstall
        if args.update:
            console.warn(Keys.cli.checking_for_updates)
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
            console.ok(Keys.cli.header_style(style=args.header))
            changed = True
        
        if args.progress_style and config_mgr.set_progress_style(args.progress_style):
            console.ok(Keys.cli.progress_style(style=args.progress_style))
            changed = True
            
        if args.lang and config_mgr.update_language(args.lang):
            console.ok(Keys.cli.language_set(name=config_mgr.get_language_name(args.lang)))
            changed = True
            
        if args.delay is not None or args.retries is not None:
            config_mgr.set_network_config(delay=args.delay, retries=args.retries)
            if args.delay:
                console.ok(Keys.cli.delay_set(delay=args.delay))
            if args.retries:
                console.ok(Keys.cli.retries_set(retries=args.retries))
            changed = True

        if args.media_scanner:
            state = (args.media_scanner == 'on')
            config_mgr.set_media_scanner(state)
            status = "Enabled" if state else "Disabled"
            console.ok(Keys.cli.media_scanner_status(status=status))
            if not IS_TERMUX and state:
                console.warn(Keys.cli.media_scanner_note)
            changed = True

        return changed

    def _handle_standalone_share(self, args):
        """Handle share command without download context."""
        
        # 1. Root Path Determination
        root_path = None
        if args.audio: 
            root_path = cfg.music_root
        elif args.video: 
            root_path = cfg.video_root
        
        # 2. Target Path
        target_path = args.share
        if root_path and target_path == 'LATEST':
            target_path = root_path
        
        # --- Logic Group Resolution ---
        if args.group:
            if not root_path:
                console.err("To share a group folder, please specify mode: -a (Audio) or -v (Video).")
                console.warn("Example: tetodl --share -a --group \"My Folder\"")
                return

            if isinstance(args.group, str):
                group_name = args.group
                potential_path = os.path.join(root_path, group_name)
                
                if os.path.exists(potential_path):
                    target_path = potential_path
                else:
                    console.err(Keys.cli.group_folder_not_found(name=group_name))
                    console.warn(Keys.cli.searched_in(path=root_path))
                    return 
            else:
                console.err(Keys.cli.specify_folder_name) 
                return
        
        # --- Fallback & LATEST ---
        if target_path is None and root_path:
            target_path = root_path

        if target_path == 'LATEST':
            config_mgr.load_config()
            from ..core.history import load_history, _download_history
            load_history()
            if not _download_history:
                console.err(Keys.cli.no_download_history)
                return
            last = next((x for x in reversed(_download_history) if x['success']), None)
            if last and os.path.exists(last['file_path']):
                target_path = last['file_path']
            else:
                console.err(Keys.cli.last_download_missing)
                return

        # 3. Final Execution
        if target_path and os.path.exists(target_path):
            if args.zip:
                if os.path.isdir(target_path):
                    from ..utils.files import create_zip_archive
                    
                    console.proc(Keys.cli.archiving_folder(name=os.path.basename(target_path)))
                    
                    zip_path = create_zip_archive(target_path)
                    
                    if zip_path and os.path.exists(zip_path):
                        try:
                            console.ok(Keys.cli.serving_temp_archive(name=os.path.basename(zip_path)))
                            start_share_server(zip_path)
                        except KeyboardInterrupt:
                            print()
                            pass
                        finally:
                            if os.path.exists(zip_path):
                                console.warn(Keys.cli.cleaning_temp_archive)
                                try:
                                    os.remove(zip_path)
                                    console.ok(Keys.cli.cleanup_complete)
                                except Exception as e:
                                    console.err(Keys.cli.failed_remove_temp_zip(error=e))
                        
                        return
                    else:
                        console.err(Keys.cli.failed_to_create_zip)
                        return
                else:
                    console.warn(Keys.cli.skipping_zip_creation)

            # Normal Share (Folder Mode)
            if args.group:
                console.ok(Keys.cli.sharing_group(name=os.path.basename(target_path)))
            
            try:
                start_share_server(target_path)
            except KeyboardInterrupt:
                print()
                pass
        else:
            console.err("Cannot share: Path not found.")
            if target_path:
                console.warn(f"Path: {target_path}")
            else:
                console.warn("Usage: tetodl --share [PATH] or --share -a/-v [--group NAME]")

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
            if args.cut:
                self.parser.error("Invalid flag: --cut cannot be used with --thumbnail-only.")
            if args.resolution or args.codec:
                self.parser.error("Invalid flag: Video settings cannot be used with --thumbnail-only.")
        
        if args.audio and (args.resolution or args.codec):
            console.warn(Keys.cli.audio_mode_note)
        
        # RULE 5: Search Constraints
        if args.limit != 5 and not args.search:
            self.parser.error("The --limit flag requires --search.")
            
        return True

    def _prepare_context(self, args) -> CliResult:
        """Prepare the execution result from parsed args."""
        detected_type, validated_format = self._detect_type_and_format(args)

        # --- Path / share-temp ---
        is_share_temp = bool(args.share_temp)
        output_path = None
        share_after = bool(args.share) or is_share_temp

        if is_share_temp:
            output_path = str(TempManager.get_temp_dir())
        elif args.output:
            if not os.path.exists(args.output):
                try:
                    os.makedirs(args.output)
                except OSError:
                    self.parser.error(f"Error: Cannot create directory {args.output}")
            output_path = os.path.abspath(args.output)

        # --- Playlist items ---
        playlist_items = None
        if args.items:
            from ..utils.processing import parse_playlist_items
            try:
                playlist_items = parse_playlist_items(args.items)
            except ValueError as e:
                self.parser.error(str(e))

        # --- Cut range ---
        cut_range = None
        if args.cut:
            from ..utils.time_parser import get_cut_seconds
            try:
                cut_range = get_cut_seconds(args.cut)
            except ValueError as e:
                self.parser.error(f"Invalid --cut format: {e}")

        # --- Resolution ---
        resolution = None
        if args.resolution and detected_type == 'video':
            res_map = {
                '144p': '144p', '240p': '240p', '360p': '360p',
                '480p': '480p', '720p': '720p', '1080p': '1080p',
                '2k': '1440p', '4k': '2160p', '8k': '4320p',
            }
            resolution = res_map.get(args.resolution, '720p')

        # --- Build DownloadSession ---
        session = DownloadSession(
            url=args.url or '',
            media_type=detected_type,
            output_path=output_path,
            format=validated_format,
            codec=args.codec if (args.codec and detected_type == 'video') else None,
            resolution=resolution,
            cut_range=cut_range,
            playlist_items=playlist_items,
            group_folder=args.group or False,
            lyrics=bool(args.lyrics),
            romaji=bool(args.romaji),
            zip=bool(args.zip),
            m3u=bool(args.m3u),
            smart_cover=bool(args.smart_cover),
            no_cover=bool(args.no_cover),
            force_crop=bool(args.force_crop),
            quiet=bool(args.quiet),
            async_mode=bool(args.async_mode),
            share_after_download=share_after,
            is_temp_session=is_share_temp,
        )

        if args.search:
            return CliSearch(
                query=args.search,
                limit=args.limit,
                session=session,
                force_recheck=args.recheck,
            )

        if args.url:
            return CliDownload(
                session=session,
                force_recheck=args.recheck,
            )

        return CliMenu()

    def _detect_type_and_format(self, args) -> Tuple[Literal['audio', 'video', 'thumbnail'], Optional[str]]:
        """Detect media type and validate format."""
        detected_type = None

        if args.thumbnail_only:
            detected_type = 'thumbnail'
        elif args.audio:
            detected_type = 'audio'
        elif args.video:
            detected_type = 'video'

        if detected_type is None and args.format:
            if args.format in VALID_THUMBNAIL_FORMATS:
                detected_type = 'thumbnail'
            elif args.format in AUDIO_QUALITY_OPTIONS:
                detected_type = 'audio'
            elif args.format in VALID_CONTAINERS:
                detected_type = 'video'

        if detected_type is None and (args.resolution or args.codec):
            detected_type = 'video'

        if detected_type is None and args.url:
            url_lower = args.url.lower()
            if "music.youtube.com" in url_lower or "spotify.com" in url_lower:
                detected_type = 'audio'
            else:
                detected_type = 'video'

        if detected_type is None:
            detected_type = 'video'

        validated_format = None
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
            validated_format = fmt

        return cast(Literal['audio', 'video', 'thumbnail'], detected_type), validated_format

    def parse(self) -> Tuple[bool, CliResult]:
        """Returns: (handled, result)"""
        if len(sys.argv) > 1 and sys.argv[1].lower() == 'daemon':
            self._handle_daemon_subcommand()
            return True, CliExit()

        # --- debug subcommand: tetodl debug {all|errors|concise} [options...] ---
        if len(sys.argv) > 2 and sys.argv[1].lower() == 'debug':
            mode = sys.argv[2].lower()
            if mode not in _DEBUG_MODES:
                self.parser.error(
                    f"Usage: tetodl debug {', '.join(sorted(_DEBUG_MODES))} [options...]\n"
                    f"  all       — all traces\n"
                    f"  errors    — exceptions only\n"
                    f"  concise   — entry/exit only\n"
                    f"Got: {mode!r}"
                )
            from ..utils.logger import set_debug
            set_debug(mode)
            from ..utils.tracer import set_dump_path
            set_dump_path()
            del sys.argv[1:3]

        args = self.parser.parse_args()

        # --debug flag: equivalent to 'tetodl debug all'
        if args.debug:
            from ..utils.logger import set_debug
            set_debug('all')
            from ..utils.tracer import set_dump_path
            set_dump_path()

        if self._handle_early_dispatch(args):
            return True, CliExit()

        self._validate_rules(args)
        result = self._prepare_context(args)

        return False, result

cli = CLIHandler()
