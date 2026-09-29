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

"""Tests for tetodl.utils.console.themes."""

import sys

from tetodl.utils.console.themes import (
    LogTheme,
    PlainTheme,
    RichTheme,
    detect_terminal_theme,
)

THEME_FIELDS = {"ok", "warn", "proc", "err", "exit", "panic", "debug"}


class TestLogTheme:
    def test_required_symbol_fields_present(self):
        instance = LogTheme(ok="", warn="", proc="", err="", exit="", panic="", debug="")
        for name in THEME_FIELDS:
            assert hasattr(instance, name), f"LogTheme instance missing field {name}"

    def test_color_fields_have_defaults(self):
        theme = LogTheme(ok="[OK]", warn="[WARN]", proc="[PROC]", err="[ERR]", exit="[EXIT]", panic="[PANIC]", debug="[DEBUG]")
        assert theme.ok_color != ""
        assert theme.err_color != ""
        assert theme.warn_color != ""
        assert theme.reset_color != ""


class TestRichTheme:
    def test_has_expected_symbols(self):
        assert RichTheme.ok == "[✓]"
        assert RichTheme.err == "[✗]"
        assert RichTheme.warn == "[!]"
        assert RichTheme.proc == "[i]"
        assert RichTheme.exit == "[-]"
        assert RichTheme.panic == "[PANIC!]"
        assert RichTheme.debug == "[DEBUG]"

    def test_has_expected_color_attrs(self):
        for attr in ("ok_color", "err_color", "warn_color", "proc_color",
                     "info_color", "exit_color", "panic_color", "debug_color",
                     "text_color", "accent_color", "reset_color"):
            assert hasattr(RichTheme, attr)


class TestPlainTheme:
    def test_has_expected_symbols(self):
        assert PlainTheme.ok == "[OK]"
        assert PlainTheme.err == "[ERR]"
        assert PlainTheme.warn == "[WARN]"
        assert PlainTheme.proc == "[PROC]"
        assert PlainTheme.exit == "[EXIT]"
        assert PlainTheme.panic == "[PANIC!]"
        assert PlainTheme.debug == "[DEBUG]"

    def test_has_expected_color_attrs(self):
        for attr in ("ok_color", "err_color", "warn_color", "proc_color",
                     "info_color", "exit_color", "panic_color", "debug_color",
                     "text_color", "accent_color", "reset_color"):
            assert hasattr(PlainTheme, attr)


class TestDetectTerminalTheme:
    def test_returns_log_theme(self):
        theme = detect_terminal_theme()
        assert isinstance(theme, LogTheme)

    def test_returns_rich_theme_when_utf8(self, mocker):
        mock_stdout = mocker.MagicMock()
        mock_stdout.encoding = "UTF-8"
        mocker.patch.object(sys, "stdout", mock_stdout)
        theme = detect_terminal_theme()
        assert theme is RichTheme

    def test_returns_plain_theme_when_not_utf8(self, mocker):
        mock_stdout = mocker.MagicMock()
        mock_stdout.encoding = "ascii"
        mocker.patch.object(sys, "stdout", mock_stdout)
        theme = detect_terminal_theme()
        assert theme is PlainTheme
