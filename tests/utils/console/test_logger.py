"""Tests for tetodl.utils.console.logger."""


import pytest

from tetodl.utils.console.logger import Console, ConsoleState


@pytest.fixture
def console(mocker):
    c = Console()
    mocker.patch.object(c, "_print")
    return c


class TestConsoleOk:
    def test_calls_print_with_ok_symbol(self, console):
        console.ok("All good")
        console._print.assert_called_once_with(
            console.theme.ok, console.theme.ok_color, "All good"
        )


class TestConsoleErr:
    def test_calls_print_with_err_symbol(self, console):
        console.err("Failed")
        console._print.assert_called_once_with(
            console.theme.err, console.theme.err_color, "Failed"
        )


class TestConsoleWarn:
    def test_calls_print_with_warn_symbol(self, console):
        console.warn("Caution")
        console._print.assert_called_once_with(
            console.theme.warn, console.theme.warn_color, "Caution"
        )


class TestConsoleProc:
    def test_calls_print_with_proc_symbol(self, console):
        console.proc("Working...")
        console._print.assert_called_once_with(
            console.theme.proc, console.theme.proc_color, "Working..."
        )


class TestConsoleNeutral:
    def test_calls_print_with_exit_symbol_and_text_color(self, console):
        console.neutral("Info")
        console._print.assert_called_once_with(
            console.theme.exit, console.theme.text_color, "Info"
        )


class TestConsoleDebug:
    def test_debug_suppressed_when_not_debug(self, console, mocker):
        mocker.patch.object(console, "_resolve_text", return_value="msg")
        console.state.is_debug = False
        console.debug("secret")
        console._resolve_text.assert_not_called()

    def test_debug_output_when_debug_enabled(self, console, mocker):
        mocker.patch("builtins.print")
        mocker.patch.object(console, "_resolve_text", return_value="msg")
        console.state.is_debug = True
        console.debug("secret")
        console._resolve_text.assert_called_once_with("secret")


class TestConsoleContextManager:
    def test_context_manager(self, console):
        original_quiet = console.state.is_quiet
        with console.context(is_quiet=True):
            assert console.state.is_quiet is True
        assert console.state.is_quiet == original_quiet

    def test_context_manager_preserves_falsy_overrides(self, console):
        original = console.state.is_quiet
        with console.context(is_quiet=False):
            assert console.state.is_quiet == original


class TestConsoleState:
    def test_default_state(self):
        state = ConsoleState()
        assert state.is_quiet is False
        assert state.is_debug is False
        assert state.debug_mode == "all"

    def test_state_mutable(self):
        state = ConsoleState()
        state.is_quiet = True
        assert state.is_quiet is True
        state.is_debug = True
        assert state.is_debug is True


class TestConsoleInit:
    def test_initialises_with_theme(self):
        c = Console()
        assert c.theme is not None
        assert c.state is not None

    def test_print_respects_quiet(self, mocker):
        c = Console()
        c.state.is_quiet = True
        mock_print = mocker.patch("builtins.print")
        c._print("[OK]", "[green]", "msg")
        mock_print.assert_not_called()

    def test_print_outputs_when_not_quiet(self, mocker):
        c = Console()
        c.state.is_quiet = False
        mock_print = mocker.patch("builtins.print")
        c._print("[OK]", "[green]", "msg")
        mock_print.assert_called_once()
