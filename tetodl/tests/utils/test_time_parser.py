"""Tests for tetodl.utils.time_parser."""

import pytest
from tetodl.utils.time_parser import time_to_seconds, get_cut_seconds


class TestTimeToSeconds:
    def test_seconds_only(self):
        assert time_to_seconds("45") == 45.0

    def test_mm_ss(self):
        assert time_to_seconds("1:30") == 90.0

    def test_hh_mm_ss(self):
        assert time_to_seconds("1:00:00") == 3600.0

    def test_hh_mm_ss_with_single_digits(self):
        assert time_to_seconds("1:2:3") == 3723.0

    def test_start_keyword_returns_zero(self):
        assert time_to_seconds("start") == 0.0
        assert time_to_seconds("0") == 0.0

    def test_end_keyword_returns_inf(self):
        result = time_to_seconds("end")
        assert result == float("inf")

    def test_inf_keyword_returns_inf(self):
        result = time_to_seconds("inf")
        assert result == float("inf")

    def test_empty_string_returns_zero(self):
        assert time_to_seconds("") == 0.0

    def test_whitespace_stripped(self):
        assert time_to_seconds("  45  ") == 45.0

    def test_invalid_format_raises_value_error(self):
        with pytest.raises(ValueError):
            time_to_seconds("abc")

    def test_seconds_exceeds_59_raises_value_error(self):
        with pytest.raises(ValueError, match="Seconds cannot be >= 60"):
            time_to_seconds("1:70")

    def test_minutes_exceeds_59_raises_value_error(self):
        with pytest.raises(ValueError, match="Minutes cannot be >= 60"):
            time_to_seconds("70:30")

    def test_too_many_parts_raises_value_error(self):
        with pytest.raises(ValueError, match="Format too long"):
            time_to_seconds("1:2:3:4")

    def test_invalid_number_format_raises_value_error(self):
        with pytest.raises(ValueError, match="Invalid number format"):
            time_to_seconds("1:2x:30")


class TestGetCutSeconds:
    def test_get_cut_seconds(self):
        result = get_cut_seconds("1:30-3:00")
        assert result == (90.0, 180.0)

    def test_get_cut_seconds_no_end(self):
        result = get_cut_seconds("1:30-")
        assert result == (90.0, float("inf"))

    def test_get_cut_seconds_no_start(self):
        result = get_cut_seconds("-3:00")
        assert result == (0.0, 180.0)

    def test_get_cut_seconds_no_dash_treats_as_start_to_end(self):
        result = get_cut_seconds("1:30")
        assert result == (90.0, float("inf"))

    def test_get_cut_none_on_empty_input(self):
        assert get_cut_seconds("") is None
        assert get_cut_seconds(None) is None  # type: ignore[arg-type]

    def test_start_after_end_raises_value_error(self):
        with pytest.raises(ValueError, match="Start time"):
            get_cut_seconds("3:00-1:30")

    def test_invalid_format_raises_value_error(self):
        with pytest.raises(ValueError, match="Invalid format"):
            get_cut_seconds("1-2-3")
