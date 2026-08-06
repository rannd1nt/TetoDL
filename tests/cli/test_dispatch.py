

from tetodl.core.domain.models import DownloadResult, DownloadSession


class TestDispatch:
    """Tests for CLI dispatch module."""

    def _import_modules(self):
        """Ensure submodules are loaded so mocker.patch can resolve dotted paths."""
        import tetodl.ui.cli.dispatch  # noqa: F401
        import tetodl.core.domain.config  # noqa: F401
        import tetodl.core.resolver  # noqa: F401
        import tetodl.core.cover  # noqa: F401

    def test_execute_download_audio(self, mocker):
        self._import_modules()
        """execute_download calls download_audio_youtube for audio media_type."""
        mock_dl = mocker.patch(
            "tetodl.ui.cli.dispatch.download_audio_youtube",
            return_value=DownloadResult(success=True, file_path="/tmp/song.mp3"),
        )
        mock_config = mocker.patch("tetodl.ui.cli.dispatch.load_app_config")
        mock_resolver = mocker.patch("tetodl.ui.cli.dispatch.ConfigResolver")
        mock_resolver.return_value.resolve.return_value = mock_config.return_value

        from tetodl.ui.cli.dispatch import execute_download

        session = DownloadSession(
            url="https://music.youtube.com/watch?v=test",
            media_type="audio",
        )
        result = execute_download(session)

        mock_dl.assert_called_once()
        assert result.success is True

    def test_execute_download_video(self, mocker):
        self._import_modules()
        """execute_download calls download_video_youtube for video media_type."""
        mock_dl = mocker.patch(
            "tetodl.ui.cli.dispatch.download_video_youtube",
            return_value=DownloadResult(success=True, file_path="/tmp/video.mp4"),
        )
        mock_config = mocker.patch("tetodl.ui.cli.dispatch.load_app_config")
        mock_resolver = mocker.patch("tetodl.ui.cli.dispatch.ConfigResolver")
        mock_resolver.return_value.resolve.return_value = mock_config.return_value

        from tetodl.ui.cli.dispatch import execute_download

        session = DownloadSession(
            url="https://youtube.com/watch?v=test",
            media_type="video",
        )
        result = execute_download(session)

        mock_dl.assert_called_once()
        assert result.success is True

    def test_execute_download_thumbnail(self, mocker):
        self._import_modules()
        """execute_download calls CoverService.download for thumbnail."""
        mock_thumb = mocker.patch(
            "tetodl.ui.cli.dispatch.CoverService.download",
            return_value=DownloadResult(success=True, file_path="/tmp/thumb.jpg"),
        )
        mock_config = mocker.patch("tetodl.ui.cli.dispatch.load_app_config")
        mock_resolver = mocker.patch("tetodl.ui.cli.dispatch.ConfigResolver")
        mock_resolver.return_value.resolve.return_value = mock_config.return_value

        from tetodl.ui.cli.dispatch import execute_download

        session = DownloadSession(
            url="https://youtube.com/watch?v=test",
            media_type="thumbnail",
        )
        result = execute_download(session)

        mock_thumb.assert_called_once()
        args, kwargs = mock_thumb.call_args
        assert args[0] == "https://youtube.com/watch?v=test"
        assert kwargs.get("target_format") == "jpg"
        assert result.success is True

    def test_execute_download_empty_url(self, mocker):
        self._import_modules()
        """Returns failure result when URL is empty."""
        mock_config = mocker.patch("tetodl.ui.cli.dispatch.load_app_config")
        mock_resolver = mocker.patch("tetodl.ui.cli.dispatch.ConfigResolver")
        mock_resolver.return_value.resolve.return_value = mock_config.return_value

        from tetodl.ui.cli.dispatch import execute_download

        session = DownloadSession(url="", media_type="audio")
        result = execute_download(session)

        assert result.success is False

    def test_execute_download_cancelled(self, mocker):
        self._import_modules()
        """Handles KeyboardInterrupt gracefully."""
        mocker.patch(
            "tetodl.ui.cli.dispatch.download_audio_youtube",
            side_effect=KeyboardInterrupt(),
        )
        mock_config = mocker.patch("tetodl.ui.cli.dispatch.load_app_config")
        mock_resolver = mocker.patch("tetodl.ui.cli.dispatch.ConfigResolver")
        mock_resolver.return_value.resolve.return_value = mock_config.return_value

        from tetodl.ui.cli.dispatch import execute_download

        session = DownloadSession(
            url="https://music.youtube.com/watch?v=test",
            media_type="audio",
        )
        result = execute_download(session)

        assert result.success is False
        assert result.cancelled is True

    def test_execute_download_spotify(self, mocker):
        self._import_modules()
        """execute_download calls download_spotify when is_spotify is True."""
        mock_spotify = mocker.patch(
            "tetodl.ui.cli.dispatch.download_spotify",
            return_value=DownloadResult(success=True, file_path="/music/song.mp3"),
        )
        mock_config = mocker.patch("tetodl.ui.cli.dispatch.load_app_config")
        mock_resolver = mocker.patch("tetodl.ui.cli.dispatch.ConfigResolver")
        mock_resolver.return_value.resolve.return_value = mock_config.return_value

        from tetodl.ui.cli.dispatch import execute_download

        session = DownloadSession(
            url="https://open.spotify.com/track/abc",
            media_type="audio",
            is_spotify=True,
        )
        result = execute_download(session)

        mock_spotify.assert_called_once_with(
            "https://open.spotify.com/track/abc",
            session=session,
            config=mock_config.return_value,
        )
        assert result.success is True
