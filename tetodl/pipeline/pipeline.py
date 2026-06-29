"""
MediaPipeline — per-item orchestrator running Extract → Download → Cover → Lyrics.
"""

import os
from typing import Optional

from ..core.models import (
    AppConfig,
    CoverConfig,
    CoverResult,
    DownloadedFile,
    LyricsConfig,
    MediaInfo,
)
from ..core.step import PipelineError
from ..utils.console import console
from ..utils.i18n_keys import Keys

from .steps.extract import ExtractStep
from .steps.download import DownloadStep
from .steps.cover import CoverStep
from .steps.lyrics import LyricsStep


class MediaPipeline:
    """Run a single media URL through the full download pipeline.

    Steps executed in order:
    1. **ExtractStep** — fetch metadata from yt-dlp.
    2. **DownloadStep** — download and convert the media file.
    3. **CoverStep** — fetch, crop, and embed cover art (audio only).
    4. **LyricsStep** — fetch and embed lyrics (audio only).

    Parameters
    ----------
    config : AppConfig
        Resolved application configuration.
    media_type : str
        ``'audio'`` or ``'video'``.
    is_youtube_music : bool
        Whether the URL is a YouTube Music link.
    download_type_label : str
        Label for progress messages (e.g. ``'Single Track'``).
    cut_range : tuple[float, float] | None
        Optional trim range in seconds.
    """

    def __init__(
        self,
        config: AppConfig,
        media_type: str,
        is_youtube_music: bool = False,
        download_type_label: str = "Download",
        cut_range: Optional[tuple[float, float]] = None,
    ) -> None:
        if media_type not in ("audio", "video"):
            raise ValueError(f"media_type must be 'audio' or 'video', got {media_type!r}")
        self._config = config
        self._media_type = media_type
        self._is_youtube_music = is_youtube_music
        self._dl_type_label = download_type_label
        self._cut_range = cut_range

    def run(self, url: str, target_dir: str) -> Optional[DownloadedFile]:
        """Execute the full pipeline for one URL.

        Parameters
        ----------
        url : str
            YouTube video URL.
        target_dir : str
            Directory where the downloaded file will be placed.

        Returns
        -------
        DownloadedFile | None
            The completed download, or ``None`` if the pipeline was
            skipped or failed early.
        """
        try:
            info = self._extract(url)
        except PipelineError as exc:
            console.err(Keys.download.youtube.error_downloading(
                type=self._media_type, error=str(exc),
            ))
            return None

        if info is None:
            return None

        self._show_start(info, target_dir)
        downloaded = self._download(info, target_dir)
        if downloaded is None:
            return None

        cr = self._process_cover(info, downloaded, target_dir)
        self._process_lyrics(info, downloaded, cr)
        return downloaded

    # ------------------------------------------------------------------
    # Per-step runners
    # ------------------------------------------------------------------

    def _extract(self, url: str) -> Optional[MediaInfo]:
        return ExtractStep()(url)

    def _show_start(self, info: MediaInfo, target_dir: str) -> None:
        res = self._config.max_video_resolution
        label = self._media_type
        if label == "video":
            label = f"video ({res})"
        if self._config.simple_mode:
            console.proc(Keys.download.youtube.simple_mode_start(
                type=label, path=target_dir,
            ))
        else:
            console.proc(Keys.download.youtube.start_download(
                type=label, path=target_dir,
            ))

    def _download(self, info: MediaInfo, target_dir: str) -> Optional[DownloadedFile]:
        fmt = self._config.audio_quality if self._media_type == "audio" else self._config.video_container
        skip_meta = self._config.no_cover_mode

        step = DownloadStep(
            media_type=self._media_type,
            audio_quality=fmt,
            video_container=self._config.video_container,
            video_codec=self._config.video_codec,
            max_resolution=self._config.max_video_resolution,
            quiet=self._config.simple_mode,
            progress_style=self._config.progress_style,
            cut_range=self._cut_range,
            skip_metadata=skip_meta,
        )

        try:
            return step(info, target_dir)
        except PipelineError as exc:
            console.err(Keys.download.youtube.error_downloading(
                type=self._media_type, error=str(exc),
            ))
            return None

    def _process_cover(
        self,
        info: MediaInfo,
        downloaded: DownloadedFile,
        target_dir: str,
    ) -> Optional[CoverResult]:
        if self._config.no_cover_mode or self._media_type != "audio":
            return None

        fmt = self._config.audio_quality
        use_smart = self._config.smart_cover_mode
        force_crop = self._config.force_crop

        # opus doesn't support embedded covers
        if fmt == "opus":
            console.warn(Keys.download.youtube.skip_cover_opus)
            return None

        # only process cover when YT Music or smart-cover is active
        if not (self._is_youtube_music or use_smart):
            console.warn(Keys.download.youtube.skip_cover)
            return None

        console.proc(Keys.download.youtube.processing_cover)
        step = CoverStep(
            config=CoverConfig(smart_mode=use_smart, disabled=False, force_crop=force_crop),
            is_youtube_music=self._is_youtube_music,
            audio_format=fmt,
        )
        return step(info, downloaded, target_dir)

    def _process_lyrics(
        self,
        info: MediaInfo,
        downloaded: DownloadedFile,
        cover_result: Optional[CoverResult] = None,
    ) -> None:
        if not self._config.lyrics_mode or self._media_type != "audio":
            return
        if not os.path.exists(downloaded.path):
            return

        step = LyricsStep(
            config=LyricsConfig(
                enabled=True,
                romaji=self._config.romaji_mode,
            ),
        )
        step(info, downloaded.path, cover_result)
