"""Tests for tetodl.utils.formatters."""

import pytest

from tetodl.utils.formatters import (
    Colors,
    clear,
    color,
    format_duration,
    format_duration_digital,
    key_color,
    truncate_title,
)


class TestColor:
    def test_color_wraps_text_with_ansi(self):
        result = color("hello", "r")
        assert result.startswith(Colors.RED)
        assert result.endswith(Colors.RESET)
        assert "hello" in result

    def test_color_green(self):
        result = color("ok", "g")
        assert result.startswith(Colors.GREEN)

    def test_color_bold(self):
        result = color("bold", "r", bold=True)
        assert result.startswith(Colors.BOLD)
        assert Colors.RED in result

    def test_color_invalid_code_raises(self):
        with pytest.raises(ValueError, match="Invalid color code"):
            color("test", "invalid_code")

    def test_color_yellow(self):
        result = color("warn", "y")
        assert result.startswith(Colors.YELLOW)

    def test_color_blue(self):
        result = color("info", "b")
        assert Colors.BLUE in result

    def test_color_cyan(self):
        result = color("info", "c")
        assert Colors.CYAN in result

    def test_color_white(self):
        result = color("text", "w")
        assert Colors.WHITE in result


class TestClear:
    def test_clear_exists(self):
        assert callable(clear)


class TestTruncateTitle:
    def test_truncate_short_title(self):
        assert truncate_title("Hello") == "Hello"

    def test_truncate_long_title(self):
        title = "A" * 100
        result = truncate_title(title, max_chars=50)
        assert len(result) <= 50
        assert result.endswith("...")

    def test_truncate_none_title(self):
        assert truncate_title(None) == "Unknown Title"

    def test_truncate_empty_title(self):
        assert truncate_title("") == "Unknown Title"


class TestFormatDuration:
    def test_format_duration_seconds_only(self):
        assert format_duration(45) == "45s"

    def test_format_duration_minutes(self):
        assert format_duration(90) == "1m 30s"

    def test_format_duration_hours(self):
        assert format_duration(3661) == "1h 1m 1s"

    def test_format_duration_none(self):
        assert format_duration(None) == "0s"

    def test_format_duration_zero(self):
        assert format_duration(0) == "0s"


class TestFormatDurationDigital:
    def test_digital_mm_ss(self):
        assert format_duration_digital(90) == "01:30"

    def test_digital_hh_mm_ss(self):
        assert format_duration_digital(3661) == "1:01:01"

    def test_digital_none(self):
        assert format_duration_digital(None) == "--:--"

    def test_digital_zero(self):
        assert format_duration_digital(0) == "--:--"


class TestKeyColor:
    def test_key_color_default(self):
        result = key_color("test", ansi=Colors.YELLOW)
        assert "test" in result
        assert Colors.YELLOW in result

    def test_key_color_bold(self):
        result = key_color("test", ansi=Colors.YELLOW, bold=True)
        assert Colors.BOLD in result
