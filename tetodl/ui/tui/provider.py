# Copyright 2026 rannd1nt
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
UI provider abstraction — separates TUI / CLI / Daemon UI concerns.

Layer: ui
Imports: core/, utils/, tetodl/ root (allowed for ui layer)
"""

from typing import Protocol


class UIProvider(Protocol):
    """Interface for all UI rendering strategies.

    - **TUIProvider**: interactive terminal (questionary + rich)
    - **CLIProvider**: silent no-ops (headless / daemon)
    """

    def header(self) -> None:
        """Render the application header / ASCII art."""

    def clear(self) -> None:
        """Clear the terminal screen."""

    def wait_and_clear_prompt(self, msg: str | None = None) -> None:
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
    def wait_and_clear_prompt(msg: str | None = None) -> None:
        pass


class TUIProvider:
    """Full interactive provider — used when running in terminal."""

    @staticmethod
    def header() -> None:
        from tetodl.ui.tui.components import header as _tui_header
        _tui_header()

    @staticmethod
    def clear() -> None:
        from tetodl.utils.formatters import clear as _tui_clear
        _tui_clear()

    @staticmethod
    def wait_and_clear_prompt(msg: str | None = None) -> None:
        from tetodl.utils.display import wait_and_clear_prompt as _tui_wait
        _tui_wait(msg)
