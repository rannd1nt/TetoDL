"""
CoverStep — fetch, process, and embed cover art into audio files.
"""

import os
from typing import Optional

from ...core.image_cache import fetch_image
from ...core.models import CoverResult, LyricsMetadata, MediaInfo, PipelineContext
from ...core.step import PipelineStep
from ...core.tagger import embed_metadata
from ...utils.i18n_keys import Keys
from ...utils.console import console
from tetodl.utils.tracer import trace, traced
from ...core.metadata_fetcher import fetcher
from ...utils.files import clean_temp_files
from ...utils.thumbnail import crop_thumbnail_to_square, convert_thumbnail_format


class CoverStep(PipelineStep[PipelineContext, PipelineContext]):
    """Fetch, crop, and embed cover art into a downloaded audio file.

    Reads ``ctx.media_info``, ``ctx.downloaded_file``, ``ctx.target_dir``,
    and ``ctx.config``.  Writes ``ctx.cover_result``.

    Supports two strategies in order:
    1. **Smart cover** — query iTunes / Genius for high-quality artwork.
    2. **YouTube fallback** — download the best available thumbnail from
       the video metadata (``thumbnail`` or ``thumbnails`` list).

    The step is skipped entirely for video media types, when
    ``no_cover_mode`` is enabled, or for Opus-encoded audio.

    See Also
    --------
    :class:`LyricsStep` : Next step in the pipeline after cover.
    :meth:`_smart_download` : iTunes / Genius artwork lookup.
    :meth:`_youtube_fallback` : Thumbnail-based fallback.
    :func:`embed_metadata` : Tagging of cover art into the audio file.

    Example
    -------
    >>> step = CoverStep()
    >>> ctx = PipelineContext(media_info=some_info, downloaded_file=some_file)
    >>> result = step(ctx)
    >>> result.cover_result is not None or ctx.error is not None
    True
    """

    @trace
    def __call__(self, ctx: PipelineContext) -> PipelineContext:
        """Process and embed cover art for the downloaded audio file.

        Skips processing when any of the following conditions hold:
        - ``media_info`` or ``downloaded_file`` is ``None``
        - ``no_cover_mode`` is enabled
        - media type is ``"video"``
        - audio quality is ``"opus"``
        - neither ``is_youtube_music`` nor ``smart_cover_mode`` is set

        Otherwise tries smart download (iTunes / Genius) first, then
        falls back to YouTube thumbnails.  On success, the cover image
        is cropped (for art tracks) and embedded via
        :func:`embed_metadata`.

        Parameters
        ----------
        ctx : PipelineContext
            Context with ``media_info``, ``downloaded_file``, and
            ``target_dir`` populated.

        Returns
        -------
        PipelineContext
            Context with ``cover_result`` set, or unchanged if cover
            processing is skipped.

        Raises
        ------
        None
            All errors are captured in ``ctx.cover_result`` or logged;
            no exceptions are propagated.

        See Also
        --------
        :meth:`_smart_download` : High-quality artwork from iTunes/Genius.
        :meth:`_youtube_fallback` : Thumbnail-based fallback strategy.
        :func:`embed_metadata` : Embedding cover art into the audio file.
        :func:`crop_thumbnail_to_square` : Square cropping for art tracks.

        Example
        -------
        >>> step = CoverStep()
        >>> ctx = PipelineContext(
        ...     media_info=MediaInfo(title="Song"),
        ...     downloaded_file=DownloadedFile(path="/tmp/song.mp3"),
        ...     target_dir="/tmp",
        ... )
        >>> result = step(ctx)
        """
        if ctx.media_info is None or ctx.downloaded_file is None:
            return ctx

        if ctx.config.no_cover_mode or ctx.media_type != "audio":
            return ctx

        if ctx.config.audio_quality == "opus":
            console.warn(Keys.download.youtube.skip_cover_opus)
            return ctx

        if not (ctx.is_youtube_music or ctx.config.smart_cover_mode):
            console.warn(Keys.download.youtube.skip_cover)
            return ctx

        if not ctx.config.quiet:
            console.proc(Keys.download.youtube.processing_cover)

        info = ctx.media_info
        target_dir = ctx.target_dir
        is_art = self._is_art_track(info)
        path = None
        fetched = None
        spotify_cover = False

        if ctx.cover_url:
            with traced('trying Spotify cover art'):
                path = self._download_url(ctx.cover_url, target_dir, info.id)
            if path is None:
                with traced('Spotify cover failed, falling back to smart download'):
                    path, fetched = self._smart_download(info, target_dir, ctx)
            else:
                spotify_cover = True
        elif ctx.config.smart_cover_mode:
            with traced('trying smart download (iTunes/Genius)'):
                path, fetched = self._smart_download(info, target_dir, ctx)

        if path is None and not ctx.cover_url:
            with traced('falling back to YouTube thumbnail'):
                path = self._youtube_fallback(info, target_dir, is_art, ctx.config.force_crop, ctx.config.smart_cover_mode)

        if path is None or not os.path.exists(path):
            with traced('no cover art obtained'):
                console.err(Keys.download.youtube.cover_process_failed)
                return ctx

        if ctx.config.smart_cover_mode and not fetched and spotify_cover:
            with traced('fetching metadata from iTunes/Genius'):
                fetched = self._fetch_metadata_only(info, ctx)

        if not ctx.config.quiet:
            console.proc(Keys.download.youtube.embedding_cover)
        meta = self._build_metadata(info, fetched, is_art)

        if embed_metadata(ctx.downloaded_file.path, path, ctx.config.audio_quality, meta):
            if not ctx.config.quiet:
                console.ok(Keys.download.youtube.cover_success)
        else:
            console.err(Keys.download.youtube.cover_failed)

        clean_temp_files(target_dir, info.id)
        cropped = is_art or ctx.config.force_crop
        source = "spotify" if spotify_cover else ("smart" if fetched else "youtube")
        ctx.cover_result = CoverResult(
            thumbnail_path=path,
            metadata=self._to_lyrics_metadata(fetched),
            source=source,
            cropped=cropped,
        )
        return ctx

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _download_url(url: str, target_dir: str, file_id: str) -> Optional[str]:
        path = os.path.join(target_dir, f"{file_id}.jpg")
        data = fetch_image(url)
        if data is None:
            return None
        with open(path, "wb") as f:
            f.write(data)
        return path

    @staticmethod
    def _fetch_metadata_only(
        info: MediaInfo,
        ctx: PipelineContext | None = None,
    ) -> Optional[dict]:
        if ctx and ctx.spotify_title:
            artist = ctx.spotify_artist or ""
            title = ctx.spotify_title
        else:
            artist = info.artist or info.uploader.replace(" - Topic", "")
            title = info.track or info.title
        try:
            return fetcher.fetch_metadata(artist, title)
        except Exception:
            return None

    @staticmethod
    def _is_art_track(info: MediaInfo) -> bool:
        """Determine if the media is an art-track (auto-generated by YouTube)."""
        desc = (info.description or "").lower()
        is_topic = info.uploader.endswith(" - Topic")
        is_auto = "auto-generated by youtube" in desc or "provided to youtube by" in desc
        return info.track is not None or is_topic or is_auto

    @staticmethod
    def _smart_download(
        info: MediaInfo,
        target_dir: str,
        ctx: PipelineContext | None = None,
    ) -> tuple[Optional[str], Optional[dict]]:
        """Query iTunes / Genius for high-quality cover artwork.

        Parameters
        ----------
        info : MediaInfo
            Media metadata for artist and title resolution.
        target_dir : str
            Directory to save the downloaded thumbnail.
        ctx : PipelineContext or None
            Pipeline context; ``spotify_title`` / ``spotify_artist``
            override YouTube metadata when set.

        Returns
        -------
        tuple[Optional[str], Optional[dict]]
            ``(file_path, metadata_dict)`` on success, ``(None, None)``
            on failure.
        """
        if ctx and ctx.spotify_title:
            artist = ctx.spotify_artist or ""
            title = ctx.spotify_title
        else:
            artist = info.artist or info.uploader.replace(" - Topic", "")
            title = info.track or info.title

        try:
            data = fetcher.fetch_metadata(artist, title)
        except Exception:
            return None, None

        if not data or not data.get("url"):
            return None, None

        image_url: str = data["url"]
        img_data = fetch_image(image_url)
        if img_data is None:
            return None, None

        thumb_path = os.path.join(target_dir, f"{info.id}.jpg")
        with open(thumb_path, "wb") as f:
            f.write(img_data)

        source_name = data.get("source", "iTunes")
        console.ok(Keys.download.youtube.fetch_success)
        console.ok(Keys.media.cover_art_found_via(source=source_name))
        return thumb_path, data

    @staticmethod
    def _youtube_fallback(
        info: MediaInfo,
        target_dir: str,
        is_art: bool,
        force_crop: bool = False,
        smart_mode: bool = False,
    ) -> Optional[str]:
        """Download the best available YouTube thumbnail as cover art.

        Iterates through ``info.thumbnail`` and ``info.thumbnails``
        (largest first), downloads the first reachable image, and
        optionally crops it to a square.

        Parameters
        ----------
        info : MediaInfo
            Media metadata with thumbnail URLs.
        target_dir : str
            Directory to save the downloaded thumbnail.
        is_art : bool
            Whether this is an art-track (forces square crop).
        force_crop : bool
            Always crop to square when ``True``.

        Returns
        -------
        Optional[str]
            Path to the downloaded and processed thumbnail, or ``None``.
        """
        candidates: list[str] = []
        if info.thumbnail:
            candidates.append(info.thumbnail)
        for t in reversed(info.thumbnails):
            url = t.get("url")
            if url and url not in candidates:
                candidates.append(url)

        thumb_path = os.path.join(target_dir, f"{info.id}.jpg")
        downloaded = False

        for url in candidates:
            data = fetch_image(url)
            if data is not None:
                with open(thumb_path, "wb") as f:
                    f.write(data)
                downloaded = True
                break

        if not downloaded:
            return None

        perform_crop = is_art or force_crop or smart_mode
        if perform_crop:
            crop_thumbnail_to_square(thumb_path)
        else:
            converted = convert_thumbnail_format(thumb_path, "jpg")
            if converted:
                thumb_path = converted

        return thumb_path

    @staticmethod
    def _build_metadata(
        info: MediaInfo,
        fetched: Optional[dict],
        is_art_track: bool,
    ) -> dict:
        """Build a metadata dict for embedding, preferring smart-fetch data.

        Parameters
        ----------
        info : MediaInfo
            Media metadata as fallback.
        fetched : Optional[dict]
            Data from smart cover fetch (iTunes/Genius).
        is_art_track : bool
            Whether the track is an auto-generated art track.

        Returns
        -------
        dict
            Metadata with ``artist``, ``album``, ``title`` keys.
        """
        if fetched:
            return fetched
        if is_art_track or info.artist:
            return {
                "artist": info.artist or info.uploader.replace(" - Topic", ""),
                "album": info.album or info.title,
                "title": info.track or info.title,
            }
        return {}

    @staticmethod
    def _to_lyrics_metadata(fetched: Optional[dict]) -> Optional[LyricsMetadata]:
        """Convert a smart-fetch metadata dict to a :class:`LyricsMetadata`.

        Parameters
        ----------
        fetched : Optional[dict]
            Raw metadata from smart cover fetch.

        Returns
        -------
        Optional[LyricsMetadata]
            Structured :class:`LyricsMetadata` or ``None``.
        """
        if not fetched:
            return None
        year_raw: str | int | None = fetched.get("year") or fetched.get("date")
        if isinstance(year_raw, str):
            try:
                year_raw = int(year_raw[:4])
            except (ValueError, IndexError):
                year_raw = None
        return LyricsMetadata(
            artist=fetched.get("artist", ""),
            title=fetched.get("title", ""),
            album=fetched.get("album"),
            album_artist=fetched.get("album_artist"),
            genre=fetched.get("genre"),
            year=year_raw,
            composer=fetched.get("composer"),
            track_number=fetched.get("track_number"),
            disc_number=fetched.get("disc_number"),
            cover_url=fetched.get("url"),
        )


