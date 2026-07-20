import pytest

from tetodl.daemon.models import DownloadRequest, PreviewRequest


class TestDownloadRequest:
    """Tests for daemon DownloadRequest model."""

    def test_download_request_defaults(self):
        """All optional fields default to None or their documented defaults."""
        req = DownloadRequest()
        assert req.url is None
        assert req.search_query is None
        assert req.search_limit == 5
        assert req.title is None
        assert req.audio_only is False
        assert req.video_only is False
        assert req.thumbnail_only is False
        assert req.format is None
        assert req.resolution is None
        assert req.codec is None
        assert req.async_mode is False
        assert req.cut_time is None
        assert req.items is None
        assert req.group is None
        assert req.m3u is False
        assert req.smart_cover is False
        assert req.no_cover is False
        assert req.force_crop is False
        assert req.lyrics is False
        assert req.romaji is False
        assert req.share is False
        assert req.share_temp is False

    def test_download_request_with_fields(self):
        """Fields populate correctly when provided."""
        req = DownloadRequest(
            url="https://youtube.com/watch?v=test",
            search_query="test song",
            search_limit=10,
            title="My Download",
            audio_only=True,
            video_only=False,
            thumbnail_only=False,
            format="mp3",
            resolution="1080p",
            codec="h264",
            async_mode=True,
            cut_time="01:30-02:00",
            items="1,2,5-7",
            group="My Folder",
            m3u=True,
            smart_cover=True,
            no_cover=False,
            force_crop=True,
            lyrics=True,
            romaji=True,
            share=True,
            share_temp=False,
        )
        assert req.url == "https://youtube.com/watch?v=test"
        assert req.search_query == "test song"
        assert req.search_limit == 10
        assert req.title == "My Download"
        assert req.audio_only is True
        assert req.format == "mp3"
        assert req.resolution == "1080p"
        assert req.codec == "h264"
        assert req.async_mode is True
        assert req.cut_time == "01:30-02:00"
        assert req.items == "1,2,5-7"
        assert req.group == "My Folder"
        assert req.m3u is True
        assert req.smart_cover is True
        assert req.force_crop is True
        assert req.lyrics is True
        assert req.romaji is True
        assert req.share is True
        assert req.group == "My Folder"


class TestPreviewRequest:
    """Tests for daemon PreviewRequest model."""

    def test_preview_request_requires_url(self):
        """url is a required field."""
        req = PreviewRequest(url="https://youtube.com/watch?v=test")
        assert req.url == "https://youtube.com/watch?v=test"
