from unittest.mock import MagicMock, patch

import pytest

from tetodl.core.models import MediaInfo
from tetodl.extractors.youtube import YouTubeExtractor


class TestYouTubeExtractor:
    """Tests for YouTubeExtractor."""

    def test_youtube_extractor_list_supported(self):
        """handles() returns True for youtube.com and youtu.be URLs."""
        assert YouTubeExtractor.handles("https://youtube.com/watch?v=test") is True
        assert YouTubeExtractor.handles("https://youtu.be/test") is True
        assert YouTubeExtractor.handles("https://music.youtube.com/watch?v=test") is True
        assert YouTubeExtractor.handles("https://www.youtube.com/playlist?list=PLtest") is True

    def test_youtube_extractor_does_not_handle_other(self):
        """handles() returns False for non-YouTube URLs."""
        assert YouTubeExtractor.handles("https://vimeo.com/12345") is False
        assert YouTubeExtractor.handles("https://example.com") is False

    def test_youtube_extractor_has_extract_method(self):
        """Has extract() method that returns MediaInfo."""
        extractor = YouTubeExtractor()
        assert hasattr(extractor, "extract")
        assert callable(extractor.extract)

    def test_youtube_extractor_raises_when_no_ytdlp(self):
        """Raises PipelineError when yt-dlp is unavailable."""
        with patch("tetodl.extractors.youtube.yt", None):
            extractor = YouTubeExtractor()
            with pytest.raises(Exception) as excinfo:
                extractor.extract("https://youtube.com/watch?v=test")
            assert "yt-dlp" in str(excinfo.value)

    def test_youtube_extractor_extract_calls_ydl(self, mocker):
        """extract() calls yt-dlp and returns MediaInfo."""
        mock_raw = {
            "id": "abc123",
            "title": "Test Video",
            "webpage_url": "https://youtube.com/watch?v=abc123",
            "duration": 240,
            "uploader": "Test Channel",
            "artist": "Test Artist",
            "track": "Test Track",
            "album": "Test Album",
            "description": "A test video",
            "thumbnail": "https://img.youtube.com/vi/abc123/maxresdefault.jpg",
            "thumbnails": [{"url": "https://img.youtube.com/vi/abc123/maxresdefault.jpg"}],
        }
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = mock_raw
        mock_ydl.__enter__.return_value = mock_ydl
        mock_ydl_cls = MagicMock(return_value=mock_ydl)

        with patch("tetodl.extractors.youtube.yt") as mock_yt:
            mock_yt.YoutubeDL = mock_ydl_cls
            extractor = YouTubeExtractor()
            result = extractor.extract("https://youtube.com/watch?v=abc123")

        assert isinstance(result, MediaInfo)
        assert result.id == "abc123"
        assert result.title == "Test Video"
        assert result.duration == 240
        assert result.uploader == "Test Channel"
        assert result.artist == "Test Artist"
        assert result.track == "Test Track"
        assert result.album == "Test Album"
        assert result.is_playlist is False
        assert result.entries is None
