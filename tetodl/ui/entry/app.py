"""
App: The main application controller.
"""
import sys
import time

from tetodl.constants import RuntimeConfig, IS_TERMUX

from . import bootstrap
from . import menu
from . import dispatch

from tetodl.ui.components import header, thread_cancel_handle, run_in_thread
from tetodl.utils.styles import print_info, print_error, print_neutral, clear
from tetodl.utils.display import wait_and_clear_prompt
from tetodl.utils.i18n import get_text as _

from tetodl.core.cli import cli
from tetodl.core.config import save_config
from tetodl.core.search import perform_youtube_search

from tetodl.downloaders.spotify import download_spotify
from tetodl.downloaders.youtube.handlers import download_audio_youtube, download_video_youtube

class App:
    """
    The main application facade that orchestrates the TetoDL lifecycle.
    """
    def __init__(self):
        self.update_status = None

    def run(self):
        """Initialize resources and start the main application loop."""
        try:
            handled, context = cli.parse()
        except KeyboardInterrupt:
            print()
            sys.exit(0)

        if handled:
            return
        
        # 1. Bootstrap Setup
        bootstrap.setup_application(force_recheck=context.get('force_recheck', False))
        bootstrap.start_update_checker(self)

        # 2. Check Mode: Search -> Download
        if context.get('mode') == 'cli_search':
            query = context.get('query')
            limit = context.get('limit', 5)
            url = perform_youtube_search(query, limit)
            
            if url:
                context['overrides']['url'] = url
                context['mode'] = 'cli_download'
            else:
                return
            
        # 3. Check Mode: Direct Download (Headless)
        if context.get('mode') == 'cli_download':
            dispatch.execute_cli_context(context)
            return
        
        # 4. Interactive Mode (TUI Loop)
        self._loop_menu()

    def _loop_menu(self):
        """Main Interactive Loop."""
        while True:
            if self.update_status:
                menu.handle_update_prompt(self.update_status)
                self.update_status = None # Reset after prompting
            
            choice = menu.show_main_menu()
            
            if choice is None: # Exit signal
                self._exit_app()
                return

            self._route_menu_action(choice)

    def _route_menu_action(self, choice):
        """Route user choice to logic."""
        if choice == "1":
            self._interactive_dl("yt_audio", download_audio_youtube)

        elif choice == "2":
            self._interactive_dl("yt_video", download_video_youtube)

        elif choice == "3":
            if RuntimeConfig.SPOTIFY_AVAILABLE:
                self._interactive_dl("spotify", download_spotify, use_thread=False)
            else:
                clear(); header()
                print_error(_('download.spotify.not_available'))
                print_info(_('download.spotify.install_instruction'))
                time.sleep(3.5)

        elif choice == "4":
            from tetodl.ui.settings import menu_folder
            clear(); header(); menu_folder()

        elif choice == "5":
            from tetodl.ui.settings import menu_settings
            clear(); header(); menu_settings()

        elif choice == "6":
            from tetodl.ui.analytics import display_history
            clear(); header(); display_history()

        elif choice == "7":
            from tetodl.ui.about import menu_about
            clear(); header(); menu_about()

        elif choice == "8":
            self._exit_app()

        else:
            if IS_TERMUX:
                print_error(_('error.invalid_input'))
                time.sleep(0.6)

    def _interactive_dl(self, title_key, dl_func, use_thread=True):
        """Helper for interactive download prompt."""
        url = menu.prompt_download_url(title_key)
        if url:
            if use_thread:
                thread_cancel_handle(run_in_thread(dl_func, url))
            else:
                dl_func(url)
                wait_and_clear_prompt()

    def _exit_app(self):
        """Clean exit."""
        clear()
        save_config()
        print_neutral(_('menu.main.exit'), "[-]")
        sys.exit(0)

app = App()