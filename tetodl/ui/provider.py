"""
UI provider abstraction — separates TUI / CLI / Daemon UI concerns.

Layer: ui
Imports: core/, utils/, tetodl/ root (allowed for ui layer)
"""

from typing import Protocol, Optional


class UIProvider(Protocol):
    """Interface for all UI rendering strategies.

    - **TUIProvider**: interactive terminal (questionary + rich)
    - **CLIProvider**: silent no-ops (headless / daemon)
    """

    def header(self) -> None:
        """Render the application header / ASCII art."""

    def clear(self) -> None:
        """Clear the terminal screen."""

    def wait_and_clear_prompt(self, msg: Optional[str] = None) -> None:
        """Wait for user input then clear."""


class NullUI:
    """Silent provider — no output, no interaction.

    Used by CLI / headless / daemon modes to replace monkey-patching.
    """

    @staticmethod
    def header() -> None:
        pass

    @staticmethod
    def clear() -> None:
        pass

    @staticmethod
    def wait_and_clear_prompt(msg: Optional[str] = None) -> None:
        pass


class TUIProvider:
    """Full interactive provider — used when running in terminal."""

    @staticmethod
    def header() -> None:
        from tetodl.ui.components import header as _tui_header
        _tui_header()

    @staticmethod
    def clear() -> None:
        from tetodl.utils.formatters import clear as _tui_clear
        _tui_clear()

    @staticmethod
    def wait_and_clear_prompt(msg: Optional[str] = None) -> None:
        from tetodl.utils.display import wait_and_clear_prompt as _tui_wait
        _tui_wait(msg)
