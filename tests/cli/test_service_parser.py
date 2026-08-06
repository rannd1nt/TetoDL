"""Tests for the ``tetodl service`` subcommand parser."""

from unittest.mock import MagicMock, patch

import pytest


class TestServiceSubcommand:
    """Tests for ``_handle_service_subcommand`` routing."""

    @patch("tetodl.ui.cli.parser.sys.argv",
           ["tetodl", "service", "serve", "--host", "0.0.0.0", "--port", "9000"])
    def test_serve_routes_to_run_server(self):
        """``service serve`` calls ``run_server`` with parsed args."""
        from tetodl.ui.cli.parser import CLIHandler

        handler = CLIHandler()
        with patch("tetodl.ui.daemon.api.run_server") as mock_run:
            handler._handle_service_subcommand()

        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        assert args == ("0.0.0.0", 9000)
        assert kwargs == {
            "verbose": False,
            "quiet": False,
            "log_file": None,
            "dev": False,
        }

    @patch("tetodl.ui.cli.parser.sys.argv",
           ["tetodl", "service", "serve", "-v", "--log-file", "/tmp/d.log", "--dev"])
    def test_serve_verbose_dev_log_file(self):
        """Verbose/dev/log-file flags are forwarded to ``run_server``."""
        from tetodl.ui.cli.parser import CLIHandler

        handler = CLIHandler()
        with patch("tetodl.ui.daemon.api.run_server") as mock_run:
            handler._handle_service_subcommand()

        _, kwargs = mock_run.call_args
        assert kwargs["verbose"] is True
        assert kwargs["log_file"] == "/tmp/d.log"
        assert kwargs["dev"] is True

    @patch("tetodl.ui.cli.parser.sys.argv",
           ["tetodl", "service", "serve", "-v", "-q"])
    def test_serve_verbose_quiet_conflict(self):
        """``-v`` and ``-q`` are mutually exclusive on serve."""
        from tetodl.ui.cli.parser import CLIHandler

        handler = CLIHandler()
        with pytest.raises(SystemExit) as exc:
            handler._handle_service_subcommand()
        assert exc.value.code == 2

    @patch("tetodl.ui.cli.parser.sys.argv",
           ["tetodl", "service", "daemon", "status"])
    def test_daemon_status_routes(self):
        """``service daemon status`` calls manager.status."""
        from tetodl.ui.cli.parser import CLIHandler

        handler = CLIHandler()
        manager = MagicMock()
        with patch("tetodl.ui.daemon.service.get_service_manager",
                   return_value=manager):
            handler._handle_service_subcommand()
        manager.status.assert_called_once()

    @patch("tetodl.ui.cli.parser.sys.argv",
           ["tetodl", "service", "daemon", "logs", "-n", "25", "-f"])
    def test_daemon_logs_routes(self):
        """``service daemon logs -n 25 -f`` passes tail/follow to manager."""
        from tetodl.ui.cli.parser import CLIHandler

        handler = CLIHandler()
        manager = MagicMock()
        with patch("tetodl.ui.daemon.service.get_service_manager",
                   return_value=manager):
            handler._handle_service_subcommand()
        manager.logs.assert_called_once_with(25, True)

    @patch("tetodl.ui.cli.parser.sys.argv",
           ["tetodl", "service", "daemon", "setup", "--port", "9000"])
    def test_daemon_setup_routes(self):
        """``service daemon setup`` passes host/port to manager.setup."""
        from tetodl.ui.cli.parser import CLIHandler

        handler = CLIHandler()
        manager = MagicMock()
        with patch("tetodl.ui.daemon.service.get_service_manager",
                   return_value=manager):
            handler._handle_service_subcommand()
        manager.setup.assert_called_once_with("0.0.0.0", 9000)

    @patch("tetodl.ui.cli.parser.sys.argv",
           ["tetodl", "service", "daemon", "remove"])
    def test_daemon_remove_routes(self):
        """``service daemon remove`` calls manager.remove."""
        from tetodl.ui.cli.parser import CLIHandler

        handler = CLIHandler()
        manager = MagicMock()
        with patch("tetodl.ui.daemon.service.get_service_manager",
                   return_value=manager):
            handler._handle_service_subcommand()
        manager.remove.assert_called_once()

    @patch("tetodl.ui.cli.parser.sys.argv",
           ["tetodl", "service", "daemon", "display"])
    def test_daemon_display_routes(self):
        """``service daemon display`` calls display_daemon_url."""
        from tetodl.ui.cli.parser import CLIHandler

        handler = CLIHandler()
        with patch("tetodl.ui.daemon.display.display_daemon_url") as mock_disp:
            handler._handle_service_subcommand()
        mock_disp.assert_called_once()

    @patch("tetodl.ui.cli.parser.sys.argv",
           ["tetodl", "service", "daemon", "status"])
    def test_parse_dispatches_service(self):
        """``tetodl service ...`` is early-dispatched and exits."""
        from tetodl.ui.cli.parser import CLIHandler
        from tetodl.core.domain.models import CliExit

        handler = CLIHandler()
        with patch.object(CLIHandler, "_handle_service_subcommand") as mock_sub:
            handled, result = handler.parse()
        assert handled is True
        assert isinstance(result, CliExit)
        mock_sub.assert_called_once()
