"""
Pydantic models for TetoDL data flow.
"""

from pydantic import BaseModel, ConfigDict, field_validator
from typing import Any, Optional, Literal, Union


# =============================================================================
# Domain-specific sub-configs
# =============================================================================

class AudioConfig(BaseModel):
    """Audio-specific download options."""
    quality: str = 'm4a'


class VideoConfig(BaseModel):
    """Video-specific download options."""
    container: str = 'mp4'
    codec: str = 'h264'
    max_resolution: str = '720p'


class CoverConfig(BaseModel):
    """Cover art processing options."""
    smart_mode: bool = True
    disabled: bool = False
    force_crop: bool = False


class LyricsConfig(BaseModel):
    """Lyrics embedding options."""
    enabled: bool = False
    romaji: bool = False


class DownloadConfig(BaseModel):
    """Base download behaviour."""
    simple_mode: bool = True
    quiet: bool = False
    async_mode: bool = False
    skip_existing: bool = True
    progress_style: str = 'minimal'


class LibraryConfig(BaseModel):
    """Storage paths and library structure."""
    music_root: str = ""
    video_root: str = ""
    thumbnail_root: str = ""
    group_mode: bool | str = False
    create_m3u: bool = False
    zip_mode: bool = False


class ThumbnailConfig(BaseModel):
    """Thumbnail format options."""
    format: str = 'jpg'


class SystemConfig(BaseModel):
    """System-level settings (not overridable per request)."""
    media_scanner_enabled: bool = False
    download_delay: int = 2
    max_retries: int = 3
    retry_delay: int = 2
    async_workers: int = 3


class DaemonConfig(BaseModel):
    """Daemon-specific settings."""
    default_temp: bool = True
    cleanup_interval: int = 3600


# =============================================================================
# AppConfig — root application configuration
# =============================================================================

class AppConfig(BaseModel):
    """Root configuration for a TetoDL session, loaded from ``config.json``
    and merged with per-request overrides via :class:`ConfigResolver`.

    The flat fields map directly to the JSON keys produced by
    :func:`core.config.load_app_config`.  Domain-specific sub-configs
    (:class:`AudioConfig`, :class:`CoverConfig`, …) are available as
    properties and will be consumed by pipeline steps.
    """
    model_config = ConfigDict(extra='forbid')

    # Paths
    music_root: str = ""
    video_root: str = ""
    thumbnail_root: str = ""

    # Mode flags
    simple_mode: bool = False
    async_mode: bool = False
    quiet: bool = False

    # Cover art
    smart_cover_mode: bool = True
    no_cover_mode: bool = False
    force_crop: bool = False
    thumbnail_format: str = "jpg"

    # Feature toggles
    group_mode: bool = False
    force_grouping_on_share: bool = False
    lyrics_mode: bool = False
    romaji_mode: bool = False
    zip_mode: bool = False
    create_m3u: bool = False
    skip_existing_files: bool = True

    # Media quality
    max_video_resolution: str = "720p"
    audio_quality: str = "m4a"
    video_container: str = "mp4"
    video_codec: str = "default"

    # UI preferences
    header_style: str = "default"
    progress_style: str = "minimal"
    language: str = "en"

    # System
    media_scanner_enabled: bool = False
    download_delay: int = 2
    max_retries: int = 3
    retry_delay: int = 2
    async_workers: int = 3

    # Daemon
    daemon_default_temp: bool = True
    daemon_cleanup_interval: int = 3600

    # Dependencies
    verified_dependencies: bool = False
    spotify_available: bool = False

    # Spotify credentials
    spotify_client_id: Optional[str] = None
    spotify_client_secret: Optional[str] = None

    # ------------------------------------------------------------------
    # Sub-config accessors — used by pipeline steps
    # ------------------------------------------------------------------

    @property
    def audio(self) -> AudioConfig:
        """Audio-specific options derived from the flat fields."""
        return AudioConfig(quality=self.audio_quality)

    @property
    def video(self) -> VideoConfig:
        """Video-specific options derived from the flat fields."""
        return VideoConfig(
            container=self.video_container,
            codec=self.video_codec,
            max_resolution=self.max_video_resolution,
        )

    @property
    def cover(self) -> CoverConfig:
        """Cover-art options derived from the flat fields."""
        return CoverConfig(
            smart_mode=self.smart_cover_mode,
            disabled=self.no_cover_mode,
            force_crop=self.force_crop,
        )

    @property
    def lyrics(self) -> LyricsConfig:
        """Lyrics options derived from the flat fields."""
        return LyricsConfig(enabled=self.lyrics_mode, romaji=self.romaji_mode)

    @property
    def download(self) -> DownloadConfig:
        """Download-behaviour options derived from the flat fields."""
        return DownloadConfig(
            simple_mode=self.simple_mode,
            quiet=self.quiet,
            async_mode=self.async_mode,
            skip_existing=self.skip_existing_files,
            progress_style=self.progress_style,
        )

    @property
    def library(self) -> LibraryConfig:
        """Library-path options derived from the flat fields."""
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
        """System-level options derived from the flat fields."""
        return SystemConfig(
            media_scanner_enabled=self.media_scanner_enabled,
            download_delay=self.download_delay,
            max_retries=self.max_retries,
            retry_delay=self.retry_delay,
            async_workers=self.async_workers,
        )

    @property
    def daemon(self) -> DaemonConfig:
        """Daemon-specific options derived from the flat fields."""
        return DaemonConfig(
            default_temp=self.daemon_default_temp,
            cleanup_interval=self.daemon_cleanup_interval,
        )


# =============================================================================
# SessionOverrides — per-request overrides (CLI flags / daemon API)
# =============================================================================

class SessionOverrides(BaseModel):
    """CLI or daemon flags that override specific :class:`AppConfig` fields.

    Every field is optional — ``None`` / ``False`` means "use the base config
    value", while a non-``None`` / ``True`` value explicitly overrides it.
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

    Attributes
    ----------
    url : str
        Target URL to download.
    media_type : Literal['audio', 'video', 'thumbnail']
        Requested media type.
    overrides : SessionOverrides
        Per-request overrides — populated either from flat keyword arguments
        (the CLI parser passes them directly) or from the structured
        ``overrides`` field.
    share_after_download : bool
        Start a share server after the download finishes.
    is_temp_session : bool
        Write output to a temporary staging directory.
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
        if v:
            return v.strip()
        return v

    def config_updates(self) -> dict[str, Any]:
        """Produce a flat override dict consumed by the dispatcher.

        Returns
        -------
        dict[str, Any]
            Mapping of ``AppConfig`` field names to override values.
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
        """Merge flat keyword fields with the structured ``overrides`` field.

        When a flat field has a non-default value it takes precedence;
        otherwise the structured ``overrides`` value is used.
        """  # Two paths feed DownloadSession: CLI parser uses flat kwargs,
             # pipeline uses .overrides — this property unifies them.
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
    """Extracted media information from yt-dlp."""
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
    """A successfully downloaded media file."""
    path: str
    container: str
    title: str
    artist: Optional[str] = None
    duration: int = 0
    info: Optional[MediaInfo] = None


class LyricsMetadata(BaseModel):
    """Rich metadata returned by an external provider (iTunes, Genius)."""
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
    """Result of cover-art processing."""
    thumbnail_path: str
    metadata: Optional[LyricsMetadata] = None
    source: str = 'youtube'
    cropped: bool = False


class DownloadTarget(BaseModel):
    """Resolved download target: output directory + format options."""
    output_dir: str
    filename_template: str
    format_string: str
    postprocessors: list[dict] = []
    cut_range: Optional[tuple[float, float]] = None


# =============================================================================
# DownloadResult — final output from download handlers
# =============================================================================

class DownloadResult(BaseModel):
    """Final output returned by every download entry point.

    Provides ``.get()`` / ``__getitem__`` / ``__contains__`` for callers
    that expect dict-style attribute access.
    """  # TODO: remove .get()/.getitem() once all internal callers use attributes
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
        return getattr(self, key)

    def get(self, key: str, default=None):
        return getattr(self, key, default)

    def __contains__(self, key: str) -> bool:
        return hasattr(self, key)


# =============================================================================
# CliResult — typed outcome of CLI parsing
# =============================================================================

class CliDownload(BaseModel):
    mode: Literal['download'] = 'download'
    session: DownloadSession
    force_recheck: bool = False

class CliSearch(BaseModel):
    mode: Literal['search'] = 'search'
    query: str
    limit: int = 5
    session: DownloadSession
    force_recheck: bool = False

class CliMenu(BaseModel):
    mode: Literal['menu'] = 'menu'

class CliExit(BaseModel):
    mode: Literal['exit'] = 'exit'

CliResult = Union[CliDownload, CliSearch, CliMenu, CliExit]
