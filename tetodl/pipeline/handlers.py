"""
Facade entry points for download operations.

Replaces ``downloaders/youtube/handlers.py``.  External code
(``dispatch.py``, ``daemon/``) calls these functions instead of the
old module.
"""

import os
import random
import shutil
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from yt_dlp.utils import sanitize_filename

from ..constants import IS_TERMUX, YTDLP_CACHE_DIR
from ..core.config import add_user_subfolder
from ..core.models import AppConfig, DownloadResult, DownloadSession
from ..core.registry import registry
from ..ui.provider import UIProvider, NullUI
from ..utils.console import console
from ..utils.files import create_zip_archive, remove_nomedia_file
from ..utils.tracer import trace, traced
from ..utils.formatters import color
from ..utils.i18n_keys import Keys
from ..utils.network import (
    check_internet,
    is_valid_youtube_url,
    is_youtube_music_url,
)
from ..utils.processing import extract_all_urls_from_content, extract_video_id

from .pipeline import MediaPipeline


def download_audio_youtube(
    url: str,
    session: DownloadSession,
    config: AppConfig,
    ui: UIProvider = NullUI(),
) -> DownloadResult:
    """Download audio from a YouTube or YouTube Music URL.

    This is the main entry point for audio downloads.  Delegates to
    :func:`_execute` with ``target_root=config.music_root`` and
    ``media_type="audio"``.  Automatically detects YouTube Music URLs
    for enhanced metadata handling.

    Parameters
    ----------
    url : str
        YouTube or YouTube Music URL.
    session : DownloadSession
        CLI / daemon session parameters (cut range, playlist items,
        group folder, share mode, etc.).
    config : AppConfig
        Resolved application configuration.
    ui : UIProvider
        User interface abstraction.  Defaults to :class:`NullUI`.

    Returns
    -------
    DownloadResult
        Result with ``success``, ``file_path``, ``title``, and optional
        playlist fields.

    Raises
    ------
    None
        Errors are captured in the returned :class:`DownloadResult`.

    See Also
    --------
    :func:`download_video_youtube` : Video download equivalent.
    :func:`_execute` : Unified execution logic.
    :class:`MediaPipeline` : Per-item pipeline orchestrator.

    Example
    -------
    >>> from tetodl.core.models import AppConfig, DownloadSession
    >>> config = AppConfig()
    >>> session = DownloadSession()
    >>> result = download_audio_youtube(
    ...     "https://music.youtube.com/watch?v=dQw4w9WgXcQ",
    ...     session, config,
    ... )
    >>> isinstance(result, DownloadResult)
    True
    """
    return _execute(
        url=url,
        session=session,
        config=config,
        ui=ui,
        target_root=config.music_root,
        media_type="audio",
        registry_media_type="audio",
        check_youtube_music=True,
    )


def download_video_youtube(
    url: str,
    session: DownloadSession,
    config: AppConfig,
    ui: UIProvider = NullUI(),
) -> DownloadResult:
    """Download video from a YouTube URL.

    This is the main entry point for video downloads.  Delegates to
    :func:`_execute` with ``target_root=config.video_root`` and
    ``media_type="video"``.  YouTube Music detection is disabled for
    video downloads.

    Parameters
    ----------
    url : str
        YouTube URL.
    session : DownloadSession
        CLI / daemon session parameters (cut range, playlist items,
        group folder, share mode, etc.).
    config : AppConfig
        Resolved application configuration.
    ui : UIProvider
        User interface abstraction.  Defaults to :class:`NullUI`.

    Returns
    -------
    DownloadResult
        Result with ``success``, ``file_path``, ``title``, and optional
        playlist fields.

    Raises
    ------
    None
        Errors are captured in the returned :class:`DownloadResult`.

    See Also
    --------
    :func:`download_audio_youtube` : Audio download equivalent.
    :func:`_execute` : Unified execution logic.
    :class:`MediaPipeline` : Per-item pipeline orchestrator.

    Example
    -------
    >>> from tetodl.core.models import AppConfig, DownloadSession
    >>> config = AppConfig()
    >>> session = DownloadSession()
    >>> result = download_video_youtube(
    ...     "https://youtube.com/watch?v=dQw4w9WgXcQ",
    ...     session, config,
    ... )
    >>> isinstance(result, DownloadResult)
    True
    """
    return _execute(
        url=url,
        session=session,
        config=config,
        ui=ui,
        target_root=config.video_root,
        media_type="video",
        registry_media_type="video",
        check_youtube_music=False,
    )

@trace
def _search_ytmusic(
    query: str, target_duration_ms: int | None = None,
) -> str | None:
    import yt_dlp as yt

    opts: dict = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "simulate": True,
        "cachedir": YTDLP_CACHE_DIR,
    }

    artist_from_query = (query.split(" - ", 1)[1] if " - " in query else "").lower()
    spotify_title = query.split(" - ", 1)[0] if " - " in query else ""

    _BLOCKED = ("live", "lyrics", "acoustic", "cover", "karaoke", "instrumental", "lirik", "terjemahan", "subtitle")

    def _is_topic(entry: dict) -> bool:
        uploader = entry.get("uploader") or entry.get("channel") or ""
        return uploader.endswith(" - Topic")

    def _has_blocked_kw(title: str) -> bool:
        lower = title.lower()
        for kw in _BLOCKED:
            if kw in lower:
                return True
        return False

    def _title_clean(title: str) -> bool:
        lower = title.lower()
        for sep in (" - ", " \u2013 ", " \u2014 "):
            if artist_from_query and lower.startswith(artist_from_query + sep):
                lower = lower[len(artist_from_query) + len(sep):]
                break
        if "(" in lower or "[" in lower:
            return False
        return True

    def _duration_ok(entry: dict) -> bool:
        if not target_duration_ms or target_duration_ms <= 0:
            return True
        duration = entry.get("duration")
        if duration is None:
            return False
        diff = abs(duration * 1000 - target_duration_ms)
        return diff <= 2000

    def _title_word_overlap(yt_title: str) -> float:
        if not spotify_title:
            return 1.0
        yt_clean = yt_title.lower()
        for sep in (" - ", " \u2013 ", " \u2014 "):
            if sep in yt_clean:
                yt_clean = yt_clean.split(sep, 1)[1]
                break
        sp_words = spotify_title.lower().split()
        if not sp_words:
            return 1.0
        matched = sum(1 for w in sp_words if w in yt_clean)
        return matched / len(sp_words)

    def _search(search_url: str) -> list[dict]:
        try:
            with yt.YoutubeDL(opts) as ydl: # pyright: ignore[reportArgumentType]
                result = ydl.extract_info(search_url, download=False)
            candidates: list[dict] = []
            for entry in result.get("entries") or []:
                entry_url = entry.get("url") or ""
                if "/watch?" not in entry_url:
                    continue
                candidates.append(entry) # pyright: ignore[reportArgumentType]
            return candidates
        except Exception:
            return []

    def _log_candidates(phase: str, candidates: list[dict]) -> None:
        console.debug(f"===== Phase {phase} =====")
        if not candidates:
            console.debug("No candidates")
            return

        console.debug(f"{len(candidates)} candidates:")
        for i, entry in enumerate(candidates):
            title = entry.get("title", "?")
            dur = entry.get("duration")
            uploader = entry.get("uploader") or entry.get("channel") or "?"
            dur_str = f"{dur}s ({dur * 1000}ms)" if dur else "N/A"
            topic = " [TOPIC]" if _is_topic(entry) else ""
            overlap = _title_word_overlap(title)
            dur_ok = _duration_ok(entry)
            clean = _title_clean(title)
            blocked = _has_blocked_kw(title)
            console.debug(f"  [{i}] {title}{topic}")
            console.debug(f"      uploader={uploader}, duration={dur_str}, overlap={overlap:.2f}, dur_ok={dur_ok}, clean={clean}, blocked={blocked}")

    def _match(tier: int, label: str, entry: dict) -> str | None:
        url = entry.get("url", "")
        console.debug(f"  \u2713 TIER {tier} ({label}): {entry.get('title')!r} \u2192 {url}")
        return url

    # ===== Phase 1: Topic-biased search =====
    query_topic = f"ytsearch10:{query} topic"
    console.debug(f"Phase 1 search: {query_topic!r}")
    candidates1 = _search(query_topic)
    _log_candidates("1 (topic)", candidates1)

    if candidates1:
        for entry in candidates1:
            if _is_topic(entry) and _duration_ok(entry) and _title_word_overlap(entry.get("title", "")) >= 0.5 and _title_clean(entry.get("title", "")):
                return _match(1, "topic+dur+overlap+clean", entry)

        for entry in candidates1:
            if _is_topic(entry) and _duration_ok(entry) and _title_word_overlap(entry.get("title", "")) >= 0.3:
                return _match(2, "topic+dur+overlap", entry)

        for entry in candidates1:
            if _duration_ok(entry) and _title_word_overlap(entry.get("title", "")) >= 0.5:
                return _match(3, "dur+overlap>=0.5", entry)

        for entry in candidates1:
            if _duration_ok(entry) and _title_word_overlap(entry.get("title", "")) >= 0.3:
                return _match(4, "dur+overlap>=0.3", entry)

    # ===== Phase 2: General search =====
    query_general = f"ytsearch10:{query}"
    console.debug(f"Phase 2 search: {query_general!r}")
    candidates2 = _search(query_general)
    _log_candidates("2 (general)", candidates2)

    if candidates2:
        for entry in candidates2:
            if _is_topic(entry) and _duration_ok(entry) and _title_word_overlap(entry.get("title", "")) >= 0.5 and _title_clean(entry.get("title", "")):
                return _match(5, "topic+dur+overlap+clean", entry)

        for entry in candidates2:
            if _is_topic(entry) and _duration_ok(entry) and _title_word_overlap(entry.get("title", "")) >= 0.3:
                return _match(6, "topic+dur+overlap", entry)

        for entry in candidates2:
            if _duration_ok(entry) and _title_word_overlap(entry.get("title", "")) >= 0.5:
                return _match(7, "dur+overlap>=0.5", entry)

        for entry in candidates2:
            if _duration_ok(entry) and _title_word_overlap(entry.get("title", "")) >= 0.3:
                return _match(8, "dur+overlap>=0.3", entry)

    # ===== Phase 3: Nekat =====
    all_candidates = candidates1 + candidates2
    console.debug(f"Phase 3: {len(all_candidates)} total candidates")
    _log_candidates("3 (nekat)", all_candidates)

    if all_candidates:
        for entry in all_candidates:
            if _title_clean(entry.get("title", "")) and _title_word_overlap(entry.get("title", "")) >= 0.5:
                return _match(9, "clean+overlap>=0.5", entry)

        for entry in all_candidates:
            if _title_word_overlap(entry.get("title", "")) >= 0.5:
                return _match(10, "overlap>=0.5", entry)

        for entry in all_candidates:
            if _title_word_overlap(entry.get("title", "")) >= 0.3:
                return _match(11, "overlap>=0.3", entry)

        return _match(12, "last resort", all_candidates[0])

    console.debug("No candidates found, returning None")
    return None


@trace
def download_spotify(
    url: str,
    session: DownloadSession,
    config: AppConfig,
    ui: UIProvider = NullUI(),
) -> DownloadResult:
    from ..core.cache import get_cache
    from ..core.spotify import SpotifyResolver
    from ..core.spotify.errors import SpotifyParseError
    from ..core.registry import registry

    resolver = SpotifyResolver()
    try:
        container_name, tracks = resolver.resolve_meta(url)
    except SpotifyParseError as e:
        console.err(str(e))
        return DownloadResult(success=False, reason="spotify_error", file_path=None)

    if not tracks:
        return DownloadResult(success=False, reason="no_tracks", file_path=None)

    # Filter by --items (1-based indices against original Spotify track order)
    if session.playlist_items:
        tracks = [t for i, t in enumerate(tracks, 1) if i in session.playlist_items]
        if not tracks:
            console.err("No tracks match the specified --items range")
            return DownloadResult(success=False, reason="no_items_match", file_path=None)

    # Determine target directory for pre-check (mirror _handle_playlist logic)
    precheck_dirs = [config.music_root]
    if session.group_folder:
        if isinstance(session.group_folder, str):
            group_name = sanitize_filename(session.group_folder)
        elif container_name:
            group_name = sanitize_filename(container_name)
        else:
            group_name = None
        if group_name:
            precheck_dirs.append(os.path.join(config.music_root, group_name))

    # --- Pre-check by spotify_id (no network, before spinner) ---
    remaining_tracks: list = []
    skip_quiet = 0
    for t in tracks:
        if t.spotify_id:
            found_existing = False
            for d in precheck_dirs:
                exists, _ = registry.check_existing(
                    content_type="audio", target_folder=d, spotify_id=t.spotify_id,
                )
                if exists:
                    found_existing = True
                    break
            if found_existing:
                console.warn(f"Skipping existing track: {t.title}")
                skip_quiet += 1
                continue
        remaining_tracks.append(t)

    if skip_quiet:
        console.warn(f"Skipped {skip_quiet} already-downloaded track(s)")

    if not remaining_tracks:
        console.err("All tracks from this URL have already been downloaded")
        return DownloadResult(success=False, reason="all_existing", file_path=None)

    # --- Search YT Music for unresolved tracks (inside spinner) ---
    yt_match_cache = get_cache("yt_match")
    yt_urls: list[str] = []
    cover_urls: list[str] = []
    spotify_titles: list[str] = []
    spotify_artists: list[str] = []
    spotify_ids: list[str] = []

    with console.spin(Keys.download.spotify.searching_ytmusic):
        for t in remaining_tracks:
            sid = t.spotify_id
            cached = yt_match_cache.get(sid) if sid else None
            if cached:
                yt_urls.append(cached["y"])
                cover_urls.append(cached.get("c") or t.cover_url or "")
                spotify_titles.append(t.title)
                spotify_artists.append(t.artist)
                spotify_ids.append(sid or "")
                continue

            query = f"{t.title} - {t.artist}"
            found = _search_ytmusic(query, target_duration_ms=t.duration_ms)
            if found:
                yt_urls.append(found)
                if not t.cover_url and sid:
                    t.cover_url = resolver.fetch_track_cover(sid)
                cover_urls.append(t.cover_url or "")
                spotify_titles.append(t.title)
                spotify_artists.append(t.artist)
                spotify_ids.append(sid or "")
                if sid:
                    yt_match_cache.set(sid, {"y": found, "c": t.cover_url or ""})
            else:
                console.warn(f"Could not find YouTube result for: {query}")

    if not yt_urls:
        console.err("No tracks could be resolved from this Spotify URL")
        return DownloadResult(success=False, reason="no_results", file_path=None)

    if len(yt_urls) == 1:
        return _handle_single(
            url=yt_urls[0],
            cover_url=cover_urls[0] or None,
            target_dir=config.music_root,
            config=config,
            media_type="audio",
            registry_media_type="audio",
            is_youtube_music=True,
            ui=ui,
            cut_range=session.cut_range,
            simple=config.simple_mode,
            spotify_title=spotify_titles[0] if spotify_titles else None,
            spotify_artist=spotify_artists[0] if spotify_artists else None,
            spotify_id=spotify_ids[0] if spotify_ids else None,
        )

    return _handle_playlist(
        urls=yt_urls,
        cover_urls=cover_urls,
        content_title=container_name or "Spotify Playlist",
        total_items=len(yt_urls),
        target_dir=config.music_root,
        config=config,
        session=session,
        media_type="audio",
        registry_media_type="audio",
        is_youtube_music=True,
        ui=ui,
        cut_range=session.cut_range,
        playlist_items=None,
        group_folder=session.group_folder,
        share_mode=session.share_after_download,
        simple=config.simple_mode,
        zip_mode=config.zip_mode,
        spotify_titles=spotify_titles,
        spotify_artists=spotify_artists,
        spotify_ids=spotify_ids,
    )


@trace
def download_spotify_thumbnail(
    url: str,
    target_format: str = "jpg",
) -> DownloadResult:
    """Download cover art from a Spotify URL as a thumbnail.

    Parameters
    ----------
    url : str
        Spotify track, playlist, or album URL.
    target_format : str
        Desired output format (``'jpg'``, ``'png'``, or ``'webp'``).

    Returns
    -------
    DownloadResult
    """
    from ..core.spotify import SpotifyResolver
    from ..core.image_cache import fetch_image
    from yt_dlp.utils import sanitize_filename
    from ..core import config as cfg

    target_dir = cfg.thumbnail_root
    if not os.path.exists(target_dir):
        try:
            os.makedirs(target_dir, exist_ok=True)
        except OSError as e:
            console.err(f"Failed to create thumbnail directory: {e}")
            return DownloadResult(success=False)

    resolver = SpotifyResolver()
    try:
        tracks = resolver.resolve(url)
    except Exception as e:
        console.err(f"Failed to resolve Spotify URL: {e}")
        return DownloadResult(success=False)

    if not tracks:
        return DownloadResult(success=False, reason="no_tracks")

    track = tracks[0]
    if not track.cover_url:
        console.err("No cover art URL found for this track")
        return DownloadResult(success=False)

    filename = f"{sanitize_filename(f'{track.artist} - {track.title}')}.{target_format}"
    filepath = os.path.join(target_dir, filename)

    data = fetch_image(track.cover_url)
    if data is None:
        return DownloadResult(success=False, reason="download_failed")
    with open(filepath, "wb") as f:
        f.write(data)

    return DownloadResult(success=True, file_path=filepath, file_count=1)


# ==============================================================================
# Internal implementation
# ==============================================================================


@trace
def _execute(
    url: str,
    session: DownloadSession,
    config: AppConfig,
    ui: UIProvider,
    target_root: str,
    media_type: str,
    registry_media_type: str,
    check_youtube_music: bool,
) -> DownloadResult:
    """Unified download execution for both audio and video modes.

    Validates the URL, selects the target directory, checks the registry,
    verifies internet connectivity, expands playlist URLs, and dispatches
    to :func:`_handle_single` or :func:`_handle_playlist`.

    Parameters
    ----------
    url : str
        YouTube or YouTube Music URL.
    session : DownloadSession
        Session parameters.
    config : AppConfig
        Application configuration.
    ui : UIProvider
        User interface abstraction.
    target_root : str
        Root directory for the media type.
    media_type : str
        ``"audio"`` or ``"video"``.
    registry_media_type : str
        Media type for registry lookups.
    check_youtube_music : bool
        Whether to detect YouTube Music URLs.

    Returns
    -------
    DownloadResult
    """
    cut_range = session.cut_range
    playlist_items = session.playlist_items
    group_folder = session.group_folder
    share_mode = session.share_after_download
    simple = config.simple_mode
    zip_mode = config.zip_mode
    is_youtube_music = is_youtube_music_url(url) if check_youtube_music and url else False

    extracted_label = "track" if media_type == "audio" else "video"

    # --- URL validation ---
    if not is_valid_youtube_url(url):
        with traced('invalid URL'):
            console.err(Keys.download.youtube.invalid_url)
            ui.wait_and_clear_prompt()
            return DownloadResult(success=False, reason="invalid_url")

    # --- Target directory ---
    if simple:
        target_dir = target_root
    else:
        from ..ui.navigation import select_download_folder as _nav
        target_dir = _nav(target_root, media_type)
        if not target_dir:
            with traced('user cancelled folder selection'):
                return DownloadResult(success=False, reason="cancel")

    ui.clear()
    ui.header()

    # --- Registry check (instant — no network) ---
    skip = config.skip_existing_files
    existing = _check_exists(url, media_type, target_dir)
    if existing and (media_type == "audio" or skip):
        with traced('file exists in registry (pre-check)'):
            ui.wait_and_clear_prompt()
            return existing

    # --- Internet check ---
    if not check_internet():
        with traced('no internet'):
            console.err(Keys.download.youtube.no_internet)
            ui.wait_and_clear_prompt()
            return DownloadResult(success=False, reason="no_internet")

    if config.smart_cover_mode and media_type == "audio":
        console.warn(Keys.download.youtube.smart_cover_info)

    if IS_TERMUX:
        remove_nomedia_file(target_dir)

    # --- URL expansion (playlist / single) ---
    with traced('expanding URLs'):
        with console.spin(Keys.download.youtube.extracting):
            urls, content_title, total_items = extract_all_urls_from_content(url)
    console.ok(Keys.download.youtube.extracted(count=total_items, type=extracted_label))

    if total_items > 1:
        return _handle_playlist(
            urls=urls,
            content_title=content_title,
            total_items=total_items,
            target_dir=target_dir,
            config=config,
            session=session,
            media_type=media_type,
            registry_media_type=registry_media_type,
            is_youtube_music=is_youtube_music,
            ui=ui,
            cut_range=cut_range,
            playlist_items=playlist_items,
            group_folder=group_folder,
            share_mode=share_mode,
            simple=simple,
            zip_mode=zip_mode,
        )

    return _handle_single(
        url=urls[0],
        target_dir=target_dir,
        config=config,
        media_type=media_type,
        registry_media_type=registry_media_type,
        is_youtube_music=is_youtube_music,
        ui=ui,
        cut_range=cut_range,
        simple=simple,
    )


# ---------------------------------------------------------------------------
# Single-item helpers
# ---------------------------------------------------------------------------


@trace
def _handle_single(
    url: str,
    target_dir: str,
    config: AppConfig,
    media_type: str,
    registry_media_type: str,
    is_youtube_music: bool,
    ui: UIProvider,
    cut_range: Optional[tuple[float, float]] = None,
    simple: bool = False,
    cover_url: Optional[str] = None,
    spotify_title: Optional[str] = None,
    spotify_artist: Optional[str] = None,
    spotify_id: Optional[str] = None,
) -> DownloadResult:
    """Download a single video or audio item via :class:`MediaPipeline`.

    Parameters
    ----------
    url : str
        Media URL.
    target_dir : str
        Output directory.
    config : AppConfig
        Application configuration.
    media_type : str
        ``"audio"`` or ``"video"``.
    registry_media_type : str
        Media type for registry lookups.
    is_youtube_music : bool
        Whether the URL is from YouTube Music.
    ui : UIProvider
        User interface abstraction.
    cut_range : tuple[float, float] or None
        Optional (start, end) cut range in seconds.
    simple : bool
        When ``True``, use simplified output mode.
    cover_url : str or None
        Pre-resolved cover art URL (e.g. from Spotify embed).

    Returns
    -------
    DownloadResult
    """
    pipeline = MediaPipeline(config=config)

    result = pipeline.run(
        url, target_dir,
        media_type=media_type,
        is_youtube_music=is_youtube_music,
        cut_range=cut_range,
        cover_url=cover_url,
        spotify_title=spotify_title,
        spotify_artist=spotify_artist,
        spotify_id=spotify_id,
    )

    # Existing file found in registry
    if result.classification and result.classification.existing_result:
        ui.wait_and_clear_prompt()
        return result.classification.existing_result

    if result.downloaded_file is None:
        with traced('pipeline returned no file'):
            ui.wait_and_clear_prompt()
            return DownloadResult(success=False)

    if media_type == "audio" and is_youtube_music:
        console.ok(Keys.download.youtube.complete_metadata(title=result.downloaded_file.title))
    else:
        console.ok(Keys.download.youtube.complete(title=result.downloaded_file.title))
    ui.wait_and_clear_prompt()
    return DownloadResult(
        success=True,
        file_path=result.downloaded_file.path,
        title=result.downloaded_file.title,
    )





# ---------------------------------------------------------------------------
# Playlist helpers
# ---------------------------------------------------------------------------


def _handle_playlist(
    urls: list[str],
    content_title: str,
    total_items: int,
    target_dir: str,
    config: AppConfig,
    session: DownloadSession,
    media_type: str,
    registry_media_type: str,
    is_youtube_music: bool,
    ui: UIProvider,
    cut_range: Optional[tuple[float, float]] = None,
    playlist_items: set[int] | None = None,
    group_folder: Optional[str | bool] = None,
    share_mode: bool = False,
    simple: bool = False,
    zip_mode: bool = False,
    cover_urls: Optional[list[str]] = None,
    spotify_titles: Optional[list[str]] = None,
    spotify_artists: Optional[list[str]] = None,
    spotify_ids: Optional[list[str]] = None,
) -> DownloadResult:
    """Handle a playlist or multi-item download.

    Supports sequential and concurrent (async) download modes, optional
    sub-folder grouping, share-mode staging, and ZIP archive creation.

    Parameters
    ----------
    urls : list[str]
        Expanded list of individual media URLs.
    content_title : str
        Original playlist or content title.
    total_items : int
        Total number of items.
    cover_urls : list[str] or None
        Per-item cover art URLs (e.g. from Spotify embed).
    target_dir : str
        Base output directory.
    config : AppConfig
        Application configuration.
    session : DownloadSession
        Session parameters (async mode, etc.).
    media_type : str
        ``"audio"`` or ``"video"``.
    registry_media_type : str
        Media type for registry lookups.
    is_youtube_music : bool
        Whether URLs are from YouTube Music.
    ui : UIProvider
        User interface abstraction.
    cut_range : tuple[float, float] or None
        Cut range (ignored for playlists with a warning).
    playlist_items : str or None
        Playlist item range spec (e.g. ``"1,2,5-7"``).
    group_folder : str, bool, or None
        Custom sub-folder name or ``True`` to auto-generate.
    share_mode : bool
        When ``True`` items are downloaded to a staging directory.
    simple : bool
        Simplified output mode.
    zip_mode : bool
        When ``True`` the output folder is archived to a ZIP file.

    Returns
    -------
    DownloadResult
    """
    if cut_range:
        console.warn(color("Warning: '--cut' flag is ignored for playlists.", "y"))
        cut_range = None

    console.proc(
        Keys.download.youtube.found_playlist(
            count=total_items, type="track" if media_type == "audio" else "video",
            title=content_title,
        )
    )
    if media_type == "video":
        console.proc(Keys.download.youtube.max_resolution(resolution=config.max_video_resolution))

    safe_title = sanitize_filename(content_title)
    custom_group_name: Optional[str] = None
    m3u_name = content_title

    if isinstance(group_folder, str):
        custom_group_name = sanitize_filename(group_folder)
        m3u_name = group_folder
    elif group_folder:
        custom_group_name = safe_title

    final_dir = target_dir
    parent_if_staging: Optional[str] = None
    alt_dirs: list[str] = []
    is_staging = False

    if custom_group_name:
        final_dir = os.path.join(target_dir, custom_group_name)
        try:
            add_user_subfolder(target_dir, custom_group_name)
        except Exception:
            pass
    elif share_mode:
        is_staging = True
        parent_if_staging = target_dir
        candidate = os.path.join(target_dir, safe_title)
        if os.path.exists(candidate):
            final_dir = os.path.join(target_dir, f"{safe_title} (Share)")
            alt_dirs.append(candidate)
        else:
            final_dir = candidate
        alt_dirs.append(target_dir)

    if final_dir != target_dir and not os.path.exists(final_dir):
        os.makedirs(final_dir, exist_ok=True)

    async_mode = session.async_mode and media_type == "audio"

    if async_mode:
        success, skipped, failed = _playlist_concurrent(
            urls=urls,
            cover_urls=cover_urls,
            target_dir=final_dir,
            alt_dirs=alt_dirs,
            config=config,
            media_type=media_type,
            registry_media_type=registry_media_type,
            is_youtube_music=is_youtube_music,
            ui=ui,
            cut_range=cut_range,
            playlist_items=playlist_items,
            spotify_titles=spotify_titles,
            spotify_artists=spotify_artists,
            spotify_ids=spotify_ids,
        )
    else:
        success, skipped, failed = _playlist_sequential(
            urls=urls,
            cover_urls=cover_urls,
            target_dir=final_dir,
            config=config,
            media_type=media_type,
            registry_media_type=registry_media_type,
            is_youtube_music=is_youtube_music,
            ui=ui,
            cut_range=cut_range,
            playlist_items=playlist_items,
            alt_dirs=alt_dirs,
            m3u_name=m3u_name,
            spotify_titles=spotify_titles,
            spotify_artists=spotify_artists,
            spotify_ids=spotify_ids,
        )

    if is_staging and success == 0:
        if os.path.exists(final_dir) and not os.listdir(final_dir):
            console.warn(Keys.media.all_items_exist)
            try:
                shutil.rmtree(final_dir)
            except Exception:
                pass
            return DownloadResult(
                success=False, is_playlist=True, file_path=None,
                is_staging=False, parent_dir=None,                 skipped=bool(skipped),
                suppress_error=True,
            )

    final_path: str = final_dir
    if zip_mode:
        zip_path = create_zip_archive(final_dir)
        if zip_path:
            final_path = zip_path
            if is_staging or (share_mode and not custom_group_name):
                try:
                    shutil.rmtree(final_dir)
                except Exception:
                    pass

    return DownloadResult(
        success=success > 0,
        is_playlist=True,
        file_path=final_path,
        is_staging=is_staging,
        parent_dir=parent_if_staging,
        skipped=bool(skipped),
    )


def _playlist_sequential(
    urls: list[str],
    target_dir: str,
    config: AppConfig,
    media_type: str,
    registry_media_type: str,
    is_youtube_music: bool,
    ui: UIProvider,
    cut_range: Optional[tuple[float, float]] = None,
    playlist_items: set[int] | None = None,
    alt_dirs: Optional[list[str]] = None,
    m3u_name: str = "Playlist",
    cover_urls: Optional[list[str]] = None,
    spotify_titles: Optional[list[str]] = None,
    spotify_artists: Optional[list[str]] = None,
    spotify_ids: Optional[list[str]] = None,
) -> tuple[int, int, int]:
    """Download playlist items one at a time.

    Supports item range filtering via ``playlist_items``, registry
    skip checks, configurable inter-item delay, and M3U playlist
    generation.

    Parameters
    ----------
    urls : list[str]
        Individual item URLs.
    target_dir : str
        Output directory.
    cover_urls : list[str] or None
        Per-item cover art URLs.
    config : AppConfig
        Application configuration.
    media_type : str
        ``"audio"`` or ``"video"``.
    registry_media_type : str
        Registry media type.
    is_youtube_music : bool
        YouTube Music flag.
    ui : UIProvider
        User interface.
    cut_range : tuple[float, float] or None
        Optional cut range.
    playlist_items : str or None
        Range spec string.
    alt_dirs : list[str] or None
        Additional directories for registry checks.
    m3u_name : str
        Name for the generated M3U file.

    Returns
    -------
    tuple[int, int, int]
        ``(success_count, skipped_count, failed_count)``.
    """
    total = len(urls)
    success_count = 0
    failed_count = 0
    skipped_count = 0
    ordered_files: list[str] = []

    allowed = playlist_items

    dirs_to_check = [target_dir]
    if alt_dirs:
        dirs_to_check.extend(alt_dirs)

    for i, url in enumerate(urls, 1):
        if allowed is not None and i not in allowed:
            console.warn(Keys.media.skipping_item(index=i))
            continue

        console.proc(Keys.download.youtube.progress(current=i, total=total))

        if _skip_registry_check(url, registry_media_type, dirs_to_check, ordered_files):
            skipped_count += 1
            time.sleep(0.1)
            continue

        console.warn(Keys.download.youtube.downloading_url(
            url=url, type=media_type,
        ))

        result = _pipeline_item(
            url=url,
            cover_url=cover_urls[i - 1] if cover_urls else None,
            target_dir=target_dir,
            config=config,
            media_type=media_type,
            registry_media_type=registry_media_type,
            is_youtube_music=is_youtube_music,
            ui=ui,
            cut_range=cut_range,
            download_type="Playlist Track" if media_type == "audio" else "Playlist Video",
            spotify_title=spotify_titles[i - 1] if spotify_titles else None,
            spotify_artist=spotify_artists[i - 1] if spotify_artists else None,
            spotify_id=spotify_ids[i - 1] if spotify_ids else None,
        )

        if result is None:
            failed_count += 1
        elif result.get("skipped"):
            console.warn(Keys.download.youtube.file_exists_playlist(title=result.get("title", "")))
            skipped_count += 1
        else:
            console.ok(Keys.download.youtube.success(title=result.get("title", "")))
            success_count += 1
            fpath = result.get("file_path")
            if fpath:
                ordered_files.append(os.path.basename(fpath))

        if i < total:
            jitter = random.uniform(config.jitter_min, config.jitter_max)  # type: ignore[arg-type]
            console.proc(Keys.download.youtube.wait_jitter(jitter_min=config.jitter_min, jitter_max=config.jitter_max))
            time.sleep(jitter)

    if config.create_m3u and ordered_files:
        from ..utils.files import create_m3u8_playlist
        create_m3u8_playlist(target_dir, m3u_name, ordered_files)

    console.ok(Keys.download.youtube.summary(
        success=success_count, skipped=skipped_count,
        failed=failed_count, total=total, type=media_type,
    ))
    return success_count, skipped_count, failed_count


def _playlist_concurrent(
    urls: list[str],
    target_dir: str,
    alt_dirs: list[str],
    config: AppConfig,
    media_type: str,
    registry_media_type: str,
    is_youtube_music: bool,
    ui: UIProvider,
    cut_range: Optional[tuple[float, float]] = None,
    playlist_items: set[int] | None = None,
    cover_urls: Optional[list[str]] = None,
    spotify_titles: Optional[list[str]] = None,
    spotify_artists: Optional[list[str]] = None,
    spotify_ids: Optional[list[str]] = None,
) -> tuple[int, int, int]:
    """Download playlist items concurrently via a thread pool.

    Uses :class:`~concurrent.futures.ThreadPoolExecutor` with
    ``config.async_workers`` workers.  Registry skip checks are
    performed per item.  Handles :exc:`KeyboardInterrupt` with
    immediate executor shutdown.

    Parameters
    ----------
    urls : list[str]
        Individual item URLs.
    target_dir : str
        Output directory.
    alt_dirs : list[str]
        Additional directories for registry checks.
    cover_urls : list[str] or None
        Per-item cover art URLs.
    config : AppConfig
        Application configuration.
    media_type : str
        ``"audio"`` or ``"video"``.
    registry_media_type : str
        Registry media type.
    is_youtube_music : bool
        YouTube Music flag.
    ui : UIProvider
        User interface.
    cut_range : tuple[float, float] or None
        Optional cut range.

    Returns
    -------
    tuple[int, int, int]
        ``(success_count, skipped_count, failed_count)``.
    """
    max_workers = config.async_workers
    if max_workers > 5:
        console.warn(color("Warning: High concurrency (>5) increases risk of IP Ban.", "y"))

    console.proc(Keys.media.async_mode(count=max_workers))
    total = len(urls)
    success_count = 0
    skipped_count = 0
    failed_count = 0
    results_store: list[Optional[str]] = [None] * total

    def _task(index: int, url: str) -> dict:
        if playlist_items is not None and (index + 1) not in playlist_items:
            return {"status": "success", "skipped": True, "index": index}

        time.sleep(random.uniform(config.jitter_min, config.jitter_max))

        if _skip_registry_check(url, registry_media_type, [target_dir] + alt_dirs):
            return {"status": "success", "skipped": True, "index": index}

        result = _pipeline_item(
            url=url, cover_url=cover_urls[index] if cover_urls else None,
            target_dir=target_dir, config=config,
            media_type=media_type, registry_media_type=registry_media_type,
            is_youtube_music=is_youtube_music, ui=ui, cut_range=cut_range,
            download_type="Playlist Track" if media_type == "audio" else "Playlist Video",
            spotify_title=spotify_titles[index] if spotify_titles else None,
            spotify_artist=spotify_artists[index] if spotify_artists else None,
            spotify_id=spotify_ids[index] if spotify_ids else None,
        )

        if result is None:
            return {"status": "error", "index": index}
        return {
            "status": "success",
            "skipped": False,
            "index": index,
            "file_path": result.get("file_path"),
            "title": result.get("title"),
        }

    with console.context(is_quiet=True):
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_map = {executor.submit(_task, i, url): i for i, url in enumerate(urls)}

        try:
            for future in as_completed(future_map):
                r = future.result()
                if r["status"] == "success":
                    if r.get("skipped"):
                        skipped_count += 1
                    else:
                        success_count += 1
                    fp = r.get("file_path")
                    if fp:
                        results_store[r["index"]] = os.path.basename(fp)
                else:
                    failed_count += 1
        except KeyboardInterrupt:
            console.err(Keys.media.stopping_threads)
            executor.shutdown(wait=False)
            raise

    ordered = [f for f in results_store if f is not None]
    if config.create_m3u and ordered:
        from ..utils.files import create_m3u8_playlist
        create_m3u8_playlist(target_dir, "Playlist", ordered)

    console.ok(Keys.download.youtube.summary(
        success=success_count, skipped=skipped_count,
        failed=failed_count, total=total, type=media_type,
    ))
    return success_count, skipped_count, failed_count


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _pipeline_item(
    url: str,
    target_dir: str,
    config: AppConfig,
    media_type: str,
    registry_media_type: str,
    is_youtube_music: bool,
    ui: UIProvider,
    cut_range: Optional[tuple[float, float]] = None,
    download_type: str = "Single Track",
    cover_url: Optional[str] = None,
    spotify_title: Optional[str] = None,
    spotify_artist: Optional[str] = None,
    spotify_id: Optional[str] = None,
) -> Optional[dict]:
    """Run :class:`MediaPipeline` for one playlist item.

    Parameters
    ----------
    url : str
        Item URL.
    target_dir : str
        Output directory.
    config : AppConfig
        Application configuration.
    media_type : str
        ``"audio"`` or ``"video"``.
    registry_media_type : str
        Registry media type (unused, kept for API consistency).
    is_youtube_music : bool
        YouTube Music flag.
    ui : UIProvider
        User interface.
    cut_range : tuple[float, float] or None
        Optional cut range.
    download_type : str
        Label for the download type (e.g. ``"Playlist Track"``).
    cover_url : str or None
        Pre-resolved cover art URL (e.g. from Spotify embed).

    Returns
    -------
    dict or None
        Dict with ``title``, ``file_path``, ``skipped`` keys on success,
        or ``None`` on failure.
    """
    pipeline = MediaPipeline(config=config)

    try:
        result = pipeline.run(
            url, target_dir,
            media_type=media_type,
            is_youtube_music=is_youtube_music,
            cut_range=cut_range,
            download_type_label=download_type,
            cover_url=cover_url,
            spotify_title=spotify_title,
            spotify_artist=spotify_artist,
            spotify_id=spotify_id,
        )
    except KeyboardInterrupt:
        raise
    except Exception as exc:
        console.err(Keys.download.youtube.error_downloading(
            type=media_type, error=str(exc),
        ))
        return None

    if result.downloaded_file is None:
        return None

    return {
        "title": result.downloaded_file.title,
        "file_path": result.downloaded_file.path,
        "skipped": False,
    }


def _check_exists(
    url: str,
    media_type: str,
    target_dir: str,
) -> Optional[DownloadResult]:
    """Quick no-network registry check using URL-based video ID."""
    if "list=" in url:
        return None
    video_id = extract_video_id(url)
    if not video_id:
        return None
    exists, metadata = registry.check_existing(video_id, media_type, target_dir)
    if not exists:
        with traced('not in registry (pre-check)'):
            return None
    with traced('found in registry (pre-check)'):
        console.ok(Keys.download.youtube.file_exists)
        if metadata:
            console.warn(Keys.download.youtube.exists_title(
                title=metadata.get("title", ""),
            ))
            console.warn(Keys.download.youtube.exists_path(
                path=metadata.get("file_path", ""),
            ))
        return DownloadResult(
            success=True,
            file_path=metadata.get("file_path") if metadata else None,
            skipped=True,
        )


def _skip_registry_check(
    url: str,
    registry_media_type: str,
    dirs_to_check: list[str],
    ordered_files: Optional[list[str]] = None,
) -> bool:
    """Check the registry across directories and return ``True`` if the item exists."""
    video_id = extract_video_id(url)
    if not video_id:
        return False
    for check_dir in dirs_to_check:
        exists, metadata = registry.check_existing(video_id, registry_media_type, check_dir)
        if exists:
            if ordered_files is not None and metadata.get("file_path"):
                ordered_files.append(os.path.basename(metadata["file_path"]))
            return True
    return False


def _parse_playlist_indices(items: str, total: int) -> set[int]:
    """Parse a playlist-range string like ``'1,2,5-7'`` into a set of 1-based indices."""
    selected: set[int] = set()
    parts = items.split(",")
    for part in parts:
        if "-" in part:
            start_s, end_s = part.split("-", 1)
            start = int(start_s.strip())
            end = int(end_s.strip()) if end_s.strip() else total
            selected.update(range(start, end + 1))
        else:
            selected.add(int(part.strip()))
    return selected
