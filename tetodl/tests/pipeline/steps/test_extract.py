from unittest.mock import MagicMock, patch

from tetodl.core.models import MediaInfo, PipelineContext
from tetodl.core.step import PipelineError
from tetodl.pipeline.steps.extract import ExtractStep


class TestExtractStep:
    """Tests for ExtractStep."""

    def test_extract_step_requires_media_info(self, pipeline_ctx: PipelineContext):
        """Returns ctx unchanged when resolve_extractor raises PipelineError."""
        step = ExtractStep()

        with patch(
            "tetodl.pipeline.steps.extract.resolve_extractor",
            side_effect=PipelineError("no extractor", "extract"),
        ):
            result = step(pipeline_ctx)

        assert result.error is not None
        assert "no extractor" in result.error

    def test_extract_step_success(self, pipeline_ctx: PipelineContext):
        """Populates media_info when extraction succeeds."""
        step = ExtractStep()
        fake_media = MediaInfo(
            id="abc123",
            title="Test Song",
            url="https://youtube.com/watch?v=abc123",
            duration=240,
            uploader="Test Artist",
        )
        mock_extractor = MagicMock()
        mock_extractor.extract.return_value = fake_media

        with patch(
            "tetodl.pipeline.steps.extract.resolve_extractor",
            return_value=mock_extractor,
        ):
            result = step(pipeline_ctx)

        assert result.media_info is not None
        assert result.media_info.id == "abc123"
        assert result.media_info.title == "Test Song"
        assert result.error is None

    def test_extract_step_extract_failure(self, pipeline_ctx: PipelineContext):
        """Sets ctx.error when the extractor raises PipelineError."""
        step = ExtractStep()
        mock_extractor = MagicMock()
        mock_extractor.extract.side_effect = PipelineError(
            "extraction failed",
            "extract",
        )

        with patch(
            "tetodl.pipeline.steps.extract.resolve_extractor",
            return_value=mock_extractor,
        ):
            result = step(pipeline_ctx)

        assert result.error is not None
        assert "extraction failed" in result.error
        assert result.media_info is None
