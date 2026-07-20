from unittest.mock import MagicMock, patch

import pytest

from tetodl.core.models import (
    AppConfig,
    DownloadedFile,
    MediaInfo,
    PipelineContext,
)
from tetodl.pipeline.steps.finalize import FinalizeStep


class TestFinalizeStep:
    """Tests for FinalizeStep."""

    def test_skip_when_no_downloaded_file(self, app_config: AppConfig):
        """Returns ctx unchanged when downloaded_file is None."""
        step = FinalizeStep()
        ctx = PipelineContext(
            config=app_config,
            url="https://youtube.com/watch?v=test",
            target_dir="/tmp",
        )
        result = step(ctx)
        assert result is ctx

    def test_cache_called(self, mocker):
        """Verifies cache_metadata is called with correct data."""
        mock_cache = mocker.patch("tetodl.pipeline.steps.finalize.cache_metadata")
        mock_history = mocker.patch("tetodl.pipeline.steps.finalize.add_to_history")
        mock_scanner = mocker.patch("tetodl.utils.media_scanner.scan_media_files")

        config = AppConfig(media_scanner_enabled=True)
        info = MediaInfo(
            id="abc123",
            title="Test Song",
            url="https://youtube.com/watch?v=abc123",
            uploader="Test Artist",
            artist="Test Artist",
            album="Test Album",
            track="Test Song",
            thumbnails=[{"url": "https://img.youtube.com/vi/abc123/default.jpg"}],
        )
        dl_file = DownloadedFile(
            path="/tmp/Test Song.mp3",
            container="mp3",
            title="Test Song",
            artist="Test Artist",
            duration=240,
            info=info,
        )
        ctx = PipelineContext(
            config=config,
            url="https://youtube.com/watch?v=abc123",
            target_dir="/tmp",
            media_info=info,
            downloaded_file=dl_file,
            media_type="audio",
            is_youtube_music=True,
        )

        step = FinalizeStep()
        result = step(ctx)

        assert result is ctx
        mock_cache.assert_called_once_with(
            "https://youtube.com/watch?v=abc123",
            {
                "title": "Test Song",
                "duration": 240,
                "uploader": "Test Artist",
                "artist": "Test Artist",
                "album": "Test Album",
                "track": "Test Song",
                "thumbnails": [{"url": "https://img.youtube.com/vi/abc123/default.jpg"}],
            },
        )
        mock_history.assert_called_once()
        mock_scanner.assert_called_once()

    def test_history_args_video(self, mocker):
        """Verifies add_to_history receives correct args for video."""
        mocker.patch("tetodl.pipeline.steps.finalize.cache_metadata")
        mock_history = mocker.patch("tetodl.pipeline.steps.finalize.add_to_history")
        mocker.patch("tetodl.utils.media_scanner.scan_media_files")

        config = AppConfig(media_scanner_enabled=False)
        info = MediaInfo(
            id="abc123",
            title="Test Video",
            url="https://youtube.com/watch?v=abc123",
            uploader="Video Creator",
        )
        dl_file = DownloadedFile(
            path="/tmp/Test Video.mp4",
            container="mp4",
            title="Test Video",
            duration=300,
            info=info,
        )
        ctx = PipelineContext(
            config=config,
            url="https://youtube.com/watch?v=abc123",
            target_dir="/tmp",
            media_info=info,
            downloaded_file=dl_file,
            media_type="video",
            download_type_label="Download",
        )

        step = FinalizeStep()
        step(ctx)

        mock_history.assert_called_once()
        call_kwargs = mock_history.call_args[1]
        assert call_kwargs["content_type"] == "video"
        assert call_kwargs["title"] == "Test Video"
        assert call_kwargs["duration"] == 300
