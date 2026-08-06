from __future__ import annotations

from tetodl.core.pipeline.cleaners.title import clean_youtube_title
from tetodl.core.domain.models import CoverResult, MediaInfo, PipelineContext


def resolve_artist_title(
    info: MediaInfo,
    ctx: PipelineContext | None = None,
    cover_result: CoverResult | None = None,
) -> tuple[str, str]:
    if cover_result and cover_result.metadata:
        return cover_result.metadata.artist, cover_result.metadata.title

    if ctx and ctx.spotify_title:
        return (ctx.spotify_artist or ""), ctx.spotify_title

    if info.artist and info.track:
        return info.artist, info.track

    raw = info.title or ""
    artist, title = clean_youtube_title(raw)
    if artist and title:
        if info.uploader:
            uploader_clean = info.uploader.replace(" - Topic", "").strip().lower()
            if title.lower() == uploader_clean and artist.lower() != uploader_clean:
                artist, title = title, artist
        return artist, title

    artist = info.artist or info.uploader.replace(" - Topic", "")
    title = info.track or info.title
    return artist or "", title or ""
