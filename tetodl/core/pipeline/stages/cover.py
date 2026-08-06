import os

from tetodl.core.cover import CoverData, CoverService
from tetodl.core.domain.models import CoverResult, LyricsMetadata, MediaInfo, PipelineContext
from tetodl.core.domain.step import PipelineStep
from tetodl.core.domain.tagger import embed_cover, embed_metadata_tags
from tetodl.core.pipeline.cleaners.title import clean_youtube_title
from tetodl.utils.console import console
from tetodl.utils.files import clean_temp_files
from tetodl.utils.i18n_keys import Keys
from tetodl.utils.tracer import trace, traced


def _basic_metadata(info: MediaInfo, ctx: PipelineContext | None = None) -> dict:
    # Priority 1 — Spotify direct metadata (most reliable)
    if ctx and ctx.spotify_title:
        album = (ctx.enrichment_data.album if ctx.enrichment_data else None) or ctx.spotify_title
        return {
            "artist": ctx.spotify_artist or "",
            "album": album,
            "title": ctx.spotify_title,
        }

    # Priority 2 — Enrichment data from ResolveEnrichmentStep
    if ctx and ctx.enrichment_data and (ctx.enrichment_data.artist or ctx.enrichment_data.title):
        return {
            "artist": ctx.enrichment_data.artist or info.uploader.replace(" - Topic", ""),
            "album": ctx.enrichment_data.album or (ctx.enrichment_data.title or info.title),
            "title": ctx.enrichment_data.title or info.track or info.title,
        }

    # Priority 3 — YouTube title parsing fallback
    artist = info.artist or info.uploader.replace(" - Topic", "")
    title = info.track or info.title

    if not info.artist and not info.track and info.title:
        clean_artist, clean_title = clean_youtube_title(info.title)
        if clean_artist:
            artist = clean_artist
        if clean_title:
            title = clean_title

    return {
        "artist": artist,
        "album": info.album or "",
        "title": title,
    }


def _rich_metadata(cover_data: CoverData, info: MediaInfo,
                   ctx: PipelineContext | None = None) -> dict:
    # Provider (Spotify/YTM) artist/title should NOT be overridden by enrichment
    if ctx and ctx.spotify_title:
        return {
            "artist": ctx.spotify_artist or "",
            "album": cover_data.album or info.album or ctx.spotify_title,
            "title": ctx.spotify_title,
            "album_artist": cover_data.album_artist or "",
            "genre": cover_data.genre or "",
            "year": str(cover_data.year) if cover_data.year else "",
            "composer": cover_data.composer or "",
        }

    return {
        "artist": cover_data.artist or info.artist or info.uploader.replace(" - Topic", ""),
        "album": cover_data.album or info.album or "",
        "title": cover_data.title or info.track or info.title,
        "album_artist": cover_data.album_artist or "",
        "genre": cover_data.genre or "",
        "year": str(cover_data.year) if cover_data.year else "",
        "composer": cover_data.composer or "",
    }


class CoverStep(PipelineStep[PipelineContext, PipelineContext]):
    _cover_service = CoverService()

    @trace
    def __call__(self, ctx: PipelineContext) -> PipelineContext:
        if not ctx.cover_mode:
            return ctx
        if ctx.media_info is None or ctx.downloaded_file is None:
            return ctx
        if ctx.media_type != "audio":
            return ctx
        if ctx.config.audio_quality == "opus":
            console.warn(Keys.download.youtube.skip_cover_opus)
            return ctx

        console.proc(Keys.download.youtube.processing_cover)

        info = ctx.media_info
        target_dir = ctx.target_dir
        path = None

        # Priority 1 — Spotify direct cover URL
        if ctx.cover_url:
            with traced("trying Spotify cover art"):
                path = self._download_url(ctx.cover_url, target_dir, info.id)

        # Priority 2 — cover URL from enrichment_data (provider search)
        if path is None and ctx.enrichment_data and ctx.enrichment_data.url:
            with traced("downloading cover from enrichment data"):
                path = self._download_url(ctx.enrichment_data.url, target_dir, info.id)

        # Priority 3 — YouTube thumbnail fallback
        if path is None:
            with traced("falling back to YouTube thumbnail"):
                path = self._youtube_fallback(info, target_dir)

        if path is None or not os.path.exists(path):
            with traced("no cover art obtained"):
                console.err(Keys.download.youtube.cover_process_failed)
                return ctx

        console.proc(Keys.download.youtube.embedding_cover)
        meta = _basic_metadata(info, ctx)

        if embed_cover(ctx.downloaded_file.path, path, ctx.config.audio_quality):
            embed_metadata_tags(ctx.downloaded_file.path, ctx.config.audio_quality, meta)
            console.ok(Keys.download.youtube.cover_success)
        else:
            console.err(Keys.download.youtube.cover_failed)

        clean_temp_files(target_dir, info.id)
        if ctx.cover_result is None:
            # Preserve metadata from ResolveEnrichmentStep if available
            enrichment = ctx.enrichment_data
            ctx.cover_result = CoverResult(
                thumbnail_path=path,
                metadata=LyricsMetadata(
                    artist=(enrichment.artist if enrichment else ""),
                    title=(enrichment.title if enrichment else ""),
                    album=(enrichment.album if enrichment else ""),
                    album_artist=(enrichment.album_artist if enrichment else ""),
                    genre=(enrichment.genre if enrichment else ""),
                    year=(enrichment.year if enrichment else None),
                    composer=(enrichment.composer if enrichment else ""),
                    cover_url=(enrichment.url if enrichment else ""),
                ) if enrichment else None,
                source="spotify" if ctx.cover_url else "smart",
                cropped=False,
            )
        return ctx

    def _download_url(self, url: str, target_dir: str, file_id: str) -> str | None:
        path = os.path.join(target_dir, f"{file_id}.jpg")
        data = self._cover_service.fetch(url)
        if data is None:
            return None
        with open(path, "wb") as f:
            f.write(data)
        return path

    def _youtube_fallback(
        self,
        info: MediaInfo,
        target_dir: str,
    ) -> str | None:
        candidates: list[str] = []
        if info.thumbnail:
            candidates.append(info.thumbnail)
        for t in reversed(info.thumbnails):
            url = t.get("url")
            if url and url not in candidates:
                candidates.append(url)

        thumb_path = os.path.join(target_dir, f"{info.id}.jpg")
        for url in candidates:
            data = self._cover_service.fetch(url)
            if data is not None:
                with open(thumb_path, "wb") as f:
                    f.write(data)
                return self._cover_service.process(thumb_path, target_format="jpg")
        return None


class MetadataStep(PipelineStep[PipelineContext, PipelineContext]):
    @trace
    def __call__(self, ctx: PipelineContext) -> PipelineContext:
        if not ctx.metadata_mode:
            return ctx
        if ctx.downloaded_file is None:
            return ctx

        cover_data: CoverData | None = ctx.enrichment_data
        if not cover_data:
            return ctx

        info = ctx.media_info
        if info is None:
            return ctx

        meta = _rich_metadata(cover_data, info, ctx)
        embed_metadata_tags(ctx.downloaded_file.path, ctx.config.audio_quality, meta)

        if ctx.cover_result is None:
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
