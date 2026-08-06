"""
TUI menu runner — interactive loop with download, settings, analytics, about.
"""

from tetodl.core.domain.config import load_app_config
from tetodl.core.domain.env import env
from tetodl.core.domain.models import DownloadSession
from tetodl.ui.tui.components import header, run_in_thread, thread_cancel_handle
from tetodl.ui.tui.provider import TUIProvider
from tetodl.utils.console import console
from tetodl.utils.display import wait_and_clear_prompt
from tetodl.utils.formatters import clear
from tetodl.utils.i18n_keys import Keys

from . import menu


def run_tui_loop(app):
    while True:
        if app.update_status:
            menu.handle_update_prompt(app.update_status)
            app.update_status = None

        choice = menu.show_main_menu()

        if choice is None:
            app._exit_app()
            return

        _route_menu_action(app, choice)


def _route_menu_action(app, choice):
    if choice == "1":
        from tetodl.core.pipeline.handlers import download_audio_youtube as _dl
        _interactive_dl(app, "yt_audio", _dl)

    elif choice == "2":
        from tetodl.core.pipeline.handlers import download_video_youtube as _dl
        _interactive_dl(app, "yt_video", _dl)

    elif choice == "3":
        from tetodl.ui.tui.settings import menu_folder
        clear()
        header()
        menu_folder()

    elif choice == "4":
        from tetodl.ui.tui.settings import menu_settings
        clear()
        header()
        menu_settings()

    elif choice == "5":
        from tetodl.ui.tui.analytics import display_history
        clear()
        header()
        display_history()

    elif choice == "6":
        from tetodl.ui.tui.about import menu_about
        clear()
        header()
        menu_about()

    elif choice == "7":
        app._exit_app()

    else:
        if env.get("is_termux"):
            console.err(Keys.error.invalid_input)
            import time
            time.sleep(0.6)


def _interactive_dl(app, title_key, dl_func, use_thread=True):
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