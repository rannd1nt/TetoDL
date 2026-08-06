import argparse
import os
import re
import sys
from typing import Literal, cast

from ...constants import (
    APP_VERSION,
    AUDIO_QUALITY_OPTIONS,
    VALID_CODECS,
    VALID_CONTAINERS,
    VALID_THUMBNAIL_FORMATS
)
from ...core.domain import config as cfg
from ...core.domain import config as config_mgr
from ...core.domain.env import env
from ...core.domain import cache as cache_mod
from ...core import maintenance
from ...core.domain.models import (
    CliDownload,
    CliExit,
    CliMenu,
    CliResult,
    CliSearch,
    DownloadSession,
)
from ...utils.console import console
from ...utils.display import show_app_info
from ...utils.files import TempManager
from ...utils.formatters import color
from ...utils.i18n_keys import Keys
from .network import start_share_server

_DEBUG_MODES = frozenset({'all', 'errors', 'concise'})
_SHARE_COMBINABLE = frozenset('tzga')
"""Booleans that can be bundled after -s or -g in combined short flags."""

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
                        "  debug              Run with tracing\n" +
                        "  service            Run & manage Background API Server (Run 'tetodl service --help')",
            formatter_class=argparse.RawTextHelpFormatter
        )
        self._setup_args()

    def _setup_args(self):
        """Define all CLI arguments and groups."""
        # --- GLOBAL FLAGS ---
        self.parser.add_argument('--version', action='store_true', help="Show version")

        # --- 1. DOWNLOAD GROUP ---
        dl_group = self.parser.add_argument_group('Download Options')
        dl_group.add_argument('url', nargs='?', help='Media URL to download')

        # Mode flags (kapital)
        dl_group.add_argument('-A', '--audio', action='store_true', help='Audio only mode')
        dl_group.add_argument('-V', '--video', action='store_true', help='Video only mode')
        dl_group.add_argument('-T', '--thumbnail', action='store_true', help="Download thumbnail only")
        dl_group.add_argument('-S', '--search', metavar='QUERY', help="Search YouTube interactively")

        # Modifier flags
        dl_group.add_argument('-c', '--cover', action='store_true', help="Fetch & embed cover art")
        dl_group.add_argument('-m', '--metadata', action='store_true', help="Fetch & embed rich metadata (artist, album, genre, etc.)")
        dl_group.add_argument('-l', '--lyrics', action='store_true', help="Fetch & embed lyrics (Genius)")
        dl_group.add_argument('-N', '--no-enrich', action='store_true', help="Strip all enrichment (override auto -cm from YTM/Spotify)")
        dl_group.add_argument('-a', '--async', dest='async_mode', action='store_true', help="Concurrent downloads (playlist/album)")
        dl_group.add_argument('-g', '--group', nargs='?', const=True, default=False, metavar='NAME',
            help="Group downloads into a subfolder. Optional: Specify folder name.")
        dl_group.add_argument('-s', '--share', metavar='PATH', nargs='?', const='LATEST', help="Host file/folder via HTTP")
        dl_group.add_argument('-t', '--temp', action='store_true', help="Download to temp directory (requires -s)")
        dl_group.add_argument('-z', '--zip', action='store_true', help="Archive output into a ZIP file")
        dl_group.add_argument('-f', '--format', help='Force format (mp3/m4a/opus | mp4/mkv | jpg/png)')
        dl_group.add_argument('-o', '--output', metavar='PATH', help='Custom output directory')
        dl_group.add_argument('-r', '--resolution',
            choices=['144p', '240p', '360p', '480p', '720p', '1080p', '2k', '4k', '8k'],
            help='Max video resolution limit'
        )
        dl_group.add_argument('-q', '--quiet', action='store_true', help="Suppress download log and progress output")

        # Long-only flags
        dl_group.add_argument('--codec', choices=VALID_CODECS, help='Set video codec priority (ex --codec h264)')
        dl_group.add_argument('--romaji', action='store_true', help="Prioritize Romanized lyrics (Requires -l)")
        dl_group.add_argument('--limit', type=int, default=5, metavar='NUM', help="Search result limit")
        dl_group.add_argument('--cut', metavar='TIME', help="Trim media (e.g. '01:30-02:00')")
        dl_group.add_argument('--items', metavar='LIST', help="Playlist items to download (e.g. '1,2,5-10')")
        dl_group.add_argument('--m3u', action='store_true', help="Generate .m3u8 playlist file")

        # --- 2. UTILITY GROUP ---
        util_group = self.parser.add_argument_group('Utility & Maintenance')
        util_group.add_argument('--info', action='store_true', help="Show info")
        util_group.add_argument('--wrap', action='store_true', help="Show Analytics")
        util_group.add_argument('--history', nargs='?', const=20, type=int, metavar='LIMIT', help="Show history")
        util_group.add_argument('--reverse', action='store_true', help="Reverse history")
        util_group.add_argument('--find', metavar='QUERY', help="Filter history")
        util_group.add_argument('--recheck', action='store_true', help="Force integrity check")
        util_group.add_argument('--reset', nargs="+", choices=['history', 'cache', 'config', 'registry', 'all'], help='Reset data')
        util_group.add_argument('--update', action='store_true', help='Update TetoDL')
        util_group.add_argument('--uninstall', action='store_true', help='Remove TetoDL')

        # --- 3. CONFIGURATION GROUP ---
        cfg_group = self.parser.add_argument_group('Configuration')
        cfg_group.add_argument('--header', metavar='NAME', help="Set header")
        cfg_group.add_argument('--progress-style', choices=['minimal', 'classic', 'modern'], help="Set progress style")
        cfg_group.add_argument('--lang', choices=['en', 'id'], help="Set language")
        cfg_group.add_argument('--jitter', metavar='MIN-MAX', help="Set jitter range in seconds (e.g. 3-5)")
        cfg_group.add_argument('--retries', type=int, metavar='NUM', help="Set retries")

    def _handle_service_subcommand(self):
        service_parser = argparse.ArgumentParser(
            prog="tetodl service",
            description=color("TetoDL Background API Daemon Service", 'c')
        )

        subparsers = service_parser.add_subparsers(
            dest='command', metavar='{serve,daemon}'
        )

        serve_parser = subparsers.add_parser(
            'serve', add_help=False,
            help='Run the API server in the foreground',
            description="Run the TetoDL API server in the foreground."
        )
        serve_parser.add_argument('-h', '--help', action='help',
                                  help="Show this help message and exit")
        serve_parser.add_argument('--host', default="0.0.0.0",
                                  help="Bind IP Address (default: 0.0.0.0)")
        serve_parser.add_argument('-p', '--port', type=int, default=7370,
                                  help="Bind Port (default: 7370)")
        serve_parser.add_argument('-v', '--verbose', action='store_true',
                                  help="Show request logs (default: quiet)")
        serve_parser.add_argument('-q', '--quiet', action='store_true',
                                  help="Suppress startup banner and QR output")
        serve_parser.add_argument('--dev', action='store_true',
                                  help="Run with auto-reload (development)")
        serve_parser.add_argument('--log-file', metavar='FILE',
                                  help="Tee (interactive) or redirect (non-interactive) output to a log file")

        daemon_parser = subparsers.add_parser(
            'daemon', help='Manage the background daemon service',
            description="Install, remove, inspect and follow the TetoDL daemon service."
        )
        daemon_actions = daemon_parser.add_subparsers(
            dest='action', metavar='{setup,remove,status,logs,display}'
        )

        setup_parser = daemon_actions.add_parser(
            'setup', help='Install and start the daemon service'
        )
        setup_parser.add_argument('--host', default="0.0.0.0",
                                  help="Bind IP Address (default: 0.0.0.0)")
        setup_parser.add_argument('-p', '--port', type=int, default=7370,
                                  help="Bind Port (default: 7370)")

        daemon_actions.add_parser('remove', help='Remove the daemon service')
        daemon_actions.add_parser('status', help='Show daemon service status')

        logs_parser = daemon_actions.add_parser(
            'logs', help='Show daemon service logs'
        )
        logs_parser.add_argument('-n', '--tail', type=int, default=50,
                                 metavar='LINES', help="Log lines to show (default: 50)")
        logs_parser.add_argument('-f', '--follow', action='store_true',
                                 help="Follow new log output")

        daemon_actions.add_parser('display', help='Show daemon access URL and QR code')

        args = service_parser.parse_args(sys.argv[2:])

        if args.command == 'serve':
            if args.verbose and args.quiet:
                service_parser.error("Cannot use both -v/--verbose and -q/--quiet.")
            from ..daemon.api import run_server
            run_server(
                args.host, args.port,
                verbose=args.verbose,
                quiet=args.quiet,
                log_file=args.log_file,
                dev=args.dev,
            )
            return

        if args.command == 'daemon':
            from ..daemon.service import get_service_manager
            manager = get_service_manager()
            if args.action == 'display':
                from ..daemon.display import display_daemon_url
                display_daemon_url()
                return
            if args.action == 'setup':
                manager.setup(args.host, args.port)
                return
            if args.action == 'remove':
                manager.remove()
                return
            if args.action == 'status':
                manager.status()
                return
            if args.action == 'logs':
                manager.logs(args.tail, args.follow)
                return
            daemon_parser.print_help()
            return

        service_parser.print_help()
            
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
            show_app_info(
                version=APP_VERSION,
                config_path=env.get('config_path') or None,
                data_dir=env.get('data_dir') or None,
                cache_mod=cache_mod,
                config_mod=config_mgr,
            )
            return True

        # History & Analytics
        if args.history is not None:
            if (args.reverse or args.find) and args.history is None:
                self.parser.error("Flags '--reverse' and '--find' can only be used with '--history'")
            config_mgr.load_config()
            from ...core.domain.history import load_history
            load_history()
            from ...ui.tui import analytics as _a
            _a.render_history_view(args.history, args.reverse, args.find)
            return True

        if args.wrap:
            config_mgr.load_config()
            from ...ui.tui import analytics as _a
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
                args.jitter or args.retries):
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

        jitter_min = jitter_max = None
        if args.jitter:
            m = re.match(r'^(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)$', args.jitter)
            if m:
                jitter_min = float(m.group(1))
                jitter_max = float(m.group(2))
                changed = True
            else:
                console.err(Keys.cli.invalid_jitter_format(value=args.jitter))
                return changed
            
        if jitter_min is not None or jitter_max is not None or args.retries is not None:
            config_mgr.set_jitter_config(min_=jitter_min, max_=jitter_max, retries=args.retries)
            if jitter_min is not None:
                console.ok(Keys.cli.jitter_set(jitter_min=str(jitter_min), jitter_max=str(jitter_max)))
            if args.retries:
                console.ok(Keys.cli.retries_set(retries=args.retries))
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
                console.err(Keys.cli.share_specify_mode)
                console.warn(Keys.cli.share_example)
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
            from ...core.domain.history import _download_history, load_history
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
                from ...utils.files import create_zip_archive
                
                name = os.path.basename(target_path.rstrip(os.sep))
                console.proc(Keys.cli.archiving_folder(name=name))
                
                zip_path = create_zip_archive(target_path)
                
                if zip_path and os.path.exists(zip_path):
                    try:
                        console.ok(Keys.cli.serving_temp_archive(name=os.path.basename(zip_path)))
                        start_share_server(zip_path)
                    except KeyboardInterrupt:
                        print()
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

            # Normal Share (Folder Mode)
            if args.group:
                console.ok(Keys.cli.sharing_group(name=os.path.basename(target_path)))
            
            try:
                start_share_server(target_path)
            except KeyboardInterrupt:
                print()
        else:
            console.err(Keys.cli.cannot_share_path_not_found)
            if target_path:
                console.warn(Keys.cli.share_path(path=target_path))
            else:
                console.warn(Keys.cli.share_usage)

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
            args.audio, args.video, args.thumbnail,
            args.format, args.resolution, args.codec,
            args.cut, args.limit != 5,
            args.cover, args.metadata, args.no_enrich,
            args.zip, args.temp,
        ]

        if any(processing_flags) and not has_target:
            if not args.share:
                self.parser.error("Processing flags require a URL or --search query.")

        # RULE 2: Mode Conflict
        modes = sum([bool(args.audio), bool(args.video), bool(args.thumbnail)])
        if modes > 1:
            self.parser.error("Conflicting modes: Choose ONLY ONE of -A/--audio, -V/--video, or -T/--thumbnail.")

        # RULE 2b: Spotify conflict
        if args.url and "spotify.com" in args.url.lower() and args.video:
            self.parser.error("Spotify mode is audio-only. Remove the -V/--video flag.")

        # RULE 3: Enrichment Flags
        if args.no_enrich and (args.cover or args.metadata or args.lyrics):
            self.parser.error("Conflict: Cannot use --no-enrich with --cover, --metadata, or --lyrics.")
        if args.romaji and not args.lyrics:
            self.parser.error("Flag --romaji requires --lyrics.")

        # RULE 4: Feature Constraints
        if args.thumbnail:
            if args.cut:
                self.parser.error("Invalid flag: --cut cannot be used with -T/--thumbnail.")
            if args.resolution or args.codec:
                self.parser.error("Invalid flag: Video settings cannot be used with -T/--thumbnail.")

        if args.audio and (args.resolution or args.codec):
            console.warn(Keys.cli.audio_mode_note)

        # RULE 5: Search Constraints
        if args.limit != 5 and not args.search:
            self.parser.error("The --limit flag requires --search.")
            
        return True

    @staticmethod
    def _decompose_share_flags(args):
        """Decompose combined short flags absorbed by -s (nargs='?').

        Argparse treats ``-stz`` as ``-s`` with value ``tz``, losing ``-t``
        and ``-z``.  This method detects short non-path values and splits
        them back into their constituent flags.
        """
        _MAP = {"t": "temp", "z": "zip", "g": "group", "a": "async_mode"}

        share = args.share
        if not isinstance(share, str) or share == "LATEST":
            return
        if os.path.exists(share) or len(share) > 4:
            return

        for ch in share:
            attr = _MAP.get(ch)
            if attr:
                setattr(args, attr, True)
            else:
                return  # unknown char — treat as valid path

        args.share = "LATEST"

    @staticmethod
    def _preprocess_combined_flags():
        """Expand combined short flags before argparse sees them.

        ``-s`` (``nargs='?'``) absorbs following flag characters as its
        value.  This method expands tokens like ``-stz`` → ``-s -t -z``
        so that argparse sees each flag individually.

        Same for ``-g`` (also ``nargs='?'``): ``-gtz`` → ``-g -t -z``.
        """
        new_argv = [sys.argv[0]]
        for arg in sys.argv[1:]:
            if arg.startswith('-') and not arg.startswith('--') and len(arg) > 2:
                rest = arg[1:]
                for flag_char in ('s', 'g'):
                    idx = rest.find(flag_char)
                    if idx >= 0:
                        after = rest[idx + 1:]
                        if after and all(c in _SHARE_COMBINABLE for c in after):
                            before = rest[:idx]
                            for c in before:
                                new_argv.append(f'-{c}')
                            new_argv.append(f'-{flag_char}')
                            for c in after:
                                new_argv.append(f'-{c}')
                            break
                else:
                    new_argv.append(arg)
                    continue
            else:
                new_argv.append(arg)
        sys.argv = new_argv

    @staticmethod
    def _looks_like_media_url(s: str) -> bool:
        _PATTERNS = ("youtube.com", "youtu.be", "music.youtube.com",
                     "spotify.com", "open.spotify.com",
                     "http://", "https://")
        return any(p in s.lower() for p in _PATTERNS)

    @staticmethod
    def _route_share_url(args):
        """When -s is active and the positional arg is NOT a media URL,
        treat it as a share target (group name or path)."""
        if args.share and args.url and not CLIHandler._looks_like_media_url(args.url):
            if args.group:
                args.group = args.url
            else:
                args.share = args.url
            args.url = None

    @staticmethod
    def _early_decompose_and_route(args):
        """Run decomposition & URL routing before early-dispatch checks."""
        CLIHandler._decompose_share_flags(args)
        CLIHandler._route_share_url(args)

    def _prepare_context(self, args) -> CliResult:
        """Prepare the execution result from parsed args."""

        is_spotify = bool(args.url and "spotify.com" in args.url.lower())

        detected_type, validated_format = self._detect_type_and_format(args)
        if is_spotify and detected_type not in ("audio", "thumbnail"):
            detected_type = "audio"

        # --- Path / temp / share ---
        output_path = None
        is_temp = bool(args.temp)
        share_after = bool(args.share)

        if is_temp and not share_after:
            self.parser.error("Flag -t/--temp requires -s/--share.")

        if is_temp:
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
            from ...utils.processing import parse_playlist_items
            try:
                playlist_items = parse_playlist_items(args.items)
            except ValueError as e:
                self.parser.error(str(e))

        # --- Cut range ---
        cut_range = None
        if args.cut:
            from ...utils.time_parser import get_cut_seconds
            try:
                cut_range = get_cut_seconds(args.cut)
            except ValueError as e:
                self.parser.error(f"Invalid --cut format: {e}")

        # --- Resolution ---
        resolution = None
        if args.resolution and detected_type == 'video':
            res_map = {
                '144p': '240p', '240p': '240p', '360p': '360p',
                '480p': '480p', '720p': '720p', '1080p': '1080p',
                '2k': '1440p', '4k': '2160p', '8k': '4320p',
            }
            resolution = res_map.get(args.resolution, '720p')

        # --- Build DownloadSession ---
        session = DownloadSession(
            url=args.url or '',
            media_type=detected_type,
            is_spotify=is_spotify,
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
            cover=bool(args.cover),
            metadata=bool(args.metadata),
            no_enrich=bool(args.no_enrich),
            quiet=bool(args.quiet),
            async_mode=bool(args.async_mode),
            share_after_download=share_after,
            is_temp_session=is_temp,
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

        return CliMenu(force_recheck=args.recheck)

    def _detect_type_and_format(self, args) -> tuple[Literal['audio', 'video', 'thumbnail'], str | None]:
        """Detect media type and validate format."""
        detected_type = None

        if args.thumbnail:
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

    def parse(self) -> tuple[bool, CliResult]:
        """Returns: (handled, result)"""
        if len(sys.argv) > 1 and sys.argv[1].lower() == 'service':
            self._handle_service_subcommand()
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
            from ...utils.logger import set_debug
            set_debug(mode)
            from ...utils.tracer import set_dump_path
            set_dump_path()
            del sys.argv[1:3]

        # Expand combined short flags (-stz → -s -t -z) before argparse
        self._preprocess_combined_flags()

        args = self.parser.parse_args()

        # Decompose share flags + route URL before early dispatch
        # so that standalone-share detection sees correct values.
        self._early_decompose_and_route(args)

        if self._handle_early_dispatch(args):
            return True, CliExit()

        self._validate_rules(args)
        result = self._prepare_context(args)

        return False, result

cli = CLIHandler()
