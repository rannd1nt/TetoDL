from unittest.mock import MagicMock, patch

from tetodl.core.models import AppConfig, PipelineContext
from tetodl.pipeline.pipeline import MediaPipeline
from tetodl.utils.console import console


class TestMediaPipeline:
    """Tests for the MediaPipeline orchestrator."""

    def test_pipeline_run_with_empty_context(self, app_config: AppConfig, tetodl_trace):
        """Returns the same context when no steps are executed."""
        pipeline = MediaPipeline(config=app_config)
        ctx = pipeline.run(
            url="https://example.com/video",
            target_dir="/tmp",
        )
        assert isinstance(ctx, PipelineContext)
        assert ctx.url == "https://example.com/video"

    def test_pipeline_instantiates_steps(self, app_config: AppConfig, tetodl_trace):
        """Default step list contains all 6 steps."""
        console.debug("instantiating all 6 pipeline steps")
        pipeline = MediaPipeline(config=app_config)

        with patch(
            "tetodl.pipeline.pipeline.ExtractStep"
        ) as mock_extract, patch(
            "tetodl.pipeline.pipeline.ClassifyStep"
        ) as mock_classify, patch(
            "tetodl.pipeline.pipeline.DownloadStep"
        ) as mock_download, patch(
            "tetodl.pipeline.pipeline.CoverStep"
        ) as mock_cover, patch(
            "tetodl.pipeline.pipeline.LyricsStep"
        ) as mock_lyrics, patch(
            "tetodl.pipeline.pipeline.FinalizeStep"
        ) as mock_finalize:
            def passthrough(ctx):
                return ctx

            for m in (
                mock_extract,
                mock_classify,
                mock_download,
                mock_cover,
                mock_lyrics,
                mock_finalize,
            ):
                instance = m.return_value
                instance.side_effect = passthrough

            ctx = pipeline.run(
                url="https://youtube.com/watch?v=test",
                target_dir="/tmp",
            )

            mock_extract.assert_called_once()
            mock_classify.assert_called_once()
            mock_download.assert_called_once()
            mock_cover.assert_called_once()
            mock_lyrics.assert_called_once()
            mock_finalize.assert_called_once()
            assert isinstance(ctx, PipelineContext)

    def test_pipeline_short_circuits_on_extract_error(
        self, app_config: AppConfig, tetodl_trace,
    ):
        """Returns early when ExtractStep sets ctx.error."""
        console.debug("simulating extract failure")
        pipeline = MediaPipeline(config=app_config)

        with patch(
            "tetodl.pipeline.pipeline.ExtractStep"
        ) as mock_extract:
            err_ctx = PipelineContext(
                config=app_config,
                url="https://youtube.com/watch?v=test",
                target_dir="/tmp",
                error="extraction failed",
            )
            instance = mock_extract.return_value
            instance.side_effect = lambda ctx: err_ctx

            ctx = pipeline.run(
                url="https://youtube.com/watch?v=test",
                target_dir="/tmp",
            )
            assert ctx.error == "extraction failed"

    def test_pipeline_short_circuits_on_existing_result(
        self, app_config: AppConfig, tetodl_trace,
    ):
        """Returns early when ClassifyStep finds an existing result."""
        console.debug("checking short-circuit on existing result")
        from tetodl.core.models import Classification, DownloadResult

        pipeline = MediaPipeline(config=app_config)

        with patch(
            "tetodl.pipeline.pipeline.ExtractStep"
        ) as mock_extract, patch(
            "tetodl.pipeline.pipeline.ClassifyStep"
        ) as mock_classify:
            extract_instance = mock_extract.return_value
            extract_instance.__call__ = MagicMock(
                side_effect=lambda ctx: ctx,
            )

            existing = DownloadResult(success=True, file_path="/tmp/song.mp3")
            classify_ctx = PipelineContext(
                config=app_config,
                url="https://youtube.com/watch?v=test",
                target_dir="/tmp",
                classification=Classification(existing_result=existing),
            )
            classify_instance = mock_classify.return_value
            classify_instance.__call__ = MagicMock(return_value=classify_ctx)

            ctx = pipeline.run(
                url="https://youtube.com/watch?v=test",
                target_dir="/tmp",
            )
            assert ctx.classification is not None
            assert ctx.classification.existing_result is not None
