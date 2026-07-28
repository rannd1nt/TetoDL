import os

from tetodl.core.domain.cache import cache_metadata
from tetodl.core.domain.history import add_to_history
from tetodl.core.domain.models import PipelineContext
from tetodl.core.domain.step import PipelineStep
from tetodl.utils.processing import extract_video_id
from tetodl.utils.tracer import trace, traced


class FinalizeStep(PipelineStep[PipelineContext, PipelineContext]):
    @trace
    def __call__(self, ctx: PipelineContext) -> PipelineContext:
        if ctx.downloaded_file is None:
            return ctx

        with traced('finalize: cache, history, scanner'):
            self._cache(ctx)
            self._add_to_history(ctx)
            self._run_scanner(ctx)

        return ctx

    @staticmethod
    def _cache(ctx: PipelineContext) -> None:
        downloaded = ctx.downloaded_file
        if downloaded is None:
            return
        info = downloaded.info
        if not info:
            return
        cache_metadata(ctx.url, {
            "title": downloaded.title,
            "duration": downloaded.duration,
            "uploader": info.uploader,
            "artist": ctx.spotify_artist or info.artist or "",
            "album": info.album or "",
            "track": ctx.spotify_title or info.track or "",
            "thumbnails": info.thumbnails,
        })

    @staticmethod
    def _add_to_history(ctx: PipelineContext) -> None:
        downloaded = ctx.downloaded_file
        assert downloaded is not None
        info = downloaded.info
        video_id = info.id if info else extract_video_id(ctx.url)
        artist = ctx.spotify_artist or ((info.artist or info.uploader or "Unknown Artist") if info else "Unknown Artist")
        album = info.album if info else None

        platform = "YouTube Music" if ctx.is_youtube_music else "YouTube Audio"
        history_title = f"{artist} - {downloaded.title}" if ctx.is_youtube_music else downloaded.title
        download_type = "Playlist Track" if "Playlist" in ctx.download_type_label else "Single Track"
        if ctx.media_type == "video":
            download_type = download_type.replace("Track", "Video")

        add_to_history(
            id=video_id,
            file_path=downloaded.path,
            success=True,
            title=history_title,
            content_type=ctx.media_type,
            platform=platform,
            download_type=download_type,
            duration=downloaded.duration,
            metadata={"artist": artist, "album": album, "title": downloaded.title},
            spotify_id=ctx.spotify_id,
        )

    @staticmethod
    def _run_scanner(ctx: PipelineContext) -> None:
        if not ctx.config.media_scanner_enabled:
            return
        downloaded = ctx.downloaded_file
        assert downloaded is not None
        from tetodl.utils.media_scanner import scan_media_files
        scan_media_files(os.path.abspath(downloaded.path))
