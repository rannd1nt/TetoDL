from __future__ import annotations

import sys

from tetodl.ui.cli.parser import cli
from . import bootstrap


class App:
    def __init__(self):
        self.update_status = None

    def launch(self):
        try:
            handled, result = cli.parse()

        except KeyboardInterrupt:
            print()
            sys.exit(0)

        if handled:
            return

        from tetodl.core.domain.models import CliDownload, CliMenu, CliSearch


        if isinstance(result, (CliDownload, CliSearch)):
            bootstrap.setup_application(force_recheck=result.force_recheck)
            bootstrap.start_update_checker(self)

        if isinstance(result, CliSearch):
            from tetodl.core.search import perform_youtube_search
            url = perform_youtube_search(result.query, result.limit)
            if url:
                session = result.session.model_copy(update={'url': url})
                from tetodl.ui.cli.dispatch import execute_download as _exec
                _exec(session)
            return

        if isinstance(result, CliDownload):
            from tetodl.ui.cli.dispatch import execute_download as _exec
            _exec(result.session)
            return

        if isinstance(result, CliMenu):
            bootstrap.setup_application(force_recheck=result.force_recheck)
            bootstrap.start_update_checker(self)
            if result.force_recheck:
                return
            self._launch_tui()

    def _launch_tui(self):
        from tetodl.ui.tui.runner import run_tui_loop
        run_tui_loop(self)

    def _exit_app(self):
        from tetodl.core.domain.config import save_config
        from tetodl.utils.console import console
        from tetodl.utils.formatters import clear
        from tetodl.utils.i18n_keys import Keys

        clear()
        save_config()
        console.exit(Keys.menu.main.exit)


app = App()