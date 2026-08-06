from tetodl.core.domain.models import (
    AppConfig,
    DownloadedFile,
    MediaInfo,
    PipelineContext,
)
from tetodl.core.pipeline.stages.cover import CoverStep


class TestCoverStep:
    """Tests for CoverStep."""

    def test_skip_cover_when_cover_mode_false(self, app_config: AppConfig):
        """Returns ctx unchanged when cover_mode is False."""
        step = CoverStep()
        info = MediaInfo(
            id="abc123",
            title="Test Song",
            url="https://youtube.com/watch?v=abc123",
        )
        dl_file = DownloadedFile(
            path="/tmp/test.mp3", container="mp3", title="Test Song",
        )
        ctx = PipelineContext(
            config=app_config,
            url="https://youtube.com/watch?v=abc123",
            target_dir="/tmp",
            media_info=info,
            downloaded_file=dl_file,
            media_type="audio",
            cover_mode=False,
        )
        result = step(ctx)
        assert result is ctx
        assert result.cover_result is None

    def test_skip_cover_for_video(self, app_config: AppConfig):
        """Returns ctx unchanged when media_type is video."""
        step = CoverStep()
        info = MediaInfo(
            id="abc123",
            title="Test Video",
            url="https://youtube.com/watch?v=abc123",
        )
        dl_file = DownloadedFile(
            path="/tmp/test.mp4", container="mp4", title="Test Video",
        )
        ctx = PipelineContext(
            config=app_config,
            url="https://youtube.com/watch?v=abc123",
            target_dir="/tmp",
            media_info=info,
            downloaded_file=dl_file,
            media_type="video",
            cover_mode=True,
        )
        result = step(ctx)
        assert result is ctx
        assert result.cover_result is None

    def test_cover_step_with_fallback_thumbnail(
        self, tmp_path, app_config: AppConfig, mocker,
    ):
        """Processes cover via YouTube thumbnail fallback."""
        step = CoverStep()
        info = MediaInfo(
            id="abc123",
            title="Test Song",
            url="https://youtube.com/watch?v=abc123",
            thumbnail="https://img.youtube.com/vi/abc123/maxresdefault.jpg",
            uploader="Test Artist - Topic",
            track="Test Song",
        )
        dl_file = DownloadedFile(
            path=str(tmp_path / "song.mp3"),
            container="mp3",
            title="Test Song",
            artist="Test Artist",
            info=info,
        )
        ctx = PipelineContext(
            config=app_config,
            url="https://youtube.com/watch?v=abc123",
            target_dir=str(tmp_path),
            media_info=info,
            downloaded_file=dl_file,
            media_type="audio",
            cover_mode=True,
        )

        mocker.patch.object(step._cover_service, "fetch", return_value=b"fake_image_data")
        mocker.patch.object(step._cover_service, "process", return_value=str(tmp_path / "abc123.jpg"))

        result = step(ctx)
        assert result is ctx
