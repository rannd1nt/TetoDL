"""
Provider abstractions (Protocol) for pluggable external services.

Every external data source (iTunes, Genius, etc.) implements one of these
protocols so the pipeline steps can remain agnostic of the actual provider.
"""

from typing import Protocol, runtime_checkable

from .models import LyricsMetadata


@runtime_checkable
class MetadataProvider(Protocol):
    """
    Contract for external metadata providers (iTunes, Genius, …).

    A provider searches by artist + title and returns structured metadata
    if a match is found, or ``None`` otherwise.
    """

    def search(self, artist: str, title: str) -> LyricsMetadata | None:
        """
        Search for track metadata.

        Parameters
        ----------
        artist : str
            Artist name to search for.
        title : str
            Track title to search for.

        Returns
        -------
        LyricsMetadata | None
            Structured metadata if found, None otherwise.
        """
        ...


@runtime_checkable
class LyricsProvider(Protocol):
    """
    Contract for providers that return lyrics text (Genius, …).
    """

    def fetch_lyrics(self, artist: str, title: str, romaji: bool = False) -> str | None:
        """
        Fetch lyrics text for a track.

        Parameters
        ----------
        artist : str
            Artist name.
        title : str
            Track title.
        romaji : bool
            Request romaji transliteration if available.

        Returns
        -------
        str | None
            Lyrics text if found, None otherwise.
        """
        ...
