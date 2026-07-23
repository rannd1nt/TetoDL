"""
FinalizeStep — post-processing bookkeeping after a successful download.
"""

import os

from ...core.cache import cache_metadata
from ...core.history import add_to_history
from ...core.models import PipelineContext
from ...core.step import PipelineStep
from ...utils.processing import extract_video_id
from tetodl.utils.tracer import trace, traced


class FinalizeStep(PipelineStep[PipelineContext, PipelineContext]):
    """Post-processing bookkeeping after a successful download.

    Performs three side effects in order:
    1. **Cache** — store metadata via :func:`cache_metadata`.
    2. **History** — register the download via :func:`add_to_history`.
    3. **Scanner** — notify the media scanner if enabled.

    Reads ``ctx.downloaded_file``, ``ctx.url``, and ``ctx.config``.
    No new data is written to the context — this step is a terminal
    side-effect step.

    See Also
    --------
    :func:`cache_metadata` : Metadata caching in :mod:`core.cache`.
    :func:`add_to_history` : History registration in :mod:`core.history`.
    :func:`scan_media_files` : Media scanner notification.

    Example
    -------
    >>> step = FinalizeStep()
    >>> ctx = PipelineContext(downloaded_file=some_file, config=cfg)
    >>> result = step(ctx)
    """

    @trace
    def __call__(self, ctx: PipelineContext) -> PipelineContext:
        """Run post-processing bookkeeping for the completed download.

        Calls :meth:`_cache`, :meth:`_add_to_history`, and
        :meth:`_run_scanner` in order.  If ``ctx.downloaded_file`` is
        ``None`` the method returns immediately.

        Parameters
        ----------
        ctx : PipelineContext
            Pipeline context with ``downloaded_file`` and ``config``.

        Returns
        -------
        PipelineContext
            Unchanged context (all effects are side effects).

        Raises
        ------
        None
            Exceptions from side-effect calls are allowed to propagate.

        See Also
        --------
        :meth:`_cache` : Metadata caching.
        :meth:`_add_to_history` : History and registry registration.
        :meth:`_run_scanner` : Media scanner notification.

        Example
        -------
        >>> step = FinalizeStep()
        >>> ctx = PipelineContext(downloaded_file=my_file, config=config)
        >>> result = step(ctx)
        >>> result is ctx
        True
        """
        if ctx.downloaded_file is None:
            return ctx

        with traced('finalize: cache, history, scanner'):
            self._cache(ctx)
            self._add_to_history(ctx)
            self._run_scanner(ctx)

        return ctx

    @staticmethod
    def _cache(ctx: PipelineContext) -> None:
        """Store downloaded-file metadata in the local cache for future runs."""
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
        """Register the completed download in history and the file registry."""
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
        """Notify the media scanner of the new file if the feature is enabled."""
        if not ctx.config.media_scanner_enabled:
            return
        downloaded = ctx.downloaded_file
        assert downloaded is not None
        from ...utils.media_scanner import scan_media_files
        scan_media_files(os.path.abspath(downloaded.path))
