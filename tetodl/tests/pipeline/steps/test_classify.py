from unittest.mock import MagicMock, patch

import pytest

from tetodl.core.models import (
    AppConfig,
    Classification,
    DownloadResult,
    MediaInfo,
    PipelineContext,
)
from tetodl.pipeline.steps.classify import ClassifyStep


class TestClassifyStep:
    """Tests for ClassifyStep."""

    def test_classify_step_returns_ctx_unchanged_when_no_media_info(
        self,
    ):
        """Returns ctx unchanged when ctx.media_info is None."""
        config = AppConfig()
        ctx = PipelineContext(
            config=config,
            url="https://youtube.com/watch?v=test",
            target_dir="/tmp",
        )
        step = ClassifyStep()
        result = step(ctx)
        assert result is ctx
        assert result.classification is None

    def test_classify_step_playlist_detection(self, app_config: AppConfig):
        """Sets classification.is_playlist when media_info is a playlist."""
        info = MediaInfo(
            id="pl123",
            title="Playlist",
            url="https://youtube.com/playlist?list=pl123",
            entries=[
                MediaInfo(id="v1", title="Song 1", url="https://youtube.com/watch?v=v1"),
                MediaInfo(id="v2", title="Song 2", url="https://youtube.com/watch?v=v2"),
            ],
            is_playlist=True,
        )
        ctx = PipelineContext(
            config=app_config,
            url="https://youtube.com/playlist?list=pl123",
            target_dir="/tmp",
            media_info=info,
        )
        step = ClassifyStep()
        result = step(ctx)
        assert result.classification is not None
        assert result.classification.is_playlist is True
        assert result.classification.existing_result is None

    def test_classify_step_checks_registry_for_audio(
        self, app_config: AppConfig, mocker,
    ):
        """Checks registry for audio and returns existing result when found."""
        mock_registry = mocker.patch("tetodl.pipeline.steps.classify.registry")
        mock_registry.check_existing.return_value = (
            True,
            {"title": "Existing Song", "file_path": "/tmp/existing.mp3"},
        )

        info = MediaInfo(
            id="abc123",
            title="Test Song",
            url="https://youtube.com/watch?v=abc123",
        )
        ctx = PipelineContext(
            config=app_config,
            url="https://youtube.com/watch?v=abc123",
            target_dir="/tmp",
            media_info=info,
            media_type="audio",
        )
        step = ClassifyStep()
        result = step(ctx)
        assert result.classification is not None
        assert result.classification.existing_result is not None
        assert result.classification.existing_result.skipped is True
        mock_registry.check_existing.assert_called_once_with(
            "abc123", "audio", "/tmp",
        )

    def test_classify_step_skips_registry_for_video_when_disabled(
        self, app_config: AppConfig, mocker,
    ):
        """Skips registry check for video when skip_existing_files is False."""
        config = app_config.model_copy(update={"skip_existing_files": False})
        mock_registry = mocker.patch("tetodl.pipeline.steps.classify.registry")

        info = MediaInfo(
            id="abc123",
            title="Test Video",
            url="https://youtube.com/watch?v=abc123",
        )
        ctx = PipelineContext(
            config=config,
            url="https://youtube.com/watch?v=abc123",
            target_dir="/tmp",
            media_info=info,
            media_type="video",
        )
        step = ClassifyStep()
        result = step(ctx)
        assert result.classification is not None
        assert result.classification.existing_result is None
        mock_registry.check_existing.assert_not_called()
