from tetodl.core.domain.models import AppConfig, PipelineContext
from tetodl.core.pipeline.stages.classify import ClassifyStep
from tetodl.core.pipeline.stages.cover import CoverStep
from tetodl.core.pipeline.stages.download import DownloadStep
from tetodl.core.pipeline.stages.extract import ExtractStep
from tetodl.core.pipeline.stages.finalize import FinalizeStep
from tetodl.core.pipeline.stages.lyrics import LyricsStep
from tetodl.utils.console import console
from tetodl.utils.i18n_keys import Keys
from tetodl.utils.tracer import trace, traced


class MediaPipeline:
    def __init__(self, config: AppConfig) -> None:
        self._config = config

    @trace
    def run(self, url: str, target_dir: str, **ctx_kw) -> PipelineContext:
        ctx = PipelineContext(
            config=self._config,
            url=url,
            target_dir=target_dir,
            **ctx_kw,
        )

        ctx = ExtractStep()(ctx)
        if ctx.error:
            with traced(f'extract failed — {ctx.error}'):
                console.err(Keys.download.youtube.error_downloading(
                    type=ctx.media_type, error=ctx.error,
                ))
                return ctx

        ctx = ClassifyStep()(ctx)
        if ctx.classification and ctx.classification.existing_result:
            return ctx

        self._show_start(ctx)

        with traced('starting download'):
            ctx = DownloadStep()(ctx)
        if ctx.error and ctx.downloaded_file is None:
            with traced(f'download failed — {ctx.error}'):
                return ctx

        with traced('processing cover'):
            ctx = CoverStep()(ctx)

        with traced('processing lyrics'):
            ctx = LyricsStep()(ctx)

        ctx = FinalizeStep()(ctx)
        return ctx

    def _show_start(self, ctx: PipelineContext) -> None:
        label = ctx.media_type
        if ctx.media_type == "video":
            label = f"video ({self._config.max_video_resolution})"

        if self._config.simple_mode:
            console.proc(Keys.download.youtube.simple_mode_start(
                type=label, path=ctx.target_dir,
            ))
        else:
            console.proc(Keys.download.youtube.start_download(
                type=label, path=ctx.target_dir,
            ))
