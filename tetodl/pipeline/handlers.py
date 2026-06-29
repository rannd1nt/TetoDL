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

from ..constants import IS_TERMUX, RuntimeConfig
from ..core.cache import cache_metadata
from ..core.config import add_user_subfolder
from ..core.history import add_to_history
from ..core.models import AppConfig, DownloadedFile, DownloadResult, DownloadSession
from ..core.registry import registry
from ..ui.provider import UIProvider, NullUI
from ..utils.console import console
from ..utils.files import create_zip_archive, remove_nomedia_file
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
    """Download audio from a YouTube URL.

    Parameters
    ----------
    url : str
        YouTube or YouTube Music URL.
    session : DownloadSession
        CLI / daemon session parameters.
    config : AppConfig
        Resolved application configuration.
    ui : UIProvider
        User interface abstraction.

    Returns
    -------
    DownloadResult
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

    Parameters
    ----------
    url : str
        YouTube URL.
    session : DownloadSession
        CLI / daemon session parameters.
    config : AppConfig
        Resolved application configuration.
    ui : UIProvider
        User interface abstraction.

    Returns
    -------
    DownloadResult
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
    """Unified download execution for both audio and video modes."""
    cut_range = session.cut_range
    playlist_items = session.playlist_items
    group_folder = session.group_folder
    share_mode = session.share_after_download
    simple = config.simple_mode
    skip = config.skip_existing_files
    zip_mode = config.zip_mode
    is_youtube_music = is_youtube_music_url(url) if check_youtube_music and url else False

    extracted_label = "track" if media_type == "audio" else "video"

    # --- URL validation ---
    if not is_valid_youtube_url(url):
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
            return DownloadResult(success=False, reason="cancel")

    ui.clear()
    ui.header()

    # --- Registry check (single only) ---
    existing = _check_exists(url, registry_media_type, target_dir, ui)
    if existing and (media_type == "audio" or skip):
        return existing

    # --- Internet check ---
    if not check_internet():
        console.err(Keys.download.youtube.no_internet)
        ui.wait_and_clear_prompt()
        return DownloadResult(success=False, reason="no_internet")

    if config.smart_cover_mode and media_type == "audio":
        console.warn(Keys.download.youtube.smart_cover_info)

    if IS_TERMUX:
        remove_nomedia_file(target_dir)

    # --- URL expansion (playlist / single) ---
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
    """Download a single video / audio item via MediaPipeline."""
    pipeline = MediaPipeline(
        config=config,
        media_type=media_type,
        is_youtube_music=is_youtube_music,
        cut_range=cut_range,
    )

    downloaded = pipeline.run(url, target_dir)
    if downloaded is None:
        ui.wait_and_clear_prompt()
        return DownloadResult(success=False)

    # --- Post-processing ---
    _cache_metadata(url, downloaded)
    _add_to_history(url, downloaded, media_type, is_youtube_music, registry_media_type)
    _run_scanner(downloaded.path)

    if media_type == "audio" and is_youtube_music:
        console.ok(Keys.download.youtube.complete_metadata(title=downloaded.title))
    else:
        console.ok(Keys.download.youtube.complete(title=downloaded.title))
    ui.wait_and_clear_prompt()
    return DownloadResult(success=True, file_path=downloaded.path, title=downloaded.title)


def _check_exists(
    url: str,
    registry_media_type: str,
    target_dir: str,
    ui: UIProvider,
) -> Optional[DownloadResult]:
    """Return a positive result when the file is already in the registry."""
    if "list=" in url:
        return None
    video_id = extract_video_id(url)
    if not video_id:
        return None
    exists, metadata = registry.check_existing(video_id, registry_media_type, target_dir)
    if not exists:
        return None
    console.ok(Keys.download.youtube.file_exists)
    console.warn(Keys.download.youtube.exists_title(title=metadata.get("title")))
    console.warn(Keys.download.youtube.exists_path(path=metadata.get("file_path")))
    ui.wait_and_clear_prompt()
    return DownloadResult(
        success=True,
        file_path=metadata.get("file_path"),
        skipped=True,
    )


def _cache_metadata(url: str, downloaded: DownloadedFile) -> None:
    """Store metadata in the cache for future runs."""
    info = downloaded.info
    if not info:
        return
    cache_metadata(url, {
        "title": downloaded.title,
        "duration": downloaded.duration,
        "uploader": info.uploader,
        "artist": info.artist or "",
        "album": info.album or "",
        "track": info.track or "",
        "thumbnails": info.thumbnails,
    })


def _add_to_history(
    url: str,
    downloaded: DownloadedFile,
    media_type: str,
    is_youtube_music: bool,
    registry_media_type: str,
) -> None:
    """Register the download in history and registry."""
    info = downloaded.info
    video_id = info.id if info else extract_video_id(url)
    artist = info.artist or info.uploader or "Unknown Artist" if info else "Unknown Artist"
    album = info.album if info else None

    platform = "YouTube Music" if is_youtube_music else "YouTube Audio"
    history_title = f"{artist} - {downloaded.title}" if is_youtube_music else downloaded.title

    add_to_history(
        id=video_id,
        file_path=downloaded.path,
        success=True,
        title=history_title,
        content_type=registry_media_type,
        platform=platform,
        download_type="Single Track" if media_type == "audio" else "Single Video",
        duration=downloaded.duration,
        metadata={"artist": artist, "album": album, "title": downloaded.title},
    )


def _run_scanner(file_path: str) -> None:
    if not RuntimeConfig.MEDIA_SCANNER_ENABLED:
        return
    from ..media.scanner import scan_media_files
    scan_media_files(os.path.abspath(file_path))


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
    playlist_items: Optional[str] = None,
    group_folder: Optional[str | bool] = None,
    share_mode: bool = False,
    simple: bool = False,
    zip_mode: bool = False,
) -> DownloadResult:
    """Handle playlist / multi-item download."""
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
                is_staging=False, parent_dir=None, skipped=skipped,
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
        skipped=skipped,
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
    playlist_items: Optional[str] = None,
    alt_dirs: Optional[list[str]] = None,
    m3u_name: str = "Playlist",
) -> tuple[int, int, int]:
    """Download playlist items sequentially."""
    total = len(urls)
    success_count = 0
    failed_count = 0
    skipped_count = 0
    ordered_files: list[str] = []

    allowed = _parse_playlist_indices(playlist_items, total) if playlist_items else None

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
            console.warn(Keys.download.youtube.file_exists(title=result.get("title", "")))
            skipped_count += 1
        else:
            console.ok(Keys.download.youtube.success(title=result.get("title", "")))
            success_count += 1
            fpath = result.get("file_path")
            if fpath:
                ordered_files.append(os.path.basename(fpath))

        if i < total:
            delay = RuntimeConfig.DOWNLOAD_DELAY
            console.proc(Keys.download.youtube.wait_delay(delay=delay))
            time.sleep(delay)

    if RuntimeConfig.CREATE_M3U and ordered_files:
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
) -> tuple[int, int, int]:
    """Download playlist items concurrently via a thread pool."""
    max_workers = getattr(RuntimeConfig, "ASYNC_WORKERS", 3)
    if max_workers > 5:
        console.warn(color("Warning: High concurrency (>5) increases risk of IP Ban.", "y"))

    console.proc(Keys.media.async_mode(count=max_workers))
    total = len(urls)
    success_count = 0
    skipped_count = 0
    failed_count = 0
    results_store: list[Optional[str]] = [None] * total

    def _task(index: int, url: str) -> dict:
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
    if RuntimeConfig.CREATE_M3U and ordered:
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
    """Run MediaPipeline for one playlist item and return a result dict.

    Returns ``None`` on failure, or a dict with ``title``, ``file_path``,
    ``skipped`` on success.
    """
    pipeline = MediaPipeline(
        config=config,
        media_type=media_type,
        is_youtube_music=is_youtube_music,
        download_type_label=download_type,
        cut_range=cut_range,
    )

    try:
        downloaded = pipeline.run(url, target_dir)
    except KeyboardInterrupt:
        raise
    except Exception as exc:
        console.err(Keys.download.youtube.error_downloading(
            type=media_type, error=str(exc),
        ))
        return None

    if downloaded is None:
        return None

    _cache_metadata(url, downloaded)
    _add_to_history(url, downloaded, media_type, is_youtube_music, registry_media_type)
    _run_scanner(downloaded.path)

    return {
        "title": downloaded.title,
        "file_path": downloaded.path,
        "skipped": False,
    }


def _skip_registry_check(
    url: str,
    registry_media_type: str,
    dirs_to_check: list[str],
    ordered_files: Optional[list[str]] = None,
) -> bool:
    """Check the registry and return ``True`` if this URL can be skipped."""
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
    """Parse a playlist-range string (``'1,2,5-7'``) into a set of indices."""
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
