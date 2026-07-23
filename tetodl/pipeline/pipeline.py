"""
MediaPipeline — per-item orchestrator running Extract → Classify → Download → Cover → Lyrics → Finalize.
"""

from ..core.models import AppConfig, PipelineContext
from ..utils.console import console
from ..utils.i18n_keys import Keys
from ..utils.tracer import trace, traced
from .steps.classify import ClassifyStep
from .steps.cover import CoverStep
from .steps.download import DownloadStep
from .steps.extract import ExtractStep
from .steps.finalize import FinalizeStep
from .steps.lyrics import LyricsStep


class MediaPipeline:
    """Run a single media URL through the full download pipeline.

    Steps executed in order:
    1. **ExtractStep** — fetch metadata from yt-dlp.
    2. **ClassifyStep** — check playlist / registry for existing file.
    3. **DownloadStep** — download and convert the media file.
    4. **CoverStep** — fetch, crop, and embed cover art (audio only).
    5. **LyricsStep** — fetch and embed lyrics (audio only).
    6. **FinalizeStep** — post-processing (cache, history, scanner).

    Parameters
    ----------
    config : AppConfig
        Resolved application configuration.

    See Also
    --------
    :class:`ExtractStep` : First pipeline step.
    :class:`ClassifyStep` : Second pipeline step.
    :class:`DownloadStep` : Third pipeline step.
    :class:`CoverStep` : Fourth pipeline step (audio only).
    :class:`LyricsStep` : Fifth pipeline step (audio only).
    :class:`FinalizeStep` : Final pipeline step.

    Example
    -------
    >>> from tetodl.core.models import AppConfig
    >>> config = AppConfig()
    >>> pipeline = MediaPipeline(config=config)
    >>> ctx = pipeline.run("https://youtube.com/watch?v=example", "/tmp")

    """

    def __init__(self, config: AppConfig) -> None:
        """Initialize the pipeline with application configuration.

        Parameters
        ----------
        config : AppConfig
            Resolved application configuration.

        Returns
        -------
        None
        """
        self._config = config

    @trace
    def run(self, url: str, target_dir: str, **ctx_kw: object) -> PipelineContext:
        """Execute the full pipeline for one URL.

        Each step is run sequentially through the pipeline.  If a step
        sets ``ctx.error`` the pipeline short-circuits and returns the
        context immediately.  On success all six steps complete and the
        context carries the downloaded file, cover art, lyrics, and
        bookkeeping results.

        Parameters
        ----------
        url : str
            YouTube video URL.
        target_dir : str
            Directory where the downloaded file will be placed.
        **ctx_kw
            Additional :class:`PipelineContext` fields (e.g.
            ``media_type``, ``is_youtube_music``, ``cut_range``,
            ``download_type_label``).

        Returns
        -------
        PipelineContext
            Context with populated fields from each step.
            ``ctx.downloaded_file`` is ``None`` when the download failed.

        Raises
        ------
        KeyboardInterrupt
            Propagated from :class:`DownloadStep` if the user interrupts
            during download (partial files are cleaned up automatically).

        See Also
        --------
        :class:`ExtractStep` : Metadata extraction.
        :class:`ClassifyStep` : Playlist and registry classification.
        :class:`DownloadStep` : Media download via yt-dlp.
        :class:`CoverStep` : Cover art processing.
        :class:`LyricsStep` : Lyrics fetching and embedding.
        :class:`FinalizeStep` : Post-processing bookkeeping.

        Example
        -------
        >>> from tetodl.core.models import AppConfig
        >>> config = AppConfig()
        >>> pipeline = MediaPipeline(config=config)
        >>> result = pipeline.run(
        ...     "https://youtube.com/watch?v=dQw4w9WgXcQ",
        ...     "/tmp/downloads",
        ...     media_type="audio",
        ... )
        >>> result.downloaded_file is not None or result.error is not None
        True
        """
        ctx = PipelineContext(
            config=self._config,
            url=url,
            target_dir=target_dir,
            **ctx_kw,  # type: ignore[arg-type]
        )

        # 1. Extract
        ctx = ExtractStep()(ctx)
        if ctx.error:
            with traced(f'extract failed — {ctx.error}'):
                console.err(Keys.download.youtube.error_downloading(
                    type=ctx.media_type, error=ctx.error,
                ))
                return ctx

        # 2. Classify
        ctx = ClassifyStep()(ctx)
        if ctx.classification and ctx.classification.existing_result:
            return ctx

        # 3. Start message
        self._show_start(ctx)

        # 4. Download
        with traced('starting download'):
            ctx = DownloadStep()(ctx)
        if ctx.error and ctx.downloaded_file is None:
            with traced(f'download failed — {ctx.error}'):
                return ctx

        # 5. Cover
        with traced('processing cover'):
            ctx = CoverStep()(ctx)

        # 6. Lyrics
        with traced('processing lyrics'):
            ctx = LyricsStep()(ctx)

        # 7. Finalize
        ctx = FinalizeStep()(ctx)

        return ctx

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _show_start(self, ctx: PipelineContext) -> None:
        """Print a start-download message to the console with media type."""
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
