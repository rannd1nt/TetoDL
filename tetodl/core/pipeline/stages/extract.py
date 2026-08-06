import tetodl.core.sources  # noqa: F401 — auto-registers extractors
from tetodl.core.domain.models import PipelineContext
from tetodl.core.domain.step import PipelineError, PipelineStep
from tetodl.core.extractor import resolve_extractor
from tetodl.utils.tracer import trace, traced


class ExtractStep(PipelineStep[PipelineContext, PipelineContext]):
    @trace
    def __call__(self, ctx: PipelineContext) -> PipelineContext:
        try:
            extractor = resolve_extractor(ctx.url)
        except PipelineError as exc:
            ctx.error = str(exc)
            return ctx

        try:
            ctx.media_info = extractor.extract(ctx.url)
        except PipelineError as exc:
            with traced(f'extract failed — {exc}'):
                ctx.error = str(exc)

        return ctx
