from tetodl.core.cover import CoverQuery, CoverService
from tetodl.core.domain.models import CoverResult, LyricsMetadata, PipelineContext
from tetodl.core.domain.step import PipelineStep
from tetodl.core.pipeline.metadata import resolve_artist_title
from tetodl.utils.tracer import trace


class ResolveEnrichmentStep(PipelineStep[PipelineContext, PipelineContext]):
    _cover_service = CoverService()

    @trace
    def __call__(self, ctx: PipelineContext) -> PipelineContext:
        if not any([ctx.cover_mode, ctx.metadata_mode, ctx.lyrics_mode or ctx.config.lyrics_mode]):
            return ctx

        info = ctx.media_info
        if info is None:
            return ctx

        artist, title = resolve_artist_title(info, ctx=ctx)
        if not artist and not title:
            return ctx

        cover_data = self._cover_service.search(CoverQuery(artist=artist, title=title))
        ctx.enrichment_data = cover_data

        if cover_data and ctx.cover_result is None:
            ctx.cover_result = CoverResult(
                thumbnail_path="",
                metadata=LyricsMetadata(
                    artist=cover_data.artist,
                    title=cover_data.title,
                    album=cover_data.album,
                    album_artist=cover_data.album_artist,
                    genre=cover_data.genre,
                    year=cover_data.year,
                    composer=cover_data.composer,
                    cover_url=cover_data.url,
                ),
                source="smart",
                cropped=False,
            )
        return ctx
