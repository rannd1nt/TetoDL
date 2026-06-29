"""
LyricsStep — fetch and embed lyrics into an audio file via Genius.
"""

import os
import re
from typing import Optional

from ...core.models import CoverResult, LyricsConfig, MediaInfo
from ...core.step import PipelineStep
from ...core.tagger import embed_lyrics
from ...utils.i18n_keys import Keys
from ...utils.console import console
from ...core.metadata_fetcher import fetcher


class LyricsStep(PipelineStep):
    """Fetch lyrics from Genius and embed them into a downloaded audio file.

    When a preceding :class:`CoverStep` has retrieved metadata from
    iTunes / Genius (available via ``cover_result.metadata``) that data
    is used for a more accurate artist/title search.  Otherwise the
    video title is parsed with the same heuristic used in the original
    ``audio.py``::

        "Artist - Title (extra info)"  →  artist="Artist", title="Title"
    """

    def __init__(self, config: Optional[LyricsConfig] = None) -> None:
        """Configure the lyrics step.

        Parameters
        ----------
        config : LyricsConfig | None
            Lyrics options (enabled, romaji).  When ``None`` defaults
            are used (``enabled=False``, ``romaji=False``).
        """
        self._config = config or LyricsConfig()

    def __call__(
        self,
        info: MediaInfo,
        audio_path: str,
        cover_result: Optional[CoverResult] = None,
    ) -> bool:
        """Fetch and embed lyrics.

        Parameters
        ----------
        info : MediaInfo
            Extracted media metadata (used as fallback for artist/title).
        audio_path : str
            Path to the downloaded audio file.
        cover_result : CoverResult | None
            Result from a preceding ``CoverStep``.  When present and
            ``cover_result.metadata`` is set, its artist/title values
            are used for the Genius search instead of parsing the video
            title.

        Returns
        -------
        bool
            ``True`` when lyrics were successfully fetched and embedded.
        """
        if not self._config.enabled:
            return False
        if not audio_path or not os.path.exists(audio_path):
            return False

        artist, title = self._resolve_search_terms(info, cover_result)

        console.proc(Keys.media.searching_lyrics_for(artist=artist, title=title))
        lyrics = fetcher.fetch_lyrics_genius(
            artist,
            title,
            romaji=self._config.romaji,
        )

        if not lyrics:
            console.warn(Keys.media.lyrics_not_found_genius)
            return False

        if embed_lyrics(audio_path, lyrics):
            console.ok(Keys.media.lyrics_embedded_success)
            return True

        console.err(Keys.media.failed_to_embed_lyrics)
        return False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_search_terms(
        info: MediaInfo,
        cover_result: Optional[CoverResult],
    ) -> tuple[str, str]:
        """Determine the best artist/title pair for the Genius search.

        Priority:
        1. ``cover_result.metadata`` (iTunes / Genius fetched data).
        2. Parse ``title`` as ``"Artist - Title (extra)"``.
        3. Fall back to ``info.artist`` / ``info.track``.
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
