from unittest.mock import MagicMock


from tetodl.core.models import (
    AppConfig,
    DownloadedFile,
    MediaInfo,
    PipelineContext,
)
from tetodl.pipeline.steps.cover import CoverStep


class TestCoverStep:
    """Tests for CoverStep."""

    def test_skip_cover_when_no_media(self, pipeline_ctx: PipelineContext):
        """Returns ctx unchanged when no media_info or downloaded_file."""
        step = CoverStep()
        ctx = pipeline_ctx
        ctx.media_info = None
        ctx.downloaded_file = None
        result = step(ctx)
        assert result is ctx
        assert result.cover_result is None

    def test_skip_cover_when_no_cover_mode(self, app_config: AppConfig):
        """Returns ctx unchanged when no_cover_mode is enabled."""
        config = app_config.model_copy(update={"no_cover_mode": True})
        step = CoverStep()
        info = MediaInfo(
            id="abc123",
            title="Test Song",
            url="https://youtube.com/watch?v=abc123",
        )
        dl_file = DownloadedFile(
            path="/tmp/test.mp3",
            container="mp3",
            title="Test Song",
        )
        ctx = PipelineContext(
            config=config,
            url="https://youtube.com/watch?v=abc123",
            target_dir="/tmp",
            media_info=info,
            downloaded_file=dl_file,
            media_type="audio",
        )
        result = step(ctx)
        assert result is ctx
        assert result.cover_result is None

    def test_skip_cover_for_video(self, app_config: AppConfig):
        """Returns ctx unchanged when media_type is video."""
        config = app_config.model_copy(update={"smart_cover_mode": True})
        step = CoverStep()
        info = MediaInfo(
            id="abc123",
            title="Test Video",
            url="https://youtube.com/watch?v=abc123",
        )
        dl_file = DownloadedFile(
            path="/tmp/test.mp4",
            container="mp4",
            title="Test Video",
        )
        ctx = PipelineContext(
            config=config,
            url="https://youtube.com/watch?v=abc123",
            target_dir="/tmp",
            media_info=info,
            downloaded_file=dl_file,
            media_type="video",
        )
        result = step(ctx)
        assert result is ctx
        assert result.cover_result is None

    def test_skip_cover_when_not_youtube_music_and_not_smart_cover(
        self, app_config: AppConfig,
    ):
        """Returns ctx unchanged when not YT Music and smart cover is off."""
        config = app_config.model_copy(
            update={"smart_cover_mode": False, "no_cover_mode": False},
        )
        step = CoverStep()
        info = MediaInfo(
            id="abc123",
            title="Test Song",
            url="https://youtube.com/watch?v=abc123",
        )
        dl_file = DownloadedFile(
            path="/tmp/test.mp3",
            container="mp3",
            title="Test Song",
        )
        ctx = PipelineContext(
            config=config,
            url="https://youtube.com/watch?v=abc123",
            target_dir="/tmp",
            media_info=info,
            downloaded_file=dl_file,
            media_type="audio",
            is_youtube_music=False,
        )
        result = step(ctx)
        assert result is ctx
        assert result.cover_result is None

    def test_cover_step_with_fallback_thumbnail(
        self, tmp_path, app_config: AppConfig, mocker,
    ):
        """Processes cover via YouTube thumbnail fallback."""
        config = app_config.model_copy(
            update={"smart_cover_mode": True, "no_cover_mode": False},
        )
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
            config=config,
            url="https://youtube.com/watch?v=abc123",
            target_dir=str(tmp_path),
            media_info=info,
            downloaded_file=dl_file,
            media_type="audio",
            is_youtube_music=True,
        )

        thumb_path = tmp_path / "abc123.jpg"
        thumb_path.write_text("fake image")

        mocker.patch(
            "tetodl.pipeline.steps.cover.requests.get",
            return_value=MagicMock(status_code=200, content=b"fake image"),
        )
        mocker.patch(
            "tetodl.pipeline.steps.cover.crop_thumbnail_to_square",
        )
        mocker.patch(
            "tetodl.pipeline.steps.cover.embed_metadata",
            return_value=True,
        )
        mocker.patch(
            "tetodl.pipeline.steps.cover.fetcher.fetch_metadata",
            return_value=None,
        )

        result = step(ctx)
        assert result.cover_result is not None
        assert result.cover_result.source == "youtube"
