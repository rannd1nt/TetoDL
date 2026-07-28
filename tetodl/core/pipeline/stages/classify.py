from tetodl.core.domain.models import Classification, DownloadResult, MediaInfo, PipelineContext
from tetodl.core.domain.registry import registry
from tetodl.core.domain.step import PipelineStep
from tetodl.utils.console import console
from tetodl.utils.i18n_keys import Keys
from tetodl.utils.tracer import trace, traced


class ClassifyStep(PipelineStep[PipelineContext, PipelineContext]):
    def __init__(self, skip_existing: bool = True) -> None:
        self._skip_existing = skip_existing

    @trace
    def __call__(self, ctx: PipelineContext) -> PipelineContext:
        if not ctx.media_info:
            return ctx

        info = ctx.media_info
        is_playlist = info.is_playlist or bool(info.entries)

        if is_playlist:
            ctx.classification = Classification(is_playlist=True)
            return ctx

        should_skip = ctx.media_type == "audio" or ctx.config.skip_existing_files
        if self._skip_existing and should_skip:
            existing = self._check_registry(info, ctx)
            if existing is not None:
                ctx.classification = Classification(existing_result=existing)
                return ctx

        ctx.classification = Classification()
        return ctx

    def _check_registry(
        self,
        info: MediaInfo,
        ctx: PipelineContext,
    ) -> DownloadResult | None:
        video_id = info.id
        if not video_id:
            return None

        exists, metadata = registry.check_existing(
            video_id,
            ctx.media_type,
            ctx.target_dir,
        )
        if not exists:
            return None

        with traced('found in registry'):
            console.ok(Keys.download.youtube.file_exists)
            if metadata:
                console.warn(Keys.download.youtube.exists_title(
                    title=metadata.get("title", ""),
                ))
                console.warn(Keys.download.youtube.exists_path(
                    path=metadata.get("file_path", ""),
                ))
            return DownloadResult(
                success=True,
                file_path=metadata.get("file_path") if metadata else None,
                skipped=True,
            )
