import os
from unittest.mock import MagicMock, patch


from tetodl.core.models import AppConfig, MediaInfo, PipelineContext
from tetodl.pipeline.steps.download import DownloadStep


class TestDownloadStep:
    """Tests for DownloadStep."""

    def test_download_step_no_media_info(self, pipeline_ctx: PipelineContext):
        """Sets error when ctx.media_info is None."""
        step = DownloadStep()
        ctx = pipeline_ctx
        ctx.media_info = None
        result = step(ctx)
        assert result.error is not None
        assert "No media info" in result.error

    def test_download_step_no_ytdlp(self, pipeline_ctx: PipelineContext):
        """Sets error when yt-dlp is not available."""
        step = DownloadStep()
        ctx = pipeline_ctx
        ctx.media_info = MediaInfo(
            id="abc123",
            title="Test Song",
            url="https://youtube.com/watch?v=abc123",
        )
        with patch("tetodl.pipeline.steps.download.yt", None):
            result = step(ctx)
        assert result.error is not None
        assert "yt-dlp" in result.error

    def test_download_step_creates_download_dir(self, tmp_path, app_config: AppConfig):
        """Creates target directory if it does not exist."""
        target = tmp_path / "downloads" / "subdir"
        assert not target.exists()

        from tetodl.pipeline.steps.download import DownloadStep

        step = DownloadStep()
        info = MediaInfo(
            id="abc123",
            title="Test Song",
            url="https://youtube.com/watch?v=abc123",
        )
        ctx = PipelineContext(
            config=app_config,
            url="https://youtube.com/watch?v=abc123",
            target_dir=str(target),
            media_info=info,
            media_type="audio",
        )

        with patch("tetodl.pipeline.steps.download.yt") as mock_yt:
            mock_ydl = MagicMock()
            mock_yt.YoutubeDL.return_value.__enter__.return_value = mock_ydl
            mock_ydl.download.return_value = None

            fake_path = os.path.join(str(target), "Test Song.m4a")
            os.makedirs(str(target), exist_ok=True)
            with open(fake_path, "w") as f:
                f.write("fake audio")

            result = step(ctx)

        assert result.downloaded_file is not None
        assert result.downloaded_file.path == os.path.abspath(fake_path)

    def test_download_step_cleanup_on_failure(
        self, tmp_path, app_config: AppConfig,
    ):
        """Cleans up partial files on exception."""
        target = tmp_path / "downloads"
        target.mkdir(parents=True, exist_ok=True)

        step = DownloadStep()
        info = MediaInfo(
            id="abc123",
            title="Test Song",
            url="https://youtube.com/watch?v=abc123",
        )
        ctx = PipelineContext(
            config=app_config,
            url="https://youtube.com/watch?v=abc123",
            target_dir=str(target),
            media_info=info,
            media_type="audio",
        )

        part_file = target / "Test Song.mp4.part"
        part_file.write_text("partial data")

        with patch("tetodl.pipeline.steps.download.yt") as mock_yt:
            mock_ydl = MagicMock()
            mock_yt.YoutubeDL.return_value.__enter__.return_value = mock_ydl
            mock_ydl.download.side_effect = Exception("download failed")

            result = step(ctx)

        assert result.error is not None
        assert not part_file.exists()
