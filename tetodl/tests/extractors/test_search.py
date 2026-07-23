from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tetodl.core.step import PipelineError
from tetodl.extractors.search import SearchExtractor


def _mock_ytdlp(return_value: dict) -> MagicMock:
    mock_ydl = MagicMock()
    mock_ydl.extract_info.return_value = return_value
    mock_ydl.__enter__.return_value = mock_ydl
    mock_yt = MagicMock()
    mock_yt.YoutubeDL.return_value = mock_ydl
    return mock_yt


class TestSearchExtractorHandles:
    def test_handles_ytsearch(self):
        assert SearchExtractor.handles("ytsearch1:Never Gonna Give You Up")

    def test_handles_ytsearch_with_number(self):
        assert SearchExtractor.handles("ytsearch5:Never Gonna Give You Up")

    def test_handles_ytsearch_all(self):
        assert SearchExtractor.handles("ytsearch5:query")

    def test_rejects_youtube_url(self):
        assert not SearchExtractor.handles("https://youtube.com/watch?v=abc")

    def test_rejects_spotify_url(self):
        assert not SearchExtractor.handles("https://open.spotify.com/track/abc")

    def test_rejects_random_string(self):
        assert not SearchExtractor.handles("hello world")


class TestSearchExtractorExtract:
    def test_extract_success(self):
        mock_raw = {
            "id": "abc123",
            "title": "Rick Astley - Never Gonna Give You Up",
            "webpage_url": "https://youtube.com/watch?v=abc123",
            "duration": 212,
            "uploader": "Rick Astley",
            "artist": "Rick Astley",
            "track": "Never Gonna Give You Up",
            "thumbnail": "https://i.ytimg.com/vi/abc123/maxresdefault.jpg",
            "thumbnails": [],
        }
        mock_yt = _mock_ytdlp(mock_raw)

        with patch("tetodl.extractors.search.yt", mock_yt):
            extractor = SearchExtractor()
            info = extractor.extract("ytsearch1:Never Gonna Give You Up - Rick Astley")

        assert info.id == "abc123"
        assert info.title == "Rick Astley - Never Gonna Give You Up"
        assert info.url == "https://youtube.com/watch?v=abc123"
        assert info.duration == 212
        assert info.artist == "Rick Astley"
        assert info.track == "Never Gonna Give You Up"

    def test_extract_fallback_fields(self):
        mock_raw = {
            "id": "xyz789",
            "title": "Unknown Song",
            "webpage_url": None,
            "duration": None,
            "uploader": None,
            "artist": None,
            "track": None,
            "thumbnail": None,
            "thumbnails": None,
        }
        mock_yt = _mock_ytdlp(mock_raw)

        with patch("tetodl.extractors.search.yt", mock_yt):
            extractor = SearchExtractor()
            info = extractor.extract("ytsearch1:something")

        assert info.id == "xyz789"
        assert info.title == "Unknown Song"
        assert info.url == "ytsearch1:something"
        assert info.duration == 0
        assert info.uploader == ""
        assert info.artist is None
        assert info.track is None
        assert info.thumbnail is None
        assert info.thumbnails == []

    def test_extract_ytdlp_error_raises(self):
        mock_yt = MagicMock()
        mock_ydl = MagicMock()
        mock_ydl.extract_info.side_effect = Exception("Network error")
        mock_ydl.__enter__.return_value = mock_ydl
        mock_yt.YoutubeDL.return_value = mock_ydl

        with patch("tetodl.extractors.search.yt", mock_yt):
            extractor = SearchExtractor()
            with pytest.raises(PipelineError, match="Search extraction failed"):
                extractor.extract("ytsearch1:Never Gonna Give You Up")
