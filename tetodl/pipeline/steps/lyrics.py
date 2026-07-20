"""
LyricsStep — fetch and embed lyrics into an audio file via Genius.
"""

import os
import re
from typing import Optional

from ...core.models import CoverResult, MediaInfo, PipelineContext
from ...core.step import PipelineStep
from ...core.tagger import embed_lyrics
from ...utils.i18n_keys import Keys
from ...utils.console import console
from tetodl.utils.tracer import trace, traced
from ...core.metadata_fetcher import fetcher


class LyricsStep(PipelineStep[PipelineContext, PipelineContext]):
    """Fetch lyrics from Genius and embed them into a downloaded audio file.

    Reads ``ctx.media_info``, ``ctx.downloaded_file``, ``ctx.cover_result``,
    and ``ctx.config``.  Writes ``ctx.lyrics_embedded``.

    The step is skipped entirely for video media types or when
    ``lyrics_mode`` is disabled in the configuration.

    See Also
    --------
    :class:`CoverResult` : Provides alternative artist/title for search.
    :func:`embed_lyrics` : Lyrics embedding into the audio file.
    :func:`fetcher.fetch_lyrics_genius` : Genius API lyrics fetch.

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
        """Fetch and embed lyrics via the Genius API.

        Skips if ``lyrics_mode`` is disabled or the media type is not
        audio.  Uses :meth:`_resolve_search_terms` to determine the
        artist and title (preferring smart-cover metadata when
        available), then fetches lyrics via
        :func:`fetcher.fetch_lyrics_genius`.  On success embeds the
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
        :func:`fetcher.fetch_lyrics_genius` : Genius API lookup.

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

        artist, title = self._resolve_search_terms(info, ctx.cover_result)

        console.proc(Keys.media.searching_lyrics_for(artist=artist, title=title))
        with traced(f'fetching from Genius (romaji={ctx.config.romaji_mode})'):
            lyrics = fetcher.fetch_lyrics_genius(
                artist,
                title,
                romaji=ctx.config.romaji_mode,
            )

        if not lyrics:
            with traced('no lyrics returned from Genius'):
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
        cover_result: Optional[CoverResult],
    ) -> tuple[str, str]:
        """Extract artist and title for the Genius lyrics search.

        Prefers :class:`LyricsMetadata` from the cover step, falls
        back to parsing the title for a ``"Artist - Title"`` pattern,
        and finally uses ``info.artist`` / ``info.track``.

        Parameters
        ----------
        info : MediaInfo
            Media metadata with artist, track, uploader fields.
        cover_result : Optional[CoverResult]
            Result from the cover step with optional metadata.

        Returns
        -------
        tuple[str, str]
            ``(artist, title)`` for the lyrics API lookup.
        """
        if cover_result and cover_result.metadata:
            return cover_result.metadata.artist, cover_result.metadata.title

        raw = info.title or ""
        match = re.match(r"^(.*?)\s+-\s+(.*)$", raw)
        if match:
            artist = match.group(1).strip()
            raw_title = match.group(2).strip()
            title = re.sub(r"\s*[\(\[].*?[\)\]]", "", raw_title).strip()
            return artist, title

        artist = info.artist or info.uploader.replace(" - Topic", "")
        title = info.track or info.title
        return artist or "", title or ""
