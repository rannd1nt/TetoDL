"""Tests for tetodl.utils.processing."""

import pytest
from tetodl.utils.processing import extract_video_id


class TestExtractVideoId:
    def test_standard_url(self):
        vid = extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assert vid == "dQw4w9WgXcQ"

    def test_short_url(self):
        vid = extract_video_id("https://youtu.be/dQw4w9WgXcQ")
        assert vid == "dQw4w9WgXcQ"

    def test_music_youtube_url(self):
        vid = extract_video_id("https://music.youtube.com/watch?v=dQw4w9WgXcQ")
        assert vid == "dQw4w9WgXcQ"

    def test_embed_url(self):
        vid = extract_video_id("https://www.youtube.com/embed/dQw4w9WgXcQ")
        assert vid == "dQw4w9WgXcQ"

    def test_shorts_url(self):
        vid = extract_video_id("https://www.youtube.com/shorts/dQw4w9WgXcQ")
        assert vid == "dQw4w9WgXcQ"

    def test_url_with_extra_params(self):
        vid = extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PL...&index=1")
        assert vid == "dQw4w9WgXcQ"

    def test_invalid_url_returns_none(self):
        assert extract_video_id("https://example.com") is None

    def test_empty_string_returns_none(self):
        assert extract_video_id("") is None

    def test_none_returns_none(self):
        assert extract_video_id(None) is None

    def test_v_slash_format(self):
        vid = extract_video_id("https://www.youtube.com/v/dQw4w9WgXcQ")
        assert vid == "dQw4w9WgXcQ"

    def test_ampersand_v_format(self):
        vid = extract_video_id("https://www.youtube.com/watch?&v=dQw4w9WgXcQ")
        assert vid == "dQw4w9WgXcQ"

    def test_youtu_be_with_params(self):
        vid = extract_video_id("https://youtu.be/dQw4w9WgXcQ?si=abc123")
        assert vid == "dQw4w9WgXcQ"


class TestParsePlaylistItems:
    @pytest.fixture
    def parse(self):
        from tetodl.utils.processing import parse_playlist_items
        return parse_playlist_items

    def test_single_item(self, parse):
        assert parse("1") == {1}

    def test_multiple_items(self, parse):
        assert parse("1,3,5") == {1, 3, 5}

    def test_range(self, parse):
        assert parse("1-5") == {1, 2, 3, 4, 5}

    def test_mixed_items_and_ranges(self, parse):
        assert parse("1,3-5,7") == {1, 3, 4, 5, 7}

    def test_reversed_range(self, parse):
        assert parse("5-1") == {1, 2, 3, 4, 5}

    def test_empty_input_raises(self, parse):
        with pytest.raises(ValueError, match="No valid items"):
            parse("")

    def test_invalid_input_raises(self, parse):
        with pytest.raises(ValueError, match="Invalid item format"):
            parse("abc")
