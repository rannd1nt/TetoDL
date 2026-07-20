from unittest.mock import MagicMock, patch

import pytest

from tetodl.core.models import CliDownload, CliExit, CliMenu, DownloadSession
from tetodl.ui.entry.app import App


class TestApp:
    """Tests for the App class in ui/entry/app.py."""

    def test_app_instantiation(self):
        """App() creates without error."""
        app = App()
        assert app is not None
        assert app.update_status is None

    @patch("tetodl.ui.entry.app.cli")
    def test_app_run_with_download(self, mock_cli, mocker):
        """App.run dispatches download when CLI returns CliDownload."""
        mock_cli.parse.return_value = (False, CliDownload(
            session=DownloadSession(
                url="https://youtube.com/watch?v=test",
                media_type="audio",
            ),
        ))
        mock_exec = mocker.patch("tetodl.cli.dispatch.execute_download")
        mock_bootstrap = mocker.patch("tetodl.ui.entry.app.bootstrap")

        app = App()
        app.run()

        mock_exec.assert_called_once()
        mock_bootstrap.setup_application.assert_called_once()

    @patch("tetodl.ui.entry.app.cli")
    def test_app_run_handled_exit(self, mock_cli, mocker):
        """App.run returns early when CLI returns handled=True."""
        mock_cli.parse.return_value = (True, CliExit())
        mock_exec = mocker.patch("tetodl.cli.dispatch.execute_download")

        app = App()
        app.run()

        mock_exec.assert_not_called()

    @patch("tetodl.ui.entry.app.cli")
    def test_app_run_menu(self, mock_cli, mocker):
        """App.run enters menu loop when CLI returns CliMenu."""
        mock_cli.parse.return_value = (False, CliMenu())
        mock_bootstrap = mocker.patch("tetodl.ui.entry.app.bootstrap")
        mock_loop = mocker.patch.object(App, "_loop_menu")

        app = App()
        app.run()

        mock_loop.assert_called_once()
        mock_bootstrap.setup_application.assert_called_once()
