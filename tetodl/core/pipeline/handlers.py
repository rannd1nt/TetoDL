import os
import random
import shutil
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from yt_dlp.utils import sanitize_filename

from tetodl.core.domain.config import add_user_subfolder
from tetodl.core.domain.env import env
from tetodl.core.domain.models import AppConfig, DownloadResult, DownloadSession
from tetodl.core.domain.registry import registry
from tetodl.core.pipeline.metadata import resolve_artist_title
from tetodl.core.pipeline.runner import MediaPipeline
from tetodl.core.domain.provider import NullUI, UIProvider
from tetodl.utils.console import console
from tetodl.utils.files import create_zip_archive, remove_nomedia_file
from tetodl.utils.formatters import color
from tetodl.utils.i18n_keys import Keys
from tetodl.utils.network import (
    check_internet,
    is_valid_youtube_url,
    is_youtube_music_url,
)
from tetodl.utils.processing import extract_all_urls_from_content, extract_video_id
from tetodl.utils.tracer import traced


def _resolve_enrichment_flags(
    session: DownloadSession, is_youtube_music: bool, media_type: str,
) -> dict:
    """Resolve enrichment flags from session + source heuristics.

    Behavior A: any explicit flag (cover, metadata, lyrics) overrides
    auto-detection.  ``-N`` strips everything.

    Returns a dict with ``cover_mode``, ``metadata_mode``, and
    ``lyrics_mode`` keys set to ``True`` or ``False``.
    """
    # -N strips everything unconditionally
    if session.no_enrich:
        return {"cover_mode": False, "metadata_mode": False, "lyrics_mode": False}

    # Any explicit flag → override auto (Behavior A)
    explicit = session.cover or session.metadata or session.lyrics
    if explicit:
        return {
            "cover_mode": session.cover,
            "metadata_mode": session.metadata,
            "lyrics_mode": session.lyrics,
        }

    # No explicit flags → auto for YTM/Spotify
    if is_youtube_music and media_type == "audio":
        return {"cover_mode": True, "metadata_mode": True, "lyrics_mode": False}

    return {"cover_mode": False, "metadata_mode": False, "lyrics_mode": False}


def download_audio_youtube(
    url: str,
    session: DownloadSession,
    config: AppConfig,
    ui: UIProvider = NullUI(),
) -> DownloadResult:
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


def _search_ytmusic(
    query: str, target_duration_ms: int | None = None,
) -> str | None:
    import yt_dlp as yt

    opts: dict = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "simulate": True,
        "cachedir": env.get('ytdlp_cache_dir'),
    }

    artist_from_query = (query.split(" - ", 1)[1] if " - " in query else "").lower()
    spotify_title = query.split(" - ", 1)[0] if " - " in query else ""

    _BLOCKED = ("live", "lyrics", "acoustic", "cover", "karaoke", "instrumental", "lirik", "terjemahan", "subtitle")
    _LYRICS_KW = ("lyrics", "lirik", "terjemahan", "subtitle")

    def _is_topic(entry: dict) -> bool:
        uploader = entry.get("uploader") or entry.get("channel") or ""
        return uploader.endswith(" - Topic")

    def _has_blocked_kw(title: str) -> bool:
        lower = title.lower()
        for kw in _BLOCKED:
            if kw in lower:
                return True
        return False

    def _has_lyrics_kw(title: str) -> bool:
        lower = title.lower()
        for kw in _LYRICS_KW:
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

    def _duration_ok(entry: dict, tolerance_ms: int = 15000) -> bool:
        if not target_duration_ms or target_duration_ms <= 0:
            return True
        duration = entry.get("duration")
        if duration is None:
            return False
        diff = abs(duration * 1000 - target_duration_ms)
        return diff <= tolerance_ms

    def _artist_in_uploader(entry: dict) -> bool:
        if not artist_from_query:
            return False
        uploader = (entry.get("uploader") or entry.get("channel") or "").lower()
        return artist_from_query in uploader

    def _artist_in_title(yt_title: str) -> bool:
        if not artist_from_query:
            return False
        return artist_from_query in yt_title.lower()

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
            with yt.YoutubeDL(opts) as ydl:  # type: ignore[arg-type]
                result = ydl.extract_info(search_url, download=False)
            candidates: list[dict] = []
            for entry in result.get("entries") or []:  # type: ignore[union-attr]
                entry_url = entry.get("url") or ""
                if "/watch?" not in entry_url:
                    continue
                candidates.append(entry)  # type: ignore[arg-type]
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
        console.debug(f"  TIER {tier} ({label}): {entry.get('title')!r} -> {url}")
        return url

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
            if _is_topic(entry) and _duration_ok(entry) and _artist_in_uploader(entry):
                return _match(3, "topic+dur+artist_uploader", entry)
        for entry in candidates1:
            if _duration_ok(entry) and _artist_in_uploader(entry) and _artist_in_title(entry.get("title", "")):
                return _match(4, "dur+artist_uploader+artist_title", entry)
        for entry in candidates1:
            if _duration_ok(entry) and _title_word_overlap(entry.get("title", "")) >= 0.5:
                return _match(5, "dur+overlap>=0.5", entry)
        for entry in candidates1:
            if _duration_ok(entry) and _title_word_overlap(entry.get("title", "")) >= 0.3:
                return _match(6, "dur+overlap>=0.3", entry)
        for entry in candidates1:
            if _duration_ok(entry, 45000) and _title_word_overlap(entry.get("title", "")) >= 0.5:
                return _match(7, "dur_wide+overlap>=0.5", entry)
        for entry in candidates1:
            if _duration_ok(entry, 45000) and _artist_in_uploader(entry) and _artist_in_title(entry.get("title", "")):
                return _match(8, "dur_wide+artist_uploader+artist_title", entry)

    query_general = f"ytsearch10:{query}"
    console.debug(f"Phase 2 search: {query_general!r}")
    candidates2 = _search(query_general)
    _log_candidates("2 (general)", candidates2)

    if candidates2:
        for entry in candidates2:
            if _is_topic(entry) and _duration_ok(entry) and _title_word_overlap(entry.get("title", "")) >= 0.5 and _title_clean(entry.get("title", "")):
                return _match(9, "topic+dur+overlap+clean", entry)
        for entry in candidates2:
            if _is_topic(entry) and _duration_ok(entry) and _title_word_overlap(entry.get("title", "")) >= 0.3:
                return _match(10, "topic+dur+overlap", entry)
        for entry in candidates2:
            if _is_topic(entry) and _duration_ok(entry) and _artist_in_uploader(entry):
                return _match(11, "topic+dur+artist_uploader", entry)
        for entry in candidates2:
            if _duration_ok(entry) and _artist_in_uploader(entry) and _artist_in_title(entry.get("title", "")):
                return _match(12, "dur+artist_uploader+artist_title", entry)
        for entry in candidates2:
            if _duration_ok(entry) and _title_word_overlap(entry.get("title", "")) >= 0.5:
                return _match(13, "dur+overlap>=0.5", entry)
        for entry in candidates2:
            if _duration_ok(entry) and _title_word_overlap(entry.get("title", "")) >= 0.3:
                return _match(14, "dur+overlap>=0.3", entry)
        for entry in candidates2:
            if _duration_ok(entry, 45000) and _title_word_overlap(entry.get("title", "")) >= 0.5:
                return _match(15, "dur_wide+overlap>=0.5", entry)
        for entry in candidates2:
            if _duration_ok(entry, 45000) and _artist_in_uploader(entry) and _artist_in_title(entry.get("title", "")):
                return _match(16, "dur_wide+artist_uploader+artist_title", entry)

    all_candidates = candidates1 + candidates2
    console.debug(f"Phase 3: {len(all_candidates)} total candidates")
    _log_candidates("3 (nekat)", all_candidates)

    if all_candidates:
        for entry in all_candidates:
            if _duration_ok(entry) and _artist_in_uploader(entry) and _artist_in_title(entry.get("title", "")):
                return _match(17, "dur+artist_uploader+artist_title", entry)
        for entry in all_candidates:
            if _duration_ok(entry, 45000) and _has_lyrics_kw(entry.get("title", "")):
                return _match(18, "dur_wide+lyrics_kw", entry)
        for entry in all_candidates:
            if _duration_ok(entry) and _artist_in_uploader(entry):
                return _match(19, "dur+artist_uploader", entry)
        for entry in all_candidates:
            if _duration_ok(entry) and _artist_in_title(entry.get("title", "")):
                return _match(20, "dur+artist_title", entry)
        for entry in all_candidates:
            if _title_clean(entry.get("title", "")) and _title_word_overlap(entry.get("title", "")) >= 0.5:
                return _match(21, "clean+overlap>=0.5", entry)
        for entry in all_candidates:
            if _title_word_overlap(entry.get("title", "")) >= 0.5:
                return _match(22, "overlap>=0.5", entry)
        for entry in all_candidates:
            if _title_word_overlap(entry.get("title", "")) >= 0.3:
                return _match(23, "overlap>=0.3", entry)
        return _match(24, "last resort", all_candidates[0])

    console.debug("No candidates found, returning None")
    return None


def download_spotify(
    url: str,
    session: DownloadSession,
    config: AppConfig,
    ui: UIProvider = NullUI(),
) -> DownloadResult:
    from tetodl.core.clients.spotify import SpotifyResolver
    from tetodl.core.clients.spotify.errors import SpotifyParseError
    from tetodl.core.domain.cache import get_cache

    resolver = SpotifyResolver()
    try:
        container_name, tracks = resolver.resolve_meta(url)
    except SpotifyParseError as e:
        console.err(str(e))
        return DownloadResult(success=False, reason="spotify_error", file_path=None)

    if not tracks:
        return DownloadResult(success=False, reason="no_tracks", file_path=None)

    if session.playlist_items:
        tracks = [t for i, t in enumerate(tracks, 1) if i in session.playlist_items]
        if not tracks:
            console.err(Keys.download.youtube.no_tracks_match_range)
            return DownloadResult(success=False, reason="no_items_match", file_path=None)

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
                console.warn(Keys.download.youtube.skipping_existing_track(title=t.title))
                skip_quiet += 1
                continue
        remaining_tracks.append(t)

    if skip_quiet:
        console.warn(Keys.download.youtube.skipped_existing_tracks(count=skip_quiet))

    if not remaining_tracks:
        console.err(Keys.download.youtube.all_tracks_already_downloaded)
        existing_path = None
        for t in tracks:
            if t.spotify_id:
                for d in precheck_dirs:
                    exists, meta = registry.check_existing(
                        content_type="audio", target_folder=d, spotify_id=t.spotify_id,
                    )
                    if exists and meta:
                        existing_path = meta.get("file_path")
                        break
            if existing_path:
                break
        return DownloadResult(
            success=False, reason="all_existing",
            file_path=existing_path, skipped=True,
        )

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
                console.warn(Keys.download.youtube.could_not_find_youtube_result(query=query))

    if not yt_urls:
        console.err(Keys.download.youtube.no_tracks_resolved)
        return DownloadResult(success=False, reason="no_results", file_path=None)

    enrichment_flags = _resolve_enrichment_flags(session, True, "audio")

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
            enrichment_flags=enrichment_flags,
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
        enrichment_flags=enrichment_flags,
    )


def download_spotify_thumbnail(
    url: str,
    target_format: str = "jpg",
) -> DownloadResult:
    from yt_dlp.utils import sanitize_filename

    from tetodl.core.clients.spotify import SpotifyResolver
    from tetodl.core.cover import CoverService
    from tetodl.core.domain import config as cfg

    target_dir = cfg.thumbnail_root
    if not os.path.exists(target_dir):
        try:
            os.makedirs(target_dir, exist_ok=True)
        except OSError as e:
            console.err(Keys.download.youtube.failed_create_thumb_dir(error=e))
            return DownloadResult(success=False)

    resolver = SpotifyResolver()
    try:
        tracks = resolver.resolve(url)
    except Exception as e:
        console.err(Keys.download.youtube.failed_resolve_spotify_url(error=e))
        return DownloadResult(success=False)

    if not tracks:
        return DownloadResult(success=False, reason="no_tracks")

    track = tracks[0]
    if not track.cover_url:
        console.err(Keys.download.youtube.no_cover_url_found)
        return DownloadResult(success=False)

    filename = f"{sanitize_filename(f'{track.artist} - {track.title}')}.{target_format}"
    filepath = os.path.join(target_dir, filename)

    data = CoverService().fetch(track.cover_url)
    if data is None:
        return DownloadResult(success=False, reason="download_failed")
    with open(filepath, "wb") as f:
        f.write(data)

    return DownloadResult(success=True, file_path=filepath, file_count=1)


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
    cut_range = session.cut_range
    playlist_items = session.playlist_items
    group_folder = session.group_folder
    share_mode = session.share_after_download
    simple = config.simple_mode
    zip_mode = config.zip_mode
    is_youtube_music = is_youtube_music_url(url) if check_youtube_music and url else False

    extracted_label = "track" if media_type == "audio" else "video"

    if not is_valid_youtube_url(url):
        with traced('invalid URL'):
            console.err(Keys.download.youtube.invalid_url)
            ui.wait_and_clear_prompt()
            return DownloadResult(success=False, reason="invalid_url")

    if simple:
        target_dir = target_root
    else:
        target_dir = target_root

    ui.clear()
    ui.header()

    skip = config.skip_existing_files
    existing = _check_exists(url, media_type, target_dir)
    if existing and (media_type == "audio" or skip):
        with traced('file exists in registry (pre-check)'):
            if zip_mode and existing.file_path and os.path.exists(existing.file_path):
                zip_path = create_zip_archive(existing.file_path)
                if zip_path:
                    existing = DownloadResult(
                        success=True, file_path=zip_path,
                        title=existing.title, skipped=True,
                    )
            ui.wait_and_clear_prompt()
            return existing

    if not check_internet():
        with traced('no internet'):
            console.err(Keys.download.youtube.no_internet)
            ui.wait_and_clear_prompt()
            return DownloadResult(success=False, reason="no_internet")

    # Merge session enrichment flags into config
    enrichment_flags = _resolve_enrichment_flags(session, is_youtube_music, media_type)

    if env.get('is_termux'):
        remove_nomedia_file(target_dir)

    with traced('expanding URLs'), console.spin(Keys.download.youtube.extracting):
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
            enrichment_flags=enrichment_flags,
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
        zip_mode=zip_mode,
        enrichment_flags=enrichment_flags,
    )


def _handle_single(
    url: str,
    target_dir: str,
    config: AppConfig,
    media_type: str,
    registry_media_type: str,
    is_youtube_music: bool,
    ui: UIProvider,
    cut_range: tuple[float, float] | None = None,
    simple: bool = False,
    zip_mode: bool = False,
    cover_url: str | None = None,
    spotify_title: str | None = None,
    spotify_artist: str | None = None,
    spotify_id: str | None = None,
    enrichment_flags: dict | None = None,
) -> DownloadResult:
    pipeline = MediaPipeline(config=config)

    ctx_kw: dict = dict(
        media_type=media_type,
        is_youtube_music=is_youtube_music,
        cut_range=cut_range,
        cover_url=cover_url,
        spotify_title=spotify_title,
        spotify_artist=spotify_artist,
        spotify_id=spotify_id,
    )
    if enrichment_flags:
        ctx_kw.update(enrichment_flags)

    result = pipeline.run(url, target_dir, **ctx_kw)

    if result.classification and result.classification.existing_result:
        existing = result.classification.existing_result
        if zip_mode and existing.file_path and os.path.exists(existing.file_path):
            zip_path = create_zip_archive(existing.file_path)
            if zip_path:
                existing = DownloadResult(
                    success=True, file_path=zip_path,
                    title=existing.title, skipped=True,
                )
        ui.wait_and_clear_prompt()
        return existing

    if result.downloaded_file is None:
        with traced('pipeline returned no file'):
            ui.wait_and_clear_prompt()
            return DownloadResult(success=False)

    info = result.media_info
    resolved_artist, resolved_title = resolve_artist_title(info, result, result.cover_result) if info else ("", result.downloaded_file.title)
    display_title = f"{resolved_artist} - {resolved_title}" if resolved_artist else resolved_title

    if zip_mode:
        zip_path = create_zip_archive(result.downloaded_file.path)
        if zip_path:
            final_path = zip_path
        else:
            final_path = result.downloaded_file.path
    else:
        final_path = result.downloaded_file.path

    if media_type == "audio" and is_youtube_music:
        console.ok(Keys.download.youtube.complete_metadata(title=display_title))
    else:
        console.ok(Keys.download.youtube.complete(title=display_title))
    ui.wait_and_clear_prompt()
    return DownloadResult(
        success=True,
        file_path=final_path,
        title=display_title,
    )


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
    cut_range: tuple[float, float] | None = None,
    playlist_items: set[int] | None = None,
    group_folder: str | bool | None = None,
    share_mode: bool = False,
    simple: bool = False,
    zip_mode: bool = False,
    cover_urls: list[str] | None = None,
    spotify_titles: list[str] | None = None,
    spotify_artists: list[str] | None = None,
    spotify_ids: list[str] | None = None,
    enrichment_flags: dict | None = None,
) -> DownloadResult:
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
    custom_group_name: str | None = None
    m3u_name = content_title

    if isinstance(group_folder, str):
        custom_group_name = sanitize_filename(group_folder)
        m3u_name = group_folder
    elif group_folder:
        custom_group_name = safe_title

    final_dir = target_dir
    parent_if_staging: str | None = None
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
            enrichment_flags=enrichment_flags,
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
            enrichment_flags=enrichment_flags,
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
                is_staging=False, parent_dir=None, skipped=bool(skipped),
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
    cut_range: tuple[float, float] | None = None,
    playlist_items: set[int] | None = None,
    alt_dirs: list[str] | None = None,
    m3u_name: str = "Playlist",
    cover_urls: list[str] | None = None,
    spotify_titles: list[str] | None = None,
    spotify_artists: list[str] | None = None,
    spotify_ids: list[str] | None = None,
    enrichment_flags: dict | None = None,
) -> tuple[int, int, int]:
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
            enrichment_flags=enrichment_flags,
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
            jitter = random.uniform(config.jitter_min, config.jitter_max)
            console.proc(Keys.download.youtube.wait_jitter(jitter_min=int(config.jitter_min), jitter_max=int(config.jitter_max)))
            time.sleep(jitter)

    if config.create_m3u and ordered_files:
        from tetodl.utils.files import create_m3u8_playlist
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
    cut_range: tuple[float, float] | None = None,
    playlist_items: set[int] | None = None,
    cover_urls: list[str] | None = None,
    spotify_titles: list[str] | None = None,
    spotify_artists: list[str] | None = None,
    spotify_ids: list[str] | None = None,
    enrichment_flags: dict | None = None,
) -> tuple[int, int, int]:
    max_workers = config.async_workers
    if max_workers > 5:
        console.warn(color("Warning: High concurrency (>5) increases risk of IP Ban.", "y"))

    console.proc(Keys.media.async_mode(count=max_workers))
    total = len(urls)
    success_count = 0
    skipped_count = 0
    failed_count = 0
    results_store: list[str | None] = [None] * total

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
            enrichment_flags=enrichment_flags,
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
        from tetodl.utils.files import create_m3u8_playlist
        create_m3u8_playlist(target_dir, "Playlist", ordered)

    console.ok(Keys.download.youtube.summary(
        success=success_count, skipped=skipped_count,
        failed=failed_count, total=total, type=media_type,
    ))
    return success_count, skipped_count, failed_count


def _pipeline_item(
    url: str,
    target_dir: str,
    config: AppConfig,
    media_type: str,
    registry_media_type: str,
    is_youtube_music: bool,
    ui: UIProvider,
    cut_range: tuple[float, float] | None = None,
    download_type: str = "Single Track",
    cover_url: str | None = None,
    spotify_title: str | None = None,
    spotify_artist: str | None = None,
    spotify_id: str | None = None,
    enrichment_flags: dict | None = None,
) -> dict | None:
    pipeline = MediaPipeline(config=config)

    ctx_kw: dict = dict(
        media_type=media_type,
        is_youtube_music=is_youtube_music,
        cut_range=cut_range,
        download_type_label=download_type,
        cover_url=cover_url,
        spotify_title=spotify_title,
        spotify_artist=spotify_artist,
        spotify_id=spotify_id,
    )
    if enrichment_flags:
        ctx_kw.update(enrichment_flags)

    try:
        result = pipeline.run(url, target_dir, **ctx_kw)
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
) -> DownloadResult | None:
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
    ordered_files: list[str] | None = None,
) -> bool:
    video_id = extract_video_id(url)
    if not video_id:
        return False
    for check_dir in dirs_to_check:
        exists, metadata = registry.check_existing(video_id, registry_media_type, check_dir)
        if exists:
            if ordered_files is not None and metadata.get("file_path"): # pyright: ignore[reportOptionalMemberAccess]
                ordered_files.append(os.path.basename(metadata["file_path"])) # pyright: ignore[reportOptionalSubscript]
            return True
    return False


def _parse_playlist_indices(items: str, total: int) -> set[int]:
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
