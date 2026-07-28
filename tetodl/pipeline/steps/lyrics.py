"""
LyricsStep — fetch and embed lyrics into an audio file.
"""

import os

from tetodl.lyrics.cleaner import clean_youtube_title
from tetodl.lyrics.engine import search_lyrics
from tetodl.utils.tracer import trace, traced

from ...core.models import CoverResult, MediaInfo, PipelineContext
from ...core.step import PipelineStep
from ...core.tagger import embed_lyrics
from ...utils.console import console
from ...utils.i18n_keys import Keys


class LyricsStep(PipelineStep[PipelineContext, PipelineContext]):
    """Fetch lyrics and embed them into a downloaded audio file.

    Reads ``ctx.media_info``, ``ctx.downloaded_file``, ``ctx.cover_result``,
    and ``ctx.config``.  Writes ``ctx.lyrics_embedded``.

    The step is skipped entirely for video media types or when
    ``lyrics_mode`` is disabled in the configuration.

    See Also
    --------
    :class:`CoverResult` : Provides alternative artist/title for search.
    :func:`embed_lyrics` : Lyrics embedding into the audio file.
    :func:`search_lyrics` : Lyrics engine (LRCLIB + Genius fallback).

    Example
    -------
    >>> step = LyricsStep()
    >>> ctx = PipelineContext(
    ...     downloaded_file=DownloadedFile(path="/tmp/song.mp3"),
    ...     config=AppConfig(lyrics_mode=True),
    ... )
    >>> result = step(ctx)
    """

    @trace
    def __call__(self, ctx: PipelineContext) -> PipelineContext:
        """Fetch and embed lyrics.

        Skips if ``lyrics_mode`` is disabled or the media type is not
        audio.  Uses :meth:`_resolve_search_terms` to determine the
        artist and title (preferring smart-cover metadata when
        available), then fetches lyrics via
        :func:`search_lyrics`.  On success embeds the
        lyrics into the audio file via :func:`embed_lyrics`.

        Parameters
        ----------
        ctx : PipelineContext
            Context with ``media_info``, ``downloaded_file``, and
            ``cover_result`` populated.

        Returns
        -------
        PipelineContext
            Context with ``lyrics_embedded`` set to ``True`` on success,
            or unchanged on failure / skip.

        Raises
        ------
        None
            All outcomes are communicated through the context or logged.

        See Also
        --------
        :meth:`_resolve_search_terms` : Artist/title resolution.
        :func:`embed_lyrics` : Embedding lyrics into the file.
        :func:`search_lyrics` : Lyrics engine lookup.

        Example
        -------
        >>> step = LyricsStep()
        >>> ctx = PipelineContext(
        ...     media_info=MediaInfo(title="Artist - Song"),
        ...     downloaded_file=DownloadedFile(path="/tmp/song.mp3"),
        ...     config=AppConfig(lyrics_mode=True),
        ... )
        >>> result = step(ctx)
        """
        if not ctx.config.lyrics_mode or ctx.media_type != "audio":
            return ctx

        if ctx.downloaded_file is None:
            return ctx

        audio_path = ctx.downloaded_file.path
        if not audio_path or not os.path.exists(audio_path):
            return ctx

        info = ctx.media_info
        if info is None:
            return ctx

        artist, title = self._resolve_search_terms(info, ctx.cover_result, ctx)

        console.proc(Keys.media.searching_lyrics_for(artist=artist, title=title))
        duration = info.duration if info.duration else 0.0
        with traced('fetching lyrics via engine'):
            lyrics = search_lyrics(artist, title, duration=duration)

        if not lyrics:
            with traced('no lyrics returned'):
                console.warn(Keys.media.lyrics_not_found_genius)
                return ctx

        if embed_lyrics(audio_path, lyrics):
            with traced('embed successful'):
                console.ok(Keys.media.lyrics_embedded_success)
                ctx.lyrics_embedded = True
                return ctx

        with traced('embed failed'):
            console.err(Keys.media.failed_to_embed_lyrics)
            return ctx

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_search_terms(
        info: MediaInfo,
        cover_result: CoverResult | None,
        ctx: PipelineContext | None = None,
    ) -> tuple[str, str]:
        """Extract artist and title for the lyrics search.

        Priority:
        1. :class:`LyricsMetadata` from the cover step (iTunes/Genius).
        2. ``ctx.spotify_title`` / ``ctx.spotify_artist`` (Spotify origin).
        3. ``info.artist`` / ``info.track`` (structured metadata from yt-dlp).
        4. :func:`clean_youtube_title` — iTunes API lookup, then regex fallback.
        5. ``info.uploader`` / ``info.title`` (last resort).

        Parameters
        ----------
        info : MediaInfo
            Media metadata with artist, track, uploader fields.
        cover_result : Optional[CoverResult]
            Result from the cover step with optional metadata.
        ctx : Optional[PipelineContext]
            Pipeline context with Spotify overrides.

        Returns
        -------
        tuple[str, str]
            ``(artist, title)`` for the lyrics API lookup.
        """
        if cover_result and cover_result.metadata:
            return cover_result.metadata.artist, cover_result.metadata.title

        if ctx and ctx.spotify_title:
            return (ctx.spotify_artist or ""), ctx.spotify_title

        if info.artist and info.track:
            return info.artist, info.track

        raw = info.title or ""
        artist, title = clean_youtube_title(raw)
        if artist and title:
            # YouTube titles often use "Title - Artist" (common for JP videos)
            # rather than "Artist - Title".  Detect via uploader match.
            if info.uploader:
                uploader_clean = info.uploader.replace(" - Topic", "").strip().lower()
                if title.lower() == uploader_clean and artist.lower() != uploader_clean:
                    artist, title = title, artist
            return artist, title

        artist = info.artist or info.uploader.replace(" - Topic", "")
        title = info.track or info.title
        return artist or "", title or ""
