from unittest.mock import MagicMock, patch

import pytest

from tetodl.core.models import DownloadResult, DownloadSession


class TestDispatch:
    """Tests for CLI dispatch module."""

    def test_execute_download_audio(self, mocker):
        """execute_download calls download_audio_youtube for audio media_type."""
        mock_dl = mocker.patch(
            "tetodl.cli.dispatch.download_audio_youtube",
            return_value=DownloadResult(success=True, file_path="/tmp/song.mp3"),
        )
        mock_config = mocker.patch("tetodl.cli.dispatch.load_app_config")
        mock_resolver = mocker.patch("tetodl.cli.dispatch.ConfigResolver")
        mock_resolver.return_value.resolve.return_value = mock_config.return_value

        from tetodl.cli.dispatch import execute_download

        session = DownloadSession(
            url="https://music.youtube.com/watch?v=test",
            media_type="audio",
        )
        result = execute_download(session)

        mock_dl.assert_called_once()
        assert result.success is True

    def test_execute_download_video(self, mocker):
        """execute_download calls download_video_youtube for video media_type."""
        mock_dl = mocker.patch(
            "tetodl.cli.dispatch.download_video_youtube",
            return_value=DownloadResult(success=True, file_path="/tmp/video.mp4"),
        )
        mock_config = mocker.patch("tetodl.cli.dispatch.load_app_config")
        mock_resolver = mocker.patch("tetodl.cli.dispatch.ConfigResolver")
        mock_resolver.return_value.resolve.return_value = mock_config.return_value

        from tetodl.cli.dispatch import execute_download

        session = DownloadSession(
            url="https://youtube.com/watch?v=test",
            media_type="video",
        )
        result = execute_download(session)

        mock_dl.assert_called_once()
        assert result.success is True

    def test_execute_download_thumbnail(self, mocker):
        """execute_download calls download_thumbnail_task for thumbnail."""
        mock_thumb = mocker.patch(
            "tetodl.cli.dispatch.download_thumbnail_task",
            return_value=DownloadResult(success=True, file_path="/tmp/thumb.jpg"),
        )
        mock_config = mocker.patch("tetodl.cli.dispatch.load_app_config")
        mock_resolver = mocker.patch("tetodl.cli.dispatch.ConfigResolver")
        mock_resolver.return_value.resolve.return_value = mock_config.return_value

        from tetodl.cli.dispatch import execute_download

        session = DownloadSession(
            url="https://youtube.com/watch?v=test",
            media_type="thumbnail",
        )
        result = execute_download(session)

        mock_thumb.assert_called_once_with(
            "https://youtube.com/watch?v=test",
            target_format="jpg",
        )
        assert result.success is True

    def test_execute_download_empty_url(self, mocker):
        """Returns failure result when URL is empty."""
        mock_config = mocker.patch("tetodl.cli.dispatch.load_app_config")
        mock_resolver = mocker.patch("tetodl.cli.dispatch.ConfigResolver")
        mock_resolver.return_value.resolve.return_value = mock_config.return_value

        from tetodl.cli.dispatch import execute_download

        session = DownloadSession(url="", media_type="audio")
        result = execute_download(session)

        assert result.success is False

    def test_execute_download_cancelled(self, mocker):
        """Handles KeyboardInterrupt gracefully."""
        mock_dl = mocker.patch(
            "tetodl.cli.dispatch.download_audio_youtube",
            side_effect=KeyboardInterrupt(),
        )
        mock_config = mocker.patch("tetodl.cli.dispatch.load_app_config")
        mock_resolver = mocker.patch("tetodl.cli.dispatch.ConfigResolver")
        mock_resolver.return_value.resolve.return_value = mock_config.return_value

        from tetodl.cli.dispatch import execute_download

        session = DownloadSession(
            url="https://music.youtube.com/watch?v=test",
            media_type="audio",
        )
        result = execute_download(session)

        assert result.success is False
        assert result.cancelled is True
