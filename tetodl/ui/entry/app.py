"""
App: The main application controller.
"""
import sys

from tetodl.constants import IS_TERMUX

from . import bootstrap
from . import menu

from tetodl.ui.components import header, thread_cancel_handle, run_in_thread
from tetodl.ui.provider import TUIProvider
from tetodl.utils.console import console
from tetodl.utils.formatters import clear
from tetodl.utils.display import wait_and_clear_prompt
from tetodl.utils.i18n_keys import Keys

from tetodl.cli.parser import cli
from tetodl.core.models import CliDownload, CliSearch, CliMenu, DownloadSession
from tetodl.core.config import save_config, load_app_config
from tetodl.core.search import perform_youtube_search

class App:
    """
    The main application facade that orchestrates the TetoDL lifecycle.
    """
    def __init__(self):
        self.update_status = None

    def launch(self):
        """Initialize resources and start the main application loop."""
        try:
            handled, result = cli.parse()
        except KeyboardInterrupt:
            print()
            sys.exit(0)

        if handled:
            return

        # Bootstrap for actionable results
        if isinstance(result, (CliDownload, CliSearch)):
            bootstrap.setup_application(force_recheck=result.force_recheck)
            bootstrap.start_update_checker(self)

        # --- SEARCH -> DOWNLOAD ---
        if isinstance(result, CliSearch):
            url = perform_youtube_search(result.query, result.limit)
            if url:
                session = result.session.model_copy(update={'url': url})
                from tetodl.cli.dispatch import execute_download as _exec
                _exec(session)
            return

        # --- DIRECT DOWNLOAD ---
        if isinstance(result, CliDownload):
            from tetodl.cli.dispatch import execute_download as _exec
            _exec(result.session)
            return

        # --- TUI MENU ---
        if isinstance(result, CliMenu):
            bootstrap.setup_application(force_recheck=result.force_recheck)
            bootstrap.start_update_checker(self)
            if result.force_recheck:
                return
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
            from tetodl.pipeline.handlers import download_audio_youtube as _dl
            self._interactive_dl("yt_audio", _dl)

        elif choice == "2":
            from tetodl.pipeline.handlers import download_video_youtube as _dl
            self._interactive_dl("yt_video", _dl)

        elif choice == "3":
            from tetodl.ui.settings import menu_folder
            clear()
            header()
            menu_folder()

        elif choice == "4":
            from tetodl.ui.settings import menu_settings
            clear()
            header()
            menu_settings()

        elif choice == "5":
            from tetodl.ui.analytics import display_history
            clear()
            header()
            display_history()

        elif choice == "6":
            from tetodl.ui.about import menu_about
            clear()
            header()
            menu_about()

        elif choice == "7":
            self._exit_app()

        else:
            if IS_TERMUX:
                console.err(Keys.error.invalid_input)
                import time
                time.sleep(0.6)

    def _interactive_dl(self, title_key, dl_func, use_thread=True):
        """Helper for interactive download prompt."""
        url = menu.prompt_download_url(title_key)
        if url:
            is_yt = title_key in ("yt_audio", "yt_video")
            if is_yt:
                config = load_app_config()
                session = DownloadSession(url=url)
                if use_thread:
                    thread_cancel_handle(run_in_thread(dl_func, url, session=session, config=config, ui=TUIProvider()))
                else:
                    dl_func(url, session=session, config=config, ui=TUIProvider())
            else:
                if use_thread:
                    thread_cancel_handle(run_in_thread(dl_func, url))
                else:
                    dl_func(url)
                    wait_and_clear_prompt()

    def _exit_app(self):
        """Clean exit."""
        clear()
        save_config()
        console.exit(Keys.menu.main.exit)

app = App()