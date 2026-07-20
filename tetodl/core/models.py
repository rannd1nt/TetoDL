"""
Pydantic models for TetoDL data flow.
"""

from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, field_validator
from typing import Any, Optional, Literal, Union


# =============================================================================
# Domain-specific sub-configs
# =============================================================================


class AudioConfig(BaseModel):
    """Audio-specific download options.

    Controls the output audio quality and container format string that
    is passed to yt-dlp.

    Parameters
    ----------
    quality : str, optional
        Audio quality or container format (default ``'m4a'``).
        Passed directly to yt-dlp as ``--audio-format``.
        Typical values: ``'m4a'``, ``'mp3'``, ``'opus'``, ``'best'``.

    Example
    -------
    >>> cfg = AudioConfig(quality='mp3')
    >>> cfg.quality
    'mp3'

    See Also
    --------
    :class:`VideoConfig` : Video-specific download options.
    :class:`DownloadConfig` : General download behaviour.
    :class:`AppConfig.audio` : AppConfig property that builds this.
    """
    quality: str = 'm4a'


class VideoConfig(BaseModel):
    """Video-specific download options.

    Controls the output video container, codec preference, and maximum
    resolution for video downloads.

    Parameters
    ----------
    container : str, optional
        Output container format (default ``'mp4'``).
        Common values: ``'mp4'``, ``'mkv'``, ``'webm'``.
    codec : str, optional
        Preferred video codec (default ``'h264'``).
        Supported values depend on yt-dlp and ffmpeg.
    max_resolution : str, optional
        Maximum output resolution (default ``'720p'``).
        Accepts strings like ``'480p'``, ``'720p'``, ``'1080p'``.

    Example
    -------
    >>> cfg = VideoConfig(container='mkv', codec='av1', max_resolution='1080p')
    >>> cfg.container
    'mkv'

    See Also
    --------
    :class:`AudioConfig` : Audio-specific download options.
    :class:`AppConfig.video` : AppConfig property that builds this.
    """
    container: str = 'mp4'
    codec: str = 'h264'
    max_resolution: str = '720p'


class CoverConfig(BaseModel):
    """Cover art processing options.

    Configures how cover art thumbnails are fetched, cropped, and
    embedded into downloaded media files.

    Parameters
    ----------
    smart_mode : bool, optional
        Enable smart cover selection (default ``True``).
        When enabled, the best available thumbnail is chosen
        automatically.
    disabled : bool, optional
        Completely disable cover art processing (default ``False``).
    force_crop : bool, optional
        Always crop cover art to a square aspect ratio
        (default ``False``).

    Example
    -------
    >>> cfg = CoverConfig(smart_mode=False, disabled=True)
    >>> cfg.disabled
    True

    See Also
    --------
    :class:`CoverResult` : Output of cover-art processing.
    :class:`AppConfig.cover` : AppConfig property that builds this.
    """
    smart_mode: bool = True
    disabled: bool = False
    force_crop: bool = False


class LyricsConfig(BaseModel):
    """Lyrics embedding options.

    Controls whether lyrics are fetched from an external provider and
    embedded into the downloaded media file, and whether romaji
    (romanised) lyrics are preferred.

    Parameters
    ----------
    enabled : bool, optional
        Enable lyrics fetching and embedding (default ``False``).
    romaji : bool, optional
        Prefer romaji-transliterated lyrics when available
        (default ``False``).

    Example
    -------
    >>> cfg = LyricsConfig(enabled=True, romaji=True)
    >>> cfg.enabled
    True

    See Also
    --------
    :class:`LyricsMetadata` : Data model for fetched lyrics.
    :class:`AppConfig.lyrics` : AppConfig property that builds this.
    """
    enabled: bool = False
    romaji: bool = False


class DownloadConfig(BaseModel):
    """Base download behaviour.

    Controls the high-level download flow: simplified mode, quiet
    output, concurrency, skip logic, and progress display.

    Parameters
    ----------
    simple_mode : bool, optional
        Run in simplified single-file mode (default ``True``).
    quiet : bool, optional
        Suppress all non-critical console output (default ``False``).
    async_mode : bool, optional
        Enable asynchronous / concurrent downloads (default ``False``).
    skip_existing : bool, optional
        Skip downloads whose output files already exist
        (default ``True``).
    progress_style : str, optional
        Progress display style (default ``'minimal'``).
        Other recognised values: ``'detailed'``, ``'none'``.

    Example
    -------
    >>> cfg = DownloadConfig(simple_mode=False, progress_style='detailed')
    >>> cfg.skip_existing
    True

    See Also
    --------
    :class:`AudioConfig` : Audio-specific options.
    :class:`VideoConfig` : Video-specific options.
    :class:`AppConfig.download` : AppConfig property that builds this.
    """
    simple_mode: bool = True
    quiet: bool = False
    async_mode: bool = False
    skip_existing: bool = True
    progress_style: str = 'minimal'


class LibraryConfig(BaseModel):
    """Storage paths and library structure.

    Defines where download output is written to disk and how files
    are organised — grouping sub-directories, M3U playlists, and
    ZIP archives.

    Parameters
    ----------
    music_root : str, optional
        Root directory for audio downloads (default ``''``).
    video_root : str, optional
        Root directory for video downloads (default ``''``).
    thumbnail_root : str, optional
        Root directory for thumbnail output (default ``''``).
    group_mode : bool | str, optional
        Group downloads into sub-directories (default ``False``).
        When given a string, it is used as the group folder name.
    create_m3u : bool, optional
        Generate an M3U playlist file after each download
        (default ``False``).
    zip_mode : bool, optional
        Package downloaded output into a ZIP archive
        (default ``False``).

    Example
    -------
    >>> cfg = LibraryConfig(music_root='/data/music', group_mode='artist')
    >>> cfg.zip_mode
    False

    See Also
    --------
    :class:`AppConfig.library` : AppConfig property that builds this.
    :class:`DownloadTarget` : Resolved output target derived from config.
    """
    music_root: str = ""
    video_root: str = ""
    thumbnail_root: str = ""
    group_mode: bool | str = False
    create_m3u: bool = False
    zip_mode: bool = False


class ThumbnailConfig(BaseModel):
    """Thumbnail format options.

    Parameters
    ----------
    format : str, optional
        Thumbnail image file format (default ``'jpg'``).
        Supported: ``'jpg'``, ``'png'``, ``'webp'``.

    Example
    -------
    >>> cfg = ThumbnailConfig(format='png')
    >>> cfg.format
    'png'

    See Also
    --------
    :class:`CoverConfig` : Cover art processing options.
    :class:`AppConfig` : Root config that uses ``thumbnail_format``.
    """
    format: str = 'jpg'


class SystemConfig(BaseModel):
    """System-level settings (not overridable per request).

    Controls the local media scanner, download retry behaviour, and
    concurrency limits.  These values apply globally and are **not**
    overridden by :class:`SessionOverrides`.

    Parameters
    ----------
    media_scanner_enabled : bool, optional
        Enable the local media file scanner (default ``False``).
    download_delay : int, optional
        Delay in seconds between successive downloads
        (default ``2``).
    max_retries : int, optional
        Maximum number of retries on download failure
        (default ``3``).
    retry_delay : int, optional
        Delay in seconds between retry attempts (default ``2``).
    async_workers : int, optional
        Number of concurrent asynchronous workers
        (default ``3``).

    Example
    -------
    >>> cfg = SystemConfig(max_retries=5, async_workers=4)
    >>> cfg.async_workers
    4

    See Also
    --------
    :class:`DaemonConfig` : Daemon-specific settings.
    :class:`AppConfig.system` : AppConfig property that builds this.
    """
    media_scanner_enabled: bool = False
    download_delay: int = 2
    max_retries: int = 3
    retry_delay: int = 2
    async_workers: int = 3


class DaemonConfig(BaseModel):
    """Daemon-specific settings.

    Controls the behaviour of the persistent daemon process:
    temporary directory usage and cleanup scheduling.

    Parameters
    ----------
    default_temp : bool, optional
        Use the system temporary directory for staging
        (default ``True``).
    cleanup_interval : int, optional
        Interval in seconds between cache / temporary file
        cleanups (default ``3600``).

    Example
    -------
    >>> cfg = DaemonConfig(default_temp=False, cleanup_interval=7200)
    >>> cfg.cleanup_interval
    7200

    See Also
    --------
    :class:`SystemConfig` : Non-daemon system-level settings.
    :class:`AppConfig.daemon` : AppConfig property that builds this.
    """
    default_temp: bool = True
    cleanup_interval: int = 3600


# =============================================================================
# AppConfig — root application configuration
# =============================================================================


class AppConfig(BaseModel):
    """Root configuration for a TetoDL session.

    Loaded from ``config.json`` via :func:`core.config.load_app_config`
    and merged with per-request overrides through the
    :class:`ConfigResolver`.

    The flat fields map directly to JSON keys in the config file.
    Domain-specific sub-configs (:class:`AudioConfig`,
    :class:`CoverConfig`, …) are available as read-only properties
    and consumed by pipeline steps.

    Parameters
    ----------
    music_root : str, optional
        Root directory for music downloads (default ``''``).
    video_root : str, optional
        Root directory for video downloads (default ``''``).
    thumbnail_root : str, optional
        Root directory for thumbnail output (default ``''``).
    simple_mode : bool, optional
        Simplified single-file download mode (default ``False``).
    async_mode : bool, optional
        Enable concurrent / asynchronous downloads (default ``False``).
    quiet : bool, optional
        Suppress all non-critical console output (default ``False``).
    smart_cover_mode : bool, optional
        Automatically select the best available thumbnail
        (default ``True``).
    no_cover_mode : bool, optional
        Skip cover art processing entirely (default ``False``).
    force_crop : bool, optional
        Always crop cover art to a square (default ``False``).
    thumbnail_format : str, optional
        Thumbnail image format (default ``'jpg'``).
        Supported: ``'jpg'``, ``'png'``, ``'webp'``.
    group_mode : bool, optional
        Group downloads into sub-directories (default ``False``).
    force_grouping_on_share : bool, optional
        Force grouping even when the share server is active
        (default ``False``).
    lyrics_mode : bool, optional
        Fetch and embed lyrics into media files (default ``False``).
    romaji_mode : bool, optional
        Prefer romaji-transliterated lyrics (default ``False``).
    zip_mode : bool, optional
        Package output files into a ZIP archive (default ``False``).
    create_m3u : bool, optional
        Generate an M3U playlist file (default ``False``).
    skip_existing_files : bool, optional
        Skip downloads whose output files already exist
        (default ``True``).
    max_video_resolution : str, optional
        Maximum video resolution (default ``'720p'``).
    audio_quality : str, optional
        Audio quality or container format (default ``'m4a'``).
    video_container : str, optional
        Video container format (default ``'mp4'``).
    video_codec : str, optional
        Video codec preference (default ``'default'``).
    header_style : str, optional
        Console header display style (default ``'default'``).
    progress_style : str, optional
        Progress bar display style (default ``'minimal'``).
    language : str, optional
        Interface language code (default ``'en'``).
    media_scanner_enabled : bool, optional
        Enable the local media file scanner (default ``False``).
    download_delay : int, optional
        Seconds to wait between successive downloads (default ``2``).
    max_retries : int, optional
        Maximum retry attempts on download failure (default ``3``).
    retry_delay : int, optional
        Seconds to wait between retry attempts (default ``2``).
    async_workers : int, optional
        Number of concurrent async workers (default ``3``).
    daemon_default_temp : bool, optional
        Use the system temporary directory for daemon staging
        (default ``True``).
    daemon_cleanup_interval : int, optional
        Interval in seconds between daemon cleanup passes
        (default ``3600``).
    verified_dependencies : bool, optional
        Whether external dependencies have been verified at startup
        (default ``False``).

    Example
    -------
    >>> cfg = AppConfig(
    ...     music_root='/data/music',
    ...     simple_mode=True,
    ...     max_video_resolution='1080p',
    ... )
    >>> cfg.audio.quality
    'm4a'

    See Also
    --------
    :class:`AudioConfig` : Audio sub-config (:attr:`audio`).
    :class:`VideoConfig` : Video sub-config (:attr:`video`).
    :class:`CoverConfig` : Cover-art sub-config (:attr:`cover`).
    :class:`LyricsConfig` : Lyrics sub-config (:attr:`lyrics`).
    :class:`DownloadConfig` : Download sub-config (:attr:`download`).
    :class:`LibraryConfig` : Library sub-config (:attr:`library`).
    :class:`SystemConfig` : System sub-config (:attr:`system`).
    :class:`DaemonConfig` : Daemon sub-config (:attr:`daemon`).
    :class:`SessionOverrides` : Per-request overrides.
    :class:`DownloadSession` : Per-request input model.
    """
    model_config = ConfigDict(extra='forbid')

    # Paths
    music_root: str = ""
    """Root directory for music downloads."""
    video_root: str = ""
    """Root directory for video downloads."""
    thumbnail_root: str = ""
    """Root directory for thumbnail output."""

    # Mode flags
    simple_mode: bool = False
    """Simplified single-file download mode."""
    async_mode: bool = False
    """Enable concurrent / asynchronous downloads."""
    quiet: bool = False
    """Suppress non-critical console output."""

    # Cover art
    smart_cover_mode: bool = True
    """Automatically select the best available thumbnail."""
    no_cover_mode: bool = False
    """Skip cover art processing entirely."""
    force_crop: bool = False
    """Always crop cover art to a square aspect ratio."""
    thumbnail_format: str = "jpg"
    """Thumbnail image format (``'jpg'``, ``'png'``, ``'webp'``)."""

    # Feature toggles
    group_mode: bool = False
    """Group downloads into sub-directories."""
    force_grouping_on_share: bool = False
    """Force grouping even when sharing via the staging server."""
    lyrics_mode: bool = False
    """Fetch and embed lyrics into media files."""
    romaji_mode: bool = False
    """Prefer romaji-transliterated lyrics."""
    zip_mode: bool = False
    """Package downloaded files into a ZIP archive."""
    create_m3u: bool = False
    """Generate an M3U playlist file."""
    skip_existing_files: bool = True
    """Skip downloads whose output file already exists."""

    # Media quality
    max_video_resolution: str = "720p"
    """Maximum video resolution (e.g. ``'720p'``, ``'1080p'``)."""
    audio_quality: str = "m4a"
    """Audio quality or container format (e.g. ``'m4a'``, ``'mp3'``)."""
    video_container: str = "mp4"
    """Video container format (e.g. ``'mp4'``, ``'mkv'``)."""
    video_codec: str = "default"
    """Video codec preference (e.g. ``'h264'``, ``'av1'``)."""

    # UI preferences
    header_style: str = "default"
    """Console header display style."""
    progress_style: str = "minimal"
    """Progress bar style (``'minimal'``, ``'detailed'``, ``'none'``)."""
    language: str = "en"
    """Interface language code."""

    # System
    media_scanner_enabled: bool = False
    """Enable the local media file scanner."""
    download_delay: int = 2
    """Seconds to wait between successive downloads."""
    max_retries: int = 3
    """Maximum retry attempts on download failure."""
    retry_delay: int = 2
    """Seconds to wait between retry attempts."""
    async_workers: int = 3
    """Number of concurrent async workers."""

    # Daemon
    daemon_default_temp: bool = True
    """Use the system temporary directory for daemon staging."""
    daemon_cleanup_interval: int = 3600
    """Interval in seconds between daemon cleanup passes."""

    # Dependencies
    verified_dependencies: bool = False
    """Whether external dependencies have been verified at startup."""

    # ------------------------------------------------------------------
    # Sub-config accessors — used by pipeline steps
    # ------------------------------------------------------------------

    @property
    def audio(self) -> AudioConfig:
        """Audio-specific options derived from the flat fields.

        Returns
        -------
        AudioConfig
            Configuration with ``quality`` set from :attr:`audio_quality`.

        Example
        -------
        >>> cfg = AppConfig(audio_quality='mp3')
        >>> cfg.audio.quality
        'mp3'

        See Also
        --------
        :class:`AudioConfig` : The returned model.
        :meth:`AppConfig.video` : Video sub-config accessor.
        """
        return AudioConfig(quality=self.audio_quality)

    @property
    def video(self) -> VideoConfig:
        """Video-specific options derived from the flat fields.

        Returns
        -------
        VideoConfig
            Configuration with ``container``, ``codec``, and
            ``max_resolution`` populated from the corresponding
            flat fields.

        Example
        -------
        >>> cfg = AppConfig(
        ...     video_container='mkv',
        ...     video_codec='av1',
        ...     max_video_resolution='1080p',
        ... )
        >>> cfg.video.container
        'mkv'

        See Also
        --------
        :class:`VideoConfig` : The returned model.
        :meth:`AppConfig.audio` : Audio sub-config accessor.
        """
        return VideoConfig(
            container=self.video_container,
            codec=self.video_codec,
            max_resolution=self.max_video_resolution,
        )

    @property
    def cover(self) -> CoverConfig:
        """Cover-art options derived from the flat fields.

        Returns
        -------
        CoverConfig
            Configuration with ``smart_mode``, ``disabled``, and
            ``force_crop`` populated from the corresponding flat
            fields.

        Example
        -------
        >>> cfg = AppConfig(no_cover_mode=True)
        >>> cfg.cover.disabled
        True

        See Also
        --------
        :class:`CoverConfig` : The returned model.
        :meth:`AppConfig.lyrics` : Lyrics sub-config accessor.
        """
        return CoverConfig(
            smart_mode=self.smart_cover_mode,
            disabled=self.no_cover_mode,
            force_crop=self.force_crop,
        )

    @property
    def lyrics(self) -> LyricsConfig:
        """Lyrics options derived from the flat fields.

        Returns
        -------
        LyricsConfig
            Configuration with ``enabled`` and ``romaji`` populated
            from :attr:`lyrics_mode` and :attr:`romaji_mode`.

        Example
        -------
        >>> cfg = AppConfig(lyrics_mode=True, romaji_mode=True)
        >>> cfg.lyrics.romaji
        True

        See Also
        --------
        :class:`LyricsConfig` : The returned model.
        :meth:`AppConfig.cover` : Cover-art sub-config accessor.
        """
        return LyricsConfig(enabled=self.lyrics_mode, romaji=self.romaji_mode)

    @property
    def download(self) -> DownloadConfig:
        """Download-behaviour options derived from the flat fields.

        Returns
        -------
        DownloadConfig
            Configuration with all five download-flavour fields
            populated from the corresponding flat fields.

        Example
        -------
        >>> cfg = AppConfig(simple_mode=False, progress_style='detailed')
        >>> cfg.download.progress_style
        'detailed'

        See Also
        --------
        :class:`DownloadConfig` : The returned model.
        :meth:`AppConfig.library` : Library sub-config accessor.
        """
        return DownloadConfig(
            simple_mode=self.simple_mode,
            quiet=self.quiet,
            async_mode=self.async_mode,
            skip_existing=self.skip_existing_files,
            progress_style=self.progress_style,
        )

    @property
    def library(self) -> LibraryConfig:
        """Library-path options derived from the flat fields.

        Returns
        -------
        LibraryConfig
            Configuration with all six library fields populated
            from the corresponding flat fields.

        Example
        -------
        >>> cfg = AppConfig(music_root='/music', group_mode='artist')
        >>> cfg.library.group_mode
        'artist'

        See Also
        --------
        :class:`LibraryConfig` : The returned model.
        :meth:`AppConfig.download` : Download sub-config accessor.
        """
        return LibraryConfig(
            music_root=self.music_root,
            video_root=self.video_root,
            thumbnail_root=self.thumbnail_root,
            group_mode=self.group_mode,
            create_m3u=self.create_m3u,
            zip_mode=self.zip_mode,
        )

    @property
    def system(self) -> SystemConfig:
        """System-level options derived from the flat fields.

        Returns
        -------
        SystemConfig
            Configuration with all five system fields populated
            from the corresponding flat fields.

        Example
        -------
        >>> cfg = AppConfig(max_retries=5, async_workers=8)
        >>> cfg.system.async_workers
        8

        See Also
        --------
        :class:`SystemConfig` : The returned model.
        :meth:`AppConfig.daemon` : Daemon sub-config accessor.
        """
        return SystemConfig(
            media_scanner_enabled=self.media_scanner_enabled,
            download_delay=self.download_delay,
            max_retries=self.max_retries,
            retry_delay=self.retry_delay,
            async_workers=self.async_workers,
        )

    @property
    def daemon(self) -> DaemonConfig:
        """Daemon-specific options derived from the flat fields.

        Returns
        -------
        DaemonConfig
            Configuration with ``default_temp`` and ``cleanup_interval``
            populated from the corresponding flat fields.

        Example
        -------
        >>> cfg = AppConfig(daemon_cleanup_interval=7200)
        >>> cfg.daemon.cleanup_interval
        7200

        See Also
        --------
        :class:`DaemonConfig` : The returned model.
        :meth:`AppConfig.system` : System sub-config accessor.
        """
        return DaemonConfig(
            default_temp=self.daemon_default_temp,
            cleanup_interval=self.daemon_cleanup_interval,
        )


# =============================================================================
# SessionOverrides — per-request overrides (CLI flags / daemon API)
# =============================================================================


class SessionOverrides(BaseModel):
    """CLI or daemon flags that override specific :class:`AppConfig` fields.

    Every field is optional — ``None`` / ``False`` means "use the base
    config value", while a non-``None`` / ``True`` value explicitly
    overrides it.

    Parameters
    ----------
    output_path : str | None, optional
        Override the output directory path (default ``None``).
    format : str | None, optional
        Override the media format or container (default ``None``).
    codec : str | None, optional
        Override the video codec (default ``None``).
    resolution : str | None, optional
        Override the maximum resolution (default ``None``).
    cut_range : tuple[float, float] | None, optional
        Trim range in seconds ``(start, end)`` (default ``None``).
    playlist_items : set[int] | None, optional
        Specific playlist item indices to download
        (default ``None``).
    group_folder : bool | str, optional
        Group folder override — ``True`` enables auto-naming,
        a string sets the folder name explicitly (default ``False``).
    lyrics : bool, optional
        Enable lyrics embedding (default ``False``).
    romaji : bool, optional
        Prefer romaji-transliterated lyrics (default ``False``).
    zip : bool, optional
        Enable ZIP packaging of output (default ``False``).
    m3u : bool, optional
        Enable M3U playlist generation (default ``False``).
    smart_cover : bool, optional
        Enable smart cover selection (default ``False``).
    no_cover : bool, optional
        Disable cover art entirely (default ``False``).
    force_crop : bool, optional
        Force square crop on cover art (default ``False``).
    quiet : bool, optional
        Suppress console output (default ``False``).
    async_mode : bool, optional
        Enable asynchronous download mode (default ``False``).

    Example
    -------
    >>> overrides = SessionOverrides(format='mp3', lyrics=True, quiet=True)
    >>> overrides.format
    'mp3'

    See Also
    --------
    :class:`AppConfig` : The configuration being overridden.
    :class:`DownloadSession` : Per-request input that holds overrides.
    :meth:`DownloadSession.config_updates` : Produces an override dict.
    :meth:`DownloadSession.merged_overrides` : Merges flat + structured.
    """
    output_path: Optional[str] = None
    format: Optional[str] = None
    codec: Optional[str] = None
    resolution: Optional[str] = None
    cut_range: Optional[tuple[float, float]] = None
    playlist_items: Optional[set[int]] = None
    group_folder: bool | str = False
    lyrics: bool = False
    romaji: bool = False
    zip: bool = False
    m3u: bool = False
    smart_cover: bool = False
    no_cover: bool = False
    force_crop: bool = False
    quiet: bool = False
    async_mode: bool = False


# =============================================================================
# DownloadSession — per-request input (CLI args / daemon API)
# =============================================================================


class DownloadSession(BaseModel):
    """Per-request input assembled by the CLI parser or daemon API.

    This model serves as the unified input for all download entry
    points.  Two construction paths exist:

    1. **CLI parser** — passes flat keyword arguments
       (``DownloadSession(url=..., format=..., ...)``).
    2. **Daemon / pipeline** — passes a structured
       :class:`SessionOverrides` via the ``overrides`` field.

    Parameters
    ----------
    url : str, optional
        Target URL to download (default ``''``).
    media_type : Literal['audio', 'video', 'thumbnail'], optional
        Requested media type (default ``'audio'``).
    share_after_download : bool, optional
        Start a share server after the download completes
        (default ``False``).
    is_temp_session : bool, optional
        Write output to a temporary staging directory
        (default ``False``).
    output_path : str | None, optional
        Flat-field alias for output directory override
        (default ``None``).
    format : str | None, optional
        Flat-field alias for format / container override
        (default ``None``).
    codec : str | None, optional
        Flat-field alias for codec override (default ``None``).
    resolution : str | None, optional
        Flat-field alias for resolution override (default ``None``).
    cut_range : tuple[float, float] | None, optional
        Flat-field alias for trim range in seconds
        (default ``None``).
    playlist_items : set[int] | None, optional
        Flat-field alias for playlist item filter
        (default ``None``).
    group_folder : bool | str, optional
        Flat-field alias for group folder override
        (default ``False``).
    lyrics : bool, optional
        Flat-field alias for lyrics embedding toggle
        (default ``False``).
    romaji : bool, optional
        Flat-field alias for romaji preference toggle
        (default ``False``).
    zip : bool, optional
        Flat-field alias for ZIP packaging toggle
        (default ``False``).
    m3u : bool, optional
        Flat-field alias for M3U generation toggle
        (default ``False``).
    smart_cover : bool, optional
        Flat-field alias for smart cover toggle
        (default ``False``).
    no_cover : bool, optional
        Flat-field alias for disable-cover toggle
        (default ``False``).
    force_crop : bool, optional
        Flat-field alias for force-crop toggle
        (default ``False``).
    quiet : bool, optional
        Flat-field alias for quiet-mode toggle
        (default ``False``).
    async_mode : bool, optional
        Flat-field alias for async-mode toggle
        (default ``False``).
    overrides : SessionOverrides, optional
        Structured per-request overrides
        (default ``SessionOverrides()``).

    Example
    -------
    >>> session = DownloadSession(
    ...     url='https://youtube.com/watch?v=abc123',
    ...     media_type='audio',
    ...     format='mp3',
    ... )
    >>> session.url
    'https://youtube.com/watch?v=abc123'

    See Also
    --------
    :class:`SessionOverrides` : Per-request override model.
    :class:`AppConfig` : Root configuration model.
    :meth:`config_updates` : Produces an :class:`AppConfig`-style dict.
    :meth:`merged_overrides` : Merges flat + structured overrides.
    """
    model_config = ConfigDict(extra='forbid')

    url: str = ''
    media_type: Literal['audio', 'video', 'thumbnail'] = 'audio'
    share_after_download: bool = False
    is_temp_session: bool = False

    # Flat fields — used by the CLI parser which passes them as
    # keyword arguments to ``DownloadSession(url=..., format=..., ...)``.
    output_path: Optional[str] = None
    format: Optional[str] = None
    codec: Optional[str] = None
    resolution: Optional[str] = None
    cut_range: Optional[tuple[float, float]] = None
    playlist_items: Optional[set[int]] = None
    group_folder: bool | str = False
    lyrics: bool = False
    romaji: bool = False
    zip: bool = False
    m3u: bool = False
    smart_cover: bool = False
    no_cover: bool = False
    force_crop: bool = False
    quiet: bool = False
    async_mode: bool = False

    # Structured overrides — used by the new pipeline.
    overrides: SessionOverrides = SessionOverrides()

    @field_validator('url')
    @classmethod
    def url_not_empty(cls, v: str) -> str:
        """Strip leading and trailing whitespace from the URL.

        Parameters
        ----------
        v : str
            The raw URL string to validate.

        Returns
        -------
        str
            The URL with whitespace removed.  Returns the original
            value unchanged when ``v`` is empty.

        Example
        -------
        >>> DownloadSession.url_not_empty('  https://example.com  ')
        'https://example.com'

        See Also
        --------
        :meth:`config_updates` : Produce an override dict from fields.
        """
        if v:
            return v.strip()
        return v

    def config_updates(self) -> dict[str, Any]:
        """Produce a flat override dict consumed by the dispatcher.

        Translates the flat CLI-style fields into
        :class:`AppConfig` field names so the configuration
        resolver can merge them into the base config.

        Returns
        -------
        dict[str, Any]
            Mapping of ``AppConfig`` field names to override values.
            Only fields holding non-default values are included.

        Raises
        ------
        AttributeError
            If a derived field name does not exist on
            :class:`AppConfig` (should not occur under normal usage).

        Example
        -------
        >>> session = DownloadSession(
        ...     url='...', format='mp3', quiet=True, smart_cover=True,
        ... )
        >>> session.config_updates()  # doctest: +SKIP
        {'audio_quality': 'mp3', 'quiet': True,
         'smart_cover_mode': True, 'no_cover_mode': False}

        See Also
        --------
        :meth:`merged_overrides` : Merge flat + structured overrides.
        :class:`AppConfig` : The target configuration model.
        :class:`SessionOverrides` : Structured override model.
        """
        updates: dict[str, Any] = {}
        if self.output_path:
            p = str(self.output_path)
            updates.update(music_root=p, video_root=p, thumbnail_root=p)
        if self.format:
            target = 'video_container' if self.media_type == 'video' else 'audio_quality'
            updates[target] = self.format
        if self.codec:
            updates['video_codec'] = self.codec
        if self.resolution:
            updates['max_video_resolution'] = self.resolution
        if self.smart_cover:
            updates.update(smart_cover_mode=True, no_cover_mode=False)
        if self.no_cover:
            updates.update(smart_cover_mode=False, no_cover_mode=True)
        if self.force_crop:
            updates['force_crop'] = True
        if self.lyrics:
            updates['lyrics_mode'] = True
        if self.romaji:
            updates['romaji_mode'] = True
        if self.zip:
            updates['zip_mode'] = True
        if self.group_folder:
            updates['group_mode'] = self.group_folder
        if self.m3u:
            updates['create_m3u'] = True
            updates['_auto_group'] = not bool(self.group_folder)
        if self.quiet:
            updates['quiet'] = True
        if self.async_mode:
            updates['async_mode'] = True
        return updates

    @property
    def merged_overrides(self) -> SessionOverrides:
        """Merge flat keyword fields with the structured ``overrides``.

        When a flat field carries a non-default value it takes
        precedence over the corresponding field in the structured
        :attr:`overrides`.  This allows the CLI parser (which sets
        flat fields) and the daemon / pipeline (which sets
        ``overrides``) to coexist harmoniously.

        Returns
        -------
        SessionOverrides
            A new :class:`SessionOverrides` instance with merged
            values from both flat and structured sources.

        Example
        -------
        >>> session = DownloadSession(
        ...     url='...',
        ...     lyrics=True,
        ...     overrides=SessionOverrides(quiet=True),
        ... )
        >>> merged = session.merged_overrides
        >>> merged.lyrics
        True
        >>> merged.quiet
        True

        See Also
        --------
        :meth:`config_updates` : Produces an :class:`AppConfig`-style dict.
        :class:`SessionOverrides` : The target override model.
        """
        flat = SessionOverrides(
            output_path=self.output_path,
            format=self.format,
            codec=self.codec,
            resolution=self.resolution,
            cut_range=self.cut_range,
            playlist_items=self.playlist_items,
            group_folder=self.group_folder,
            lyrics=self.lyrics,
            romaji=self.romaji,
            zip=self.zip,
            m3u=self.m3u,
            smart_cover=self.smart_cover,
            no_cover=self.no_cover,
            force_crop=self.force_crop,
            quiet=self.quiet,
            async_mode=self.async_mode,
        )
        merged: dict[str, Any] = {}
        for field in SessionOverrides.model_fields:
            flat_val = getattr(flat, field)
            field_info = SessionOverrides.model_fields[field]
            if flat_val != field_info.default:
                merged[field] = flat_val
            else:
                explicit_val = getattr(self.overrides, field)
                if explicit_val != field_info.default:
                    merged[field] = explicit_val
        return SessionOverrides(**merged)


# =============================================================================
# Pipeline data models (inter-step transfer objects)
# =============================================================================


class MediaInfo(BaseModel):
    """Extracted media information from yt-dlp.

    Contains the metadata returned by yt-dlp for a single media item:
    identifiers, title, artwork URLs, and optional playlist children.

    Parameters
    ----------
    id : str
        Platform-specific video / media ID.
    title : str
        Human-readable media title.
    url : str
        Direct or watch-page URL.
    duration : int, optional
        Duration in seconds (default ``0``).
    uploader : str, optional
        Channel or uploader display name (default ``''``).
    artist : str | None, optional
        Track artist name (default ``None``).
    track : str | None, optional
        Track name (default ``None``).
    album : str | None, optional
        Album name (default ``None``).
    description : str, optional
        Full video / track description (default ``''``).
    thumbnail : str | None, optional
        URL of the best available thumbnail (default ``None``).
    thumbnails : list[dict], optional
        All available thumbnail entries as returned by yt-dlp
        (default ``[]``).
    webpage_url : str, optional
        Original webpage URL (default ``''``).
    is_playlist : bool, optional
        ``True`` when this record represents a playlist container
        (default ``False``).
    entries : list[MediaInfo] | None, optional
        Child entries when ``is_playlist`` is ``True``
        (default ``None``).

    Example
    -------
    >>> info = MediaInfo(
    ...     id='abc123',
    ...     title='My Song',
    ...     url='https://youtube.com/watch?v=abc123',
    ...     duration=240,
    ...     artist='Some Artist',
    ... )
    >>> info.title
    'My Song'

    See Also
    --------
    :class:`DownloadedFile` : Post-download file metadata.
    :class:`LyricsMetadata` : Rich metadata from external providers.
    :class:`Classification` : Playlist / existing-result classification.
    """
    id: str
    title: str
    url: str
    duration: int = 0
    uploader: str = ''
    artist: Optional[str] = None
    track: Optional[str] = None
    album: Optional[str] = None
    description: str = ''
    thumbnail: Optional[str] = None
    thumbnails: list[dict] = []
    webpage_url: str = ''
    is_playlist: bool = False
    entries: Optional[list['MediaInfo']] = None


class DownloadedFile(BaseModel):
    """A successfully downloaded media file.

    Records the on-disk path, container format, title, and optionally
    links back to the original :class:`MediaInfo`.

    Parameters
    ----------
    path : str
        Absolute or relative filesystem path to the downloaded file.
    container : str
        File container format (e.g. ``'mp4'``, ``'m4a'``, ``'mp3'``).
    title : str
        Human-readable title of the downloaded media.
    artist : str | None, optional
        Artist name extracted from metadata (default ``None``).
    duration : int, optional
        Duration in seconds (default ``0``).
    info : MediaInfo | None, optional
        Reference to the original :class:`MediaInfo` that produced
        this download (default ``None``).

    Example
    -------
    >>> file = DownloadedFile(
    ...     path='/data/music/song.mp3',
    ...     container='mp3',
    ...     title='My Song',
    ...     artist='Artist',
    ... )

    See Also
    --------
    :class:`MediaInfo` : Pre-download media information.
    :class:`CoverResult` : Cover-art processing output.
    """
    path: str
    container: str
    title: str
    artist: Optional[str] = None
    duration: int = 0
    info: Optional[MediaInfo] = None


class LyricsMetadata(BaseModel):
    """Rich metadata returned by an external provider (iTunes, Genius, …).

    Contains artist, title, album information, genre, year, composer,
    and cover art URL fetched from an external metadata provider.

    Parameters
    ----------
    artist : str
        Artist or performer name.
    title : str
        Track title.
    album : str | None, optional
        Album name (default ``None``).
    album_artist : str | None, optional
        Album artist (may differ from track artist) (default ``None``).
    genre : str | None, optional
        Music genre (default ``None``).
    year : int | None, optional
        Release year (default ``None``).
    composer : str | None, optional
        Composer credit (default ``None``).
    track_number : str | None, optional
        Track number on the album (default ``None``).
    disc_number : str | None, optional
        Disc number for multi-disc releases (default ``None``).
    cover_url : str | None, optional
        URL to the cover artwork image (default ``None``).

    Example
    -------
    >>> meta = LyricsMetadata(
    ...     artist='Artist', title='Song',
    ...     album='Album', year=2024,
    ... )

    See Also
    --------
    :class:`LyricsConfig` : Configuration for lyrics fetching.
    :class:`CoverResult` : Cover-art processing result.
    """
    artist: str
    title: str
    album: Optional[str] = None
    album_artist: Optional[str] = None
    genre: Optional[str] = None
    year: Optional[int] = None
    composer: Optional[str] = None
    track_number: Optional[str] = None
    disc_number: Optional[str] = None
    cover_url: Optional[str] = None


class CoverResult(BaseModel):
    """Result of cover-art processing.

    Produced by the cover-art pipeline step and consumed by subsequent
    steps that embed or copy the artwork.

    Parameters
    ----------
    thumbnail_path : str
        Filesystem path to the processed cover-art image.
    metadata : LyricsMetadata | None, optional
        Rich metadata associated with the cover art
        (default ``None``).
    source : str, optional
        Source of the cover image (default ``'youtube'``).
        Typical values: ``'youtube'``, ``'itunes'``, ``'file'``.
    cropped : bool, optional
        Whether the image was cropped to a square
        (default ``False``).

    Example
    -------
    >>> result = CoverResult(
    ...     thumbnail_path='/tmp/cover.jpg',
    ...     source='itunes',
    ...     cropped=True,
    ... )

    See Also
    --------
    :class:`CoverConfig` : Configuration that drives cover processing.
    :class:`DownloadedFile` : The file this cover art belongs to.
    """
    thumbnail_path: str
    metadata: Optional[LyricsMetadata] = None
    source: str = 'youtube'
    cropped: bool = False


class DownloadTarget(BaseModel):
    """Resolved download target: output directory and format details.

    Assembled by the pipeline's target-resolution step and passed to
    yt-dlp as the effective download configuration.

    Parameters
    ----------
    output_dir : str
        Absolute path to the output directory for the download.
    filename_template : str
        Template string for output filenames (yt-dlp ``-o`` syntax).
    format_string : str
        yt-dlp format selection string (e.g. ``'bestaudio'``).
    postprocessors : list[dict], optional
        List of yt-dlp post-processor configurations
        (default ``[]``).
    cut_range : tuple[float, float] | None, optional
        Optional trim range in seconds ``(start, end)``
        (default ``None``).

    Example
    -------
    >>> target = DownloadTarget(
    ...     output_dir='/data/music',
    ...     filename_template='%(title)s.%(ext)s',
    ...     format_string='bestaudio',
    ... )

    See Also
    --------
    :class:`LibraryConfig` : Library path config used for resolution.
    :class:`DownloadedFile` : The file produced from this target.
    """
    output_dir: str
    filename_template: str
    format_string: str
    postprocessors: list[dict] = []
    cut_range: Optional[tuple[float, float]] = None


@dataclass
class Classification:
    """Whether the extracted content is a playlist and whether an
    existing download was found in the registry.

    This is the output of the classification pipeline step and
    determines whether the pipeline should short-circuit (when
    ``existing_result`` is set) or iterate over playlist entries
    (when ``is_playlist`` is ``True``).

    Parameters
    ----------
    is_playlist : bool, optional
        ``True`` when the resolved content is a playlist
        (default ``False``).
    existing_result : DownloadResult | None, optional
        When set, the download already exists in the registry and
        the pipeline may short-circuit (default ``None``).

    Example
    -------
    >>> c = Classification(is_playlist=False, existing_result=None)

    See Also
    --------
    :class:`DownloadResult` : The final download result model.
    :class:`PipelineContext` : Pipeline context that holds this.
    """
    is_playlist: bool = False
    existing_result: Optional[DownloadResult] = None


@dataclass
class PipelineContext:
    """Mutable context passed through pipeline steps.

    Created by :class:`MediaPipeline` and threaded through each step
    in sequence.  Each step reads its inputs from the context and
    writes its outputs back to it.

    Parameters
    ----------
    config : AppConfig
        Resolved application configuration (read-only during the
        pipeline run).
    url : str
        The URL being processed.
    target_dir : str
        Output directory path for the downloaded file.
    media_type : str, optional
        Media type (default ``'audio'``).
        Expected values: ``'audio'``, ``'video'``.
    is_youtube_music : bool, optional
        Whether the URL originates from YouTube Music
        (default ``False``).
    cut_range : tuple[float, float] | None, optional
        Optional trim range in seconds ``(start, end)``
        (default ``None``).
    download_type_label : str, optional
        Human-readable label for progress messages
        (default ``'Download'``).
    media_info : MediaInfo | None, optional
        Extracted media info — populated by the info step
        (default ``None``).
    classification : Classification | None, optional
        Playlist / existing-result classification — populated by
        the classification step (default ``None``).
    downloaded_file : DownloadedFile | None, optional
        Result of the download step (default ``None``).
    cover_result : CoverResult | None, optional
        Result of the cover-art step (default ``None``).
    lyrics_embedded : bool, optional
        Whether lyrics were successfully embedded
        (default ``False``).
    error : str | None, optional
        Error message if the pipeline failed (default ``None``).

    Example
    -------
    >>> ctx = PipelineContext(
    ...     config=AppConfig(),
    ...     url='https://youtube.com/watch?v=abc123',
    ...     target_dir='/tmp/downloads',
    ...     media_type='audio',
    ... )

    See Also
    --------
    :class:`MediaInfo` : Populated by the info step.
    :class:`Classification` : Populated by the classification step.
    :class:`DownloadedFile` : Populated by the download step.
    :class:`CoverResult` : Populated by the cover-art step.
    :class:`DownloadResult` : Final output of the pipeline.
    """
    config: AppConfig
    url: str
    target_dir: str
    media_type: str = "audio"
    is_youtube_music: bool = False
    cut_range: Optional[tuple[float, float]] = None
    download_type_label: str = "Download"

    # Populated by steps
    media_info: Optional[MediaInfo] = None
    classification: Optional[Classification] = None
    downloaded_file: Optional[DownloadedFile] = None
    cover_result: Optional[CoverResult] = None
    lyrics_embedded: bool = False
    error: Optional[str] = None


# =============================================================================
# DownloadResult — final output from download handlers
# =============================================================================


class DownloadResult(BaseModel):
    """Final output returned by every download entry point.

    Provides ``.get()`` / ``__getitem__`` / ``__contains__`` for
    callers that expect dict-style attribute access.

    Parameters
    ----------
    success : bool
        Whether the download completed successfully.
    file_path : str | None, optional
        Path to the downloaded file (default ``None``).
    skipped : bool, optional
        Whether the download was skipped (e.g. file exists)
        (default ``False``).
    suppress_error : bool, optional
        Whether the error (if any) should be hidden from the user
        (default ``False``).
    cancelled : bool, optional
        Whether the download was cancelled by the user
        (default ``False``).
    is_playlist : bool, optional
        Whether the result corresponds to a playlist
        (default ``False``).
    file_count : int | None, optional
        Number of files downloaded when ``is_playlist`` is ``True``
        (default ``None``).
    is_staging : bool, optional
        Whether the output is in a temporary staging directory
        (default ``False``).
    parent_dir : str | None, optional
        Parent directory of the output file (default ``None``).
    title : str | None, optional
        Human-readable title of the downloaded media
        (default ``None``).
    reason : str | None, optional
        Human-readable reason or status message
        (default ``None``).

    Example
    -------
    >>> result = DownloadResult(
    ...     success=True,
    ...     file_path='/data/music/song.mp3',
    ...     title='My Song',
    ... )
    >>> result['success']
    True
    >>> 'file_path' in result
    True

    See Also
    --------
    :class:`Classification` : May carry an ``existing_result``.
    :class:`PipelineContext` : Pipeline context that produces this.
    """
    model_config = ConfigDict(extra='forbid')

    success: bool
    file_path: Optional[str] = None
    skipped: bool = False
    suppress_error: bool = False
    cancelled: bool = False

    # Playlist
    is_playlist: bool = False
    file_count: Optional[int] = None

    # Staging (for share-temp)
    is_staging: bool = False
    parent_dir: Optional[str] = None

    # Metadata
    title: Optional[str] = None
    reason: Optional[str] = None

    def __getitem__(self, key: str):
        """Dict-style attribute access via ``result[key]``.

        Parameters
        ----------
        key : str
            Attribute name.

        Returns
        -------
        Any
            The value of the requested attribute.

        Raises
        ------
        AttributeError
            If the attribute does not exist on this model.

        Example
        -------
        >>> result = DownloadResult(success=True)
        >>> result['success']
        True

        See Also
        --------
        :meth:`get` : Dict-style ``.get()`` with a default.
        :meth:`__contains__` : ``key in result`` support.
        """
        return getattr(self, key)

    def get(self, key: str, default=None):
        """Dict-style attribute access with a fallback default.

        Parameters
        ----------
        key : str
            Attribute name.
        default : Any, optional
            Value returned when the attribute is not found
            (default ``None``).

        Returns
        -------
        Any
            The attribute value, or ``default`` if the attribute
            does not exist.

        Example
        -------
        >>> result = DownloadResult(success=True)
        >>> result.get('success')
        True
        >>> result.get('nonexistent', 'fallback')
        'fallback'

        See Also
        --------
        :meth:`__getitem__` : ``result[key]`` access.
        :meth:`__contains__` : ``key in result`` check.
        """
        return getattr(self, key, default)

    def __contains__(self, key: str) -> bool:
        """Check whether an attribute exists on this model.

        Parameters
        ----------
        key : str
            Attribute name to test.

        Returns
        -------
        bool
            ``True`` when the attribute exists, ``False`` otherwise.

        Example
        -------
        >>> result = DownloadResult(success=True)
        >>> 'success' in result
        True
        >>> 'missing' in result
        False

        See Also
        --------
        :meth:`__getitem__` : ``result[key]`` access.
        :meth:`get` : ``result.get(key, default)`` access.
        """
        return hasattr(self, key)


# =============================================================================
# CliResult — typed outcome of CLI parsing
# =============================================================================


class CliDownload(BaseModel):
    """CLI parse result indicating a download action.

    Returned when the user submits a URL for immediate download
    without entering an interactive menu.

    Parameters
    ----------
    mode : Literal['download'], optional
        Discriminant tag (default ``'download'``).
    session : DownloadSession
        The parsed download session with URL and options.
    force_recheck : bool, optional
        Force a registry recheck before downloading
        (default ``False``).

    Example
    -------
    >>> result = CliDownload(
    ...     session=DownloadSession(url='https://...'),
    ... )

    See Also
    --------
    :class:`CliSearch` : Search action parse result.
    :class:`CliMenu` : Menu action parse result.
    :class:`CliExit` : Exit action parse result.
    :class:`DownloadSession` : The embedded session model.
    """
    mode: Literal['download'] = 'download'
    session: DownloadSession
    force_recheck: bool = False


class CliSearch(BaseModel):
    """CLI parse result indicating a search action.

    Returned when the user provides a search query instead of
    a direct URL.

    Parameters
    ----------
    mode : Literal['search'], optional
        Discriminant tag (default ``'search'``).
    query : str
        The raw search query string.
    limit : int, optional
        Maximum number of search results to display
        (default ``5``).
    session : DownloadSession
        A partially-filled session (may carry format/quality
        preferences for when the user selects a result).
    force_recheck : bool, optional
        Force a registry recheck (default ``False``).

    Example
    -------
    >>> result = CliSearch(
    ...     query='never gonna give you up',
    ...     session=DownloadSession(),
    ... )

    See Also
    --------
    :class:`CliDownload` : Download action parse result.
    :class:`CliMenu` : Menu action parse result.
    :class:`CliExit` : Exit action parse result.
    """
    mode: Literal['search'] = 'search'
    query: str
    limit: int = 5
    session: DownloadSession
    force_recheck: bool = False


class CliMenu(BaseModel):
    """CLI parse result indicating the user requested the interactive menu.

    Parameters
    ----------
    mode : Literal['menu'], optional
        Discriminant tag (default ``'menu'``).

    Example
    -------
    >>> result = CliMenu()

    See Also
    --------
    :class:`CliDownload` : Download action parse result.
    :class:`CliSearch` : Search action parse result.
    :class:`CliExit` : Exit action parse result.
    """
    mode: Literal['menu'] = 'menu'


class CliExit(BaseModel):
    """CLI parse result indicating the user requested an exit.

    Parameters
    ----------
    mode : Literal['exit'], optional
        Discriminant tag (default ``'exit'``).

    Example
    -------
    >>> result = CliExit()

    See Also
    --------
    :class:`CliDownload` : Download action parse result.
    :class:`CliSearch` : Search action parse result.
    :class:`CliMenu` : Menu action parse result.
    """
    mode: Literal['exit'] = 'exit'


CliResult = Union[CliDownload, CliSearch, CliMenu, CliExit]
