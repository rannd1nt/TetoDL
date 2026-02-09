"""
The main application facade that orchestrates the TetoDL lifecycle.
"""
import os
import sys
import time
import threading
import subprocess
import questionary
from questionary import Choice

from teto_dl.core.search import perform_youtube_search

from ..constants import RuntimeConfig, IS_TERMUX
from ..utils.i18n import get_text as _
from ..utils.styles import (
    print_info, print_error, print_neutral, clear,
    color, menu_style, print_success
)
from ..core import cli
from ..core.config import (
    initialize_config, save_config, get_audio_quality_info
)
from ..core.history import load_history
from ..core.dependency import get_ytdlp_version_info
from ..ui.analytics import display_history
from ..ui.settings import menu_folder, menu_settings
from ..ui.about import menu_about
from ..ui.components import header, thread_cancel_handle, run_in_thread
from ..utils.display import wait_and_clear_prompt
from ..utils.files import TempManager
from ..downloaders.spotify import download_spotify
from ..utils.network import start_share_server
import teto_dl.downloaders.youtube as yt_downloader_module 
from teto_dl.downloaders.youtube import download_audio_youtube, download_video_youtube

class App:
    """
    The main application facade that orchestrates the TetoDL lifecycle.
    """
    def __init__(self):
        self.update_status = None

    def setup(self, force_recheck=False):
        """Init config, history, and dependencies."""
        initialize_config()
        load_history()

        if force_recheck or not RuntimeConfig.VERIFIED_DEPENDENCIES:
            from ..ui.verifier import verify_dependencies

            header_title = "System Integrity Check" if force_recheck else None

            if not verify_dependencies(header_title):
                sys.exit(1)
        
        threading.Thread(target=self._update_checker_worker, daemon=True).start()

    def _update_checker_worker(self):
        """Background worker to check updates silently."""
        try:
            is_outdated, current, latest = get_ytdlp_version_info()
            if is_outdated:
                self.update_status = (current, latest)
        except Exception:
            pass

    def _get_labels(self):
        """Generate menu labels dynamically."""
        audio_info = get_audio_quality_info()
        
        return {
            "yt_audio": f"- {_('menu.main.youtube_audio', format=audio_info['ext'].upper(), bitrate=audio_info['bitrate'])}",
            "yt_video": f"- {_('menu.main.youtube_video', container=RuntimeConfig.VIDEO_CONTAINER.upper(), resolution=RuntimeConfig.MAX_VIDEO_RESOLUTION)}",
            "spotify": f"- {_('menu.main.spotify')}" if RuntimeConfig.SPOTIFY_AVAILABLE else f"{_('menu.main.spotify_unavailable')}",
            "folder": f"- {_('menu.main.root_folder')}",
            "settings": f"- {_('menu.main.settings')}",
            "history": f"- {_('menu.settings.history')}",
            "about": f"- {_('menu.main.about')}",
            "exit": f"- {_('menu.main.exit')}"
        }

    def _handle_update_prompt(self):
        """Handle the UI interruption for update."""
        current, latest = self.update_status
        
        clear()
        header()
        print("  " + print_info(f"Dependency Update Available!", True))
        print(f"      {color('Current:', 'y')} {current}")
        print(f"      {color('Latest :', 'g')} {latest}")
        print()
        
        should_update = False

        if not IS_TERMUX:
            should_update = questionary.confirm(
                "Do you want to update now?",
                qmark=' ',
                default=True,
                style=menu_style()
            ).ask()
        else:
            try:
                res = input(f"{color('Update now? (Y/n) > ', 'c')}").strip().lower()
                should_update = res in ['', 'y', 'yes']
            except KeyboardInterrupt:
                pass

        if should_update:
            print()
            print_info("Updating yt-dlp...")
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"]
                )
                print_success("Update complete!")
                time.sleep(1)
            except subprocess.CalledProcessError:
                print_error("Update failed. Please check your connection.")
                time.sleep(2)
        
        self.update_status = None

    def menu(self):
        """Render UI and capture user choice."""
        clear()
        header()
        
        lbl = self._get_labels()
        is_spotify_disabled = not RuntimeConfig.SPOTIFY_AVAILABLE

        # --- LINUX ---
        if not IS_TERMUX:
            choices = [
                Choice(title=lbl["yt_audio"], value="1"),
                Choice(title=lbl["yt_video"], value="2"),
                Choice(title=lbl["spotify"], value="3", disabled=is_spotify_disabled),
                Choice(title=lbl["folder"], value="4"),
                Choice(title=lbl["settings"], value="5"),
                Choice(title=lbl["history"], value="6"),
                Choice(title=lbl["about"], value="7"),
                Choice(title=lbl["exit"], value="8"),
            ]
            
            selection = questionary.select(
                _('menu.main.choose'), choices=choices, style=menu_style(),
                qmark='', pointer=">", use_indicator=False, 
                show_description=False, instruction=' '
            ).ask()
            
            if selection is None: self._exit_app()
            return selection

        # --- TERMUX  ---
        else:
            print(color(f"{_('menu.main.choose')}", "c"))
            for key in ["yt_audio", "yt_video", "spotify", "folder", "settings", "history", "about", "exit"]:
                print(lbl[key])
            print()

            try:
                return input(f"{color('Pilihan > ', 'c')}").strip()
            except KeyboardInterrupt:
                return None

    def _dl_wrapper(self, title_key, dl_func, use_thread=True):
        clear()
        header()
        
        lbl = self._get_labels()
        
        print(color(f"[{lbl.get(title_key, '').replace('- ', '')}]", 'c'))
        
        url = input("Link => ").strip()
        if url:
            if use_thread:
                thread_cancel_handle(run_in_thread(dl_func, url))
            else:
                dl_func(url)
                wait_and_clear_prompt()

    def _apply_runtime_overrides(self, overrides):
        """Menerapkan konfigurasi CLI ke dalam RuntimeConfig (Synchronized)"""
        
        if overrides.get('simple_mode'):
            RuntimeConfig.SIMPLE_MODE = True
            
        if 'output_path' in overrides:
            path = overrides['output_path']
            RuntimeConfig.MUSIC_ROOT = path
            RuntimeConfig.VIDEO_ROOT = path
            
        if 'format' in overrides:
            fmt = overrides['format']
            dl_type = overrides.get('type')
            
            if dl_type == 'video':
                RuntimeConfig.VIDEO_CONTAINER = fmt
            else:
                RuntimeConfig.AUDIO_QUALITY = fmt
        
        if 'codec' in overrides:
            RuntimeConfig.VIDEO_CODEC = overrides['codec']
        
        if 'resolution' in overrides:
            RuntimeConfig.MAX_VIDEO_RESOLUTION = overrides['resolution']

        if overrides.get('smart_cover'):
            RuntimeConfig.SMART_COVER_MODE = True
            RuntimeConfig.NO_COVER_MODE = False
            
        if overrides.get('no_cover'):
            RuntimeConfig.SMART_COVER_MODE = False
            RuntimeConfig.NO_COVER_MODE = True
            
        if overrides.get('force_crop'):
            RuntimeConfig.FORCE_CROP = True

    def act(self, choice):
        """Execute logic based on choice."""
        if not choice: return

        if choice == "1":
            self._dl_wrapper("yt_audio", download_audio_youtube)

        elif choice == "2":
            self._dl_wrapper("yt_video", download_video_youtube)

        elif choice == "3":
            if RuntimeConfig.SPOTIFY_AVAILABLE:
                self._dl_wrapper("spotify", download_spotify, use_thread=False)
            else:
                clear(); header()
                print_error(_('download.spotify.not_available'))
                print_info(_('download.spotify.install_instruction'))
                time.sleep(3.5)

        elif choice == "4":
            clear(); header(); menu_folder()

        elif choice == "5":
            clear(); header(); menu_settings()

        elif choice == "6":
            clear(); header(); display_history()

        elif choice == "7":
            clear(); header(); menu_about()

        elif choice == "8":
            self._exit_app()

        else:
            if IS_TERMUX:
                print_error(_('error.invalid_input'))
                time.sleep(0.6)

    def _exit_app(self):
        """Clean exit."""
        clear()
        save_config()
        print_neutral(_('menu.main.exit'), "[-]")
        sys.exit(0)

    def run(self):
        """Initialize resources and start the main application loop."""
        try:
            handled, context = cli.init_parser()
        except KeyboardInterrupt:
            print()
            sys.exit(0)

        if handled:
            return
        
        self.setup(force_recheck=context.get('force_recheck', False))

        if context.get('mode') == 'cli_search':
            query = context.get('query')
            limit = context.get('limit', 5)
            url = perform_youtube_search(query, limit)
            
            if url:
                context['overrides']['url'] = url
                context['mode'] = 'cli_download' 
            else:
                return
            
        if context.get('mode') == 'cli_download':
            overrides = context.get('overrides', {})
            is_temp_session = context.get('is_temp_session', False)
            
            # Dependency & Silence Injection
            self._apply_runtime_overrides(overrides)
            yt_downloader_module.header = lambda: None
            yt_downloader_module.clear = lambda: None
            yt_downloader_module.wait_and_clear_prompt = lambda: None
            
            try:
                url = overrides.get('url')
                if not url:
                    print_error("Error: No URL provided for download.")
                    return
                
                if overrides.get('thumbnail_only'):
                    if 'smart_cover' not in overrides:
                        RuntimeConfig.SMART_COVER_MODE = False
                    
                    fmt = overrides.get('format', 'jpg')
                    yt_downloader_module.download_thumbnail_task(url, target_format=fmt)
                    return
                
                dl_type = overrides.get('type', 'video')
                cut_range = overrides.get('cut_range')

                if dl_type == 'video':
                    result = yt_downloader_module.download_video_youtube(url, cut_range)
                else:
                    result = yt_downloader_module.download_audio_youtube(url, cut_range)
                
                if overrides.get('share_after_download'):
                    if result and isinstance(result, dict) and result.get('success'):
                        file_path = result.get('file_path')
                        
                        if file_path and os.path.exists(file_path):
                            start_share_server(file_path)
                        else:
                            print_error("Cannot share file: File path not found or file missing.")
                    else:
                        pass
            except KeyboardInterrupt:
                print_info("Operation cancelled by user.")
            
            finally:
                if is_temp_session:
                    print_info("Cleaning up temporary files...")
                    TempManager.cleanup()
                    print_success("Cleanup complete.")
            return
        
        while True:
            if self.update_status:
                self._handle_update_prompt()
            choice = self.menu()
            if choice is None and IS_TERMUX:
                return
            
            self.act(choice)

app = App()