"""
DownloadStep — download media via yt-dlp with the same options as the
original ``audio.py`` / ``video.py``.
"""

import glob
import os
from typing import Optional

try:
    import yt_dlp as yt
except ImportError:
    yt = None

from ...constants import FFMPEG_CMD, RuntimeConfig
from ...core.models import DownloadedFile, MediaInfo
from ...core.step import PipelineStep, PipelineError
from ...utils.console import console
from ...utils.hooks import QuietLogger, get_progress_hook, get_postprocessor_hook
from ...utils.i18n_keys import Keys
from ...utils.processing import (
    get_audio_format_string,
    build_audio_postprocessors,
)


class DownloadStep(PipelineStep):
    """Download a single media file via yt-dlp.

    Supports both audio-only and video downloads with the same format
    strings, postprocessors, and FFmpeg options as the original code.
    Callers must set ``media_type`` to ``'audio'`` or ``'video'``.
    """

    def __init__(
        self,
        media_type: str = "audio",
        audio_quality: str = "m4a",
        video_container: str = "mp4",
        video_codec: str = "h264",
        max_resolution: str = "720p",
        quiet: bool = False,
        progress_style: str = "minimal",
        cut_range: Optional[tuple[float, float]] = None,
        skip_metadata: bool = False,
    ) -> None:
        """Configure the download step.

        Parameters
        ----------
        media_type : str
            ``'audio'`` or ``'video'``.
        audio_quality : str
            Target audio format (e.g. ``'m4a'``, ``'opus'``, ``'mp3'``).
        video_container : str
            Target video container (e.g. ``'mp4'``, ``'mkv'``).
        video_codec : str
            Target video codec (e.g. ``'h264'``, ``'h265'``).
        max_resolution : str
            Maximum video resolution (e.g. ``'720p'``, ``'1080p'``).
        quiet : bool
            Suppress non-essential output.
        progress_style : str
            Progress bar style (``'minimal'``, ``'detailed'``).
        cut_range : tuple[float, float] | None
            Start and end time in seconds for trimming.
        skip_metadata : bool
            When ``True``, remove the ``FFmpegMetadata`` post-processor
            (equivalent to the ``--no-cover`` / ``NO_COVER_MODE`` flag).
        """
        self._media_type = media_type
        self._audio_quality = audio_quality
        self._video_container = video_container
        self._video_codec = video_codec
        self._max_resolution = max_resolution
        self._quiet = quiet
        self._progress_style = progress_style
        self._cut_range = cut_range
        self._skip_metadata = skip_metadata

    def __call__(self, info: MediaInfo, target_dir: str) -> DownloadedFile:
        """Download the media file.

        Parameters
        ----------
        info : MediaInfo
            Extracted media metadata (used for title, id, url).
        target_dir : str
            Output directory for the downloaded file.

        Returns
        -------
        DownloadedFile
            Path and metadata of the completed download.

        Raises
        ------
        PipelineError
            If yt-dlp is unavailable or the download fails.
        KeyboardInterrupt
            Propagated from the download hook (user cancellation).
        """
        if yt is None:
            raise PipelineError("yt-dlp is not available", "download")

        try:
            return self._download(info, target_dir)
        except KeyboardInterrupt:
            self._cleanup_partial(target_dir, info)
            raise
        except Exception as exc:
            self._cleanup_partial(target_dir, info)
            raise PipelineError(str(exc), "download") from exc

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _download(self, info: MediaInfo, target_dir: str) -> DownloadedFile:
        opts = self._build_ydl_opts(info, target_dir)

        if self._cut_range:
            start, end = self._cut_range
            console.warn(Keys.media.trimming_audio(start=start, end=end))
            opts["download_ranges"] = lambda info, ydl: [{"start_time": start, "end_time": end}]
            opts["force_keyframes_at_cuts"] = True

        console.proc(Keys.download.youtube.downloading_item(title=info.title))
        with yt.YoutubeDL(opts) as ydl:
            ydl.download([info.url])

        container = self._audio_quality if self._media_type == "audio" else self._video_container
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

    def _build_ydl_opts(self, info: MediaInfo, target_dir: str) -> dict:
        if self._media_type == "video":
            return self._video_opts(target_dir)
        return self._audio_opts(target_dir)

    def _audio_opts(self, target_dir: str) -> dict:
        fmt = get_audio_format_string(self._audio_quality)
        pps = build_audio_postprocessors(self._audio_quality)
        if self._skip_metadata:
            pps = [pp for pp in pps if pp.get("key") != "FFmpegMetadata"]

        return {
            "format": fmt,
            "outtmpl": os.path.join(target_dir, "%(title)s.%(ext)s"),
            "postprocessors": pps,
            "ffmpeg_location": FFMPEG_CMD,
            "quiet": True,
            "no_warnings": True,
            "writethumbnail": False,
            "logger": QuietLogger(),
            "progress_hooks": [get_progress_hook(self._progress_style)],
            "noprogress": False,
            "retries": RuntimeConfig.MAX_RETRIES,
            "fragment_retries": RuntimeConfig.MAX_RETRIES,
            "file_access_retries": RuntimeConfig.MAX_RETRIES,
            "extractor_retries": 3,
        }

    def _video_opts(self, target_dir: str) -> dict:
        pp_args: list[str] = []
        if self._video_codec == "h264":
            pp_args = [
                "-c:v", "libx264",
                "-profile:v", "main",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-movflags", "+faststart",
            ]
        elif self._video_codec == "h265":
            pp_args = ["-c:v", "libx265", "-c:a", "aac"]

        max_h = self._max_resolution.replace("p", "")
        video_fmt = f"bestvideo[height<={max_h}]+bestaudio/best[height<={max_h}]"
        progress = get_progress_hook(self._progress_style)
        pp_hook = [get_postprocessor_hook(
            Keys.media.encoding(codec=self._video_codec.upper())
        )]

        return {
            "format": video_fmt,
            "merge_output_format": self._video_container,
            "outtmpl": os.path.join(target_dir, "%(title)s.%(ext)s"),
            "ffmpeg_location": FFMPEG_CMD,
            "quiet": True,
            "no_warnings": True,
            "logger": QuietLogger(),
            "progress_hooks": [progress],
            "postprocessor_hooks": pp_hook,
            "postprocessor_args": pp_args if pp_args else None,
            "retries": RuntimeConfig.MAX_RETRIES,
            "fragment_retries": RuntimeConfig.MAX_RETRIES,
            "file_access_retries": RuntimeConfig.MAX_RETRIES,
            "extractor_retries": 3,
        }

    @staticmethod
    def _cleanup_partial(target_dir: str, info: MediaInfo) -> None:
        """Remove partial (.part, .ytdl) files left by a failed download."""
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
