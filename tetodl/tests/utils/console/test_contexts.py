"""Tests for tetodl.utils.console.contexts."""

import threading

import pytest

from tetodl.utils.console.contexts import ConsoleStateContext, ConsoleSpinnerContext
from tetodl.utils.console.logger import Console


@pytest.fixture
def console():
    return Console()


class TestConsoleStateContext:
    def test_state_saved_and_restored(self, console):
        original = console.state.is_quiet
        with ConsoleStateContext(console, {"is_quiet": True}):
            assert console.state.is_quiet is True
        assert console.state.is_quiet == original

    def test_multiple_overrides(self, console):
        with ConsoleStateContext(console, {"is_quiet": True, "is_debug": True}):
            assert console.state.is_quiet is True
            assert console.state.is_debug is True
        assert console.state.is_quiet is False

    def test_falsy_overrides_skipped(self, console):
        with ConsoleStateContext(console, {"is_quiet": False, "is_debug": None}):
            assert console.state.is_quiet is False
            assert console.state.is_debug is False

    def test_unknown_key_skipped(self, console):
        with ConsoleStateContext(console, {"nonexistent": True}):
            pass

    def test_returns_console(self, console):
        ctx = ConsoleStateContext(console, {"is_quiet": True})
        with ctx as c:
            assert c is console

    def test_restores_on_exception(self, console):
        original = console.state.is_quiet
        try:
            with ConsoleStateContext(console, {"is_quiet": True}):
                raise ValueError("boom")
        except ValueError:
            pass
        assert console.state.is_quiet == original


class TestConsoleSpinnerContext:
    def test_does_not_start_when_quiet(self, console):
        console.state.is_quiet = True
        with ConsoleSpinnerContext(console, "test"):
            pass

    def test_starts_and_stops_thread(self, console):
        with ConsoleSpinnerContext(console, "working") as spinner:
            assert spinner.running is True
            assert spinner.thread is not None
            assert spinner.thread.is_alive()
        assert spinner.running is False

    def test_exit_clears_output(self, console, mocker):
        mock_write = mocker.patch("sys.stdout.write")
        mock_flush = mocker.patch("sys.stdout.flush")
        with ConsoleSpinnerContext(console, "working"):
            pass
        mock_write.assert_any_call("\r\033[K")

    def test_custom_delay(self, console):
        ctx = ConsoleSpinnerContext(console, "test", delay=0.2)
        assert ctx.delay == 0.2

    def test_multiple_spins(self, console):
        with ConsoleSpinnerContext(console, "first"):
            pass
        with ConsoleSpinnerContext(console, "second"):
            pass
