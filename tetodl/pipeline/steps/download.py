"""
DownloadStep — download media via yt-dlp.
"""

import glob
import os
from typing import Optional

try:
    import yt_dlp as yt
except ImportError:
    yt = None

from ...constants import FFMPEG_CMD
from ...core.models import DownloadedFile, MediaInfo, PipelineContext
from ...core.step import PipelineStep
from ...utils.console import console
from ...utils.hooks import QuietLogger, get_progress_hook, get_postprocessor_hook
from tetodl.utils.tracer import trace
from ...utils.i18n_keys import Keys
from ...utils.processing import (
    get_audio_format_string,
    build_audio_postprocessors,
)


class DownloadStep(PipelineStep[PipelineContext, PipelineContext]):
    """Download a single media file via yt-dlp.

    Reads ``ctx.media_info``, ``ctx.target_dir``, and ``ctx.config``,
    then writes ``ctx.downloaded_file``.  Builds media-type-specific
    yt-dlp options (audio or video) and handles partial-file cleanup
    on failure.

    See Also
    --------
    :class:`MediaInfo` : Input metadata for download.
    :class:`DownloadedFile` : Output model with file path and metadata.
    :class:`CoverStep` : Next step in the pipeline (audio only).

    Example
    -------
    >>> step = DownloadStep()
    >>> ctx = PipelineContext(media_info=some_info, target_dir="/tmp")
    >>> result = step(ctx)
    >>> result.downloaded_file is not None or result.error is not None
    True
    """

    def __init__(self) -> None:
        """Initialize the download step.

        Returns
        -------
        None
        """
        pass

    @trace
    def __call__(self, ctx: PipelineContext) -> PipelineContext:
        """Download the media file described by the pipeline context.

        Validates that ``ctx.media_info`` and ``yt-dlp`` are available,
        then delegates to :meth:`_download`.  On :exc:`KeyboardInterrupt`
        or generic exception, partial files are cleaned up via
        :meth:`_cleanup_partial`.

        Parameters
        ----------
        ctx : PipelineContext
            Context with ``media_info`` and ``target_dir`` set.

        Returns
        -------
        PipelineContext
            Context with ``downloaded_file`` set, or ``error`` set on
            failure.

        Raises
        ------
        KeyboardInterrupt
            Re-raised after partial file cleanup so the caller can handle
            user interruption.

        See Also
        --------
        :meth:`_download` : Core download logic.
        :meth:`_cleanup_partial` : Partial file removal on failure.

        Example
        -------
        >>> from tetodl.core.models import PipelineContext, MediaInfo
        >>> info = MediaInfo(title="Test", url="https://...")
        >>> ctx = PipelineContext(media_info=info, target_dir="/tmp")
        >>> step = DownloadStep()
        >>> ctx = step(ctx)
        """
        if ctx.media_info is None:
            ctx.error = "No media info available for download"
            return ctx
        if yt is None:
            ctx.error = "yt-dlp is not available"
            return ctx

        info = ctx.media_info
        target_dir = ctx.target_dir

        try:
            result = self._download(info, target_dir, ctx)
            ctx.downloaded_file = result
            return ctx
        except KeyboardInterrupt:
            self._cleanup_partial(target_dir, info)
            raise
        except Exception as exc:
            self._cleanup_partial(target_dir, info)
            ctx.error = str(exc)
            return ctx

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _download(
        self,
        info: MediaInfo,
        target_dir: str,
        ctx: PipelineContext,
    ) -> DownloadedFile:
        """Execute the yt-dlp download and return a :class:`DownloadedFile`.

        Builds yt-dlp options via :meth:`_build_ydl_opts`, handles
        cut-range trimming, runs the download, and resolves the final
        file path (accounting for yt-dlp extensions).

        Parameters
        ----------
        info : MediaInfo
            Media metadata (title, url, artist, etc.).
        target_dir : str
            Output directory for the downloaded file.
        ctx : PipelineContext
            Full pipeline context with config and media type.

        Returns
        -------
        DownloadedFile
            Descriptor of the successfully downloaded file.
        """
        opts = self._build_ydl_opts(ctx)

        if ctx.cut_range:
            start, end = ctx.cut_range
            console.warn(Keys.media.trimming_audio(start=str(start), end=str(end)))
            opts["download_ranges"] = lambda info, ydl: [{"start_time": start, "end_time": end}]
            opts["force_keyframes_at_cuts"] = True

        console.proc(Keys.download.youtube.downloading_item(title=info.title))
        with yt.YoutubeDL(opts) as ydl:
            ydl.download([info.url])

        container = ctx.config.audio_quality if ctx.media_type == "audio" else ctx.config.video_container
        path = os.path.join(target_dir, f"{info.title}.{container}")
        if not os.path.exists(path):
            guessed = self._find_file(target_dir, info)
            path = guessed or path

        return DownloadedFile(
            path=os.path.abspath(path),
            container=container,
            title=info.title,
            artist=info.artist or info.uploader,
            duration=info.duration,
            info=info,
        )

    def _build_ydl_opts(self, ctx: PipelineContext) -> dict:
        """Build yt-dlp options dict for the current media type.

        Delegates to :meth:`_video_opts` or :meth:`_audio_opts`
        based on ``ctx.media_type``.

        Parameters
        ----------
        ctx : PipelineContext
            Pipeline context with config and media type.

        Returns
        -------
        dict
            yt-dlp options dictionary.
        """
        if ctx.media_type == "video":
            return self._video_opts(ctx)
        return self._audio_opts(ctx)

    def _audio_opts(self, ctx: PipelineContext) -> dict:
        """Build yt-dlp options for audio download and conversion.

        Parameters
        ----------
        ctx : PipelineContext
            Pipeline context with audio quality config.

        Returns
        -------
        dict
            yt-dlp options with postprocessor config for audio.
        """
        config = ctx.config
        fmt = get_audio_format_string(config.audio_quality)
        pps = build_audio_postprocessors(config.audio_quality)
        if config.no_cover_mode:
            pps = [pp for pp in pps if pp.get("key") != "FFmpegMetadata"]

        return {
            "format": fmt,
            "outtmpl": os.path.join(ctx.target_dir, "%(title)s.%(ext)s"),
            "postprocessors": pps,
            "ffmpeg_location": FFMPEG_CMD,
            "quiet": True,
            "no_warnings": True,
            "writethumbnail": False,
            "logger": QuietLogger(),
            "progress_hooks": [get_progress_hook(config.progress_style)],
            "noprogress": False,
            "retries": config.max_retries,
            "fragment_retries": config.max_retries,
            "file_access_retries": config.max_retries,
            "extractor_retries": 3,
        }

    def _video_opts(self, ctx: PipelineContext) -> dict:
        """Build yt-dlp options for video download and encoding.

        Parameters
        ----------
        ctx : PipelineContext
            Pipeline context with video codec and resolution config.

        Returns
        -------
        dict
            yt-dlp options with merge and postprocessor args for video.
        """
        config = ctx.config
        pp_args: list[str] = []
        if config.video_codec == "h264":
            pp_args = [
                "-c:v", "libx264",
                "-profile:v", "main",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-movflags", "+faststart",
            ]
        elif config.video_codec == "h265":
            pp_args = ["-c:v", "libx265", "-c:a", "aac"]

        max_h = config.max_video_resolution.replace("p", "")
        video_fmt = f"bestvideo[height<={max_h}]+bestaudio/best[height<={max_h}]"
        progress = get_progress_hook(config.progress_style)
        pp_hook = [get_postprocessor_hook(
            f"Re-encoding video to {config.video_codec.upper()}..."
        )]

        return {
            "format": video_fmt,
            "merge_output_format": config.video_container,
            "outtmpl": os.path.join(ctx.target_dir, "%(title)s.%(ext)s"),
            "ffmpeg_location": FFMPEG_CMD,
            "quiet": True,
            "no_warnings": True,
            "logger": QuietLogger(),
            "progress_hooks": [progress],
            "postprocessor_hooks": pp_hook,
            "postprocessor_args": pp_args if pp_args else None,
            "retries": config.max_retries,
            "fragment_retries": config.max_retries,
            "file_access_retries": config.max_retries,
            "extractor_retries": 3,
        }

    @staticmethod
    def _cleanup_partial(target_dir: str, info: MediaInfo) -> None:
        """Remove partial (``.part``, ``.ytdl``) files left by a failed download."""
        base = os.path.join(target_dir, info.title)
        for pattern in (f"{base}.*.part", f"{base}.part", f"{base}.ytdl"):
            for f in glob.glob(pattern):
                try:
                    os.remove(f)
                except OSError:
                    pass

    @staticmethod
    def _find_file(target_dir: str, info: MediaInfo) -> Optional[str]:
        """Search for the downloaded file when the expected path doesn't exist."""
        base = os.path.join(target_dir, info.title)
        for f in glob.glob(f"{base}.*"):
            if not f.endswith(".part") and not f.endswith(".ytdl"):
                return f
        return None
