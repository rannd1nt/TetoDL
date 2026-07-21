"""
Facade entry points for download operations.

Replaces ``downloaders/youtube/handlers.py``.  External code
(``dispatch.py``, ``daemon/``) calls these functions instead of the
old module.
"""

import os
import shutil
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from yt_dlp.utils import sanitize_filename

from ..constants import IS_TERMUX
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
            target_dir=final_dir,
            alt_dirs=alt_dirs,
            config=config,
            media_type=media_type,
            registry_media_type=registry_media_type,
            is_youtube_music=is_youtube_music,
            ui=ui,
            cut_range=cut_range,
            playlist_items=playlist_items,
        )
    else:
        success, skipped, failed = _playlist_sequential(
            urls=urls,
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
            target_dir=target_dir,
            config=config,
            media_type=media_type,
            registry_media_type=registry_media_type,
            is_youtube_music=is_youtube_music,
            ui=ui,
            cut_range=cut_range,
            download_type="Playlist Track" if media_type == "audio" else "Playlist Video",
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
            delay = config.download_delay
            console.proc(Keys.download.youtube.wait_delay(delay=delay))
            time.sleep(delay)

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

        import random
        time.sleep(random.uniform(0.1, 1.0))

        if _skip_registry_check(url, registry_media_type, [target_dir] + alt_dirs):
            return {"status": "success", "skipped": True, "index": index}

        result = _pipeline_item(
            url=url, target_dir=target_dir, config=config,
            media_type=media_type, registry_media_type=registry_media_type,
            is_youtube_music=is_youtube_music, ui=ui, cut_range=cut_range,
            download_type="Playlist Track" if media_type == "audio" else "Playlist Video",
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
