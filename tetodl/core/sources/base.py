"""
Source handler protocol — each source (YouTube, Spotify, etc.) implements
:class:`SourceHandler` to declare which URLs it handles and how to extract
track metadata from them.

Usage::

    from tetodl.core.sources.base import SourceHandler, VideoInfo
"""

from dataclasses import dataclass
from typing import Protocol


@dataclass
class VideoInfo:
    url: str
    title: str
    artist: str | None = None
    album: str | None = None
    cover_url: str | None = None
    source: str = ""
    raw_title: str | None = None


class SourceHandler(Protocol):
    """Handle one type of input URL -> list of VideoInfo."""

    def handles(self, url: str) -> bool:
        """Return True if this handler can process the given URL."""
        ...

    def extract(self, url: str) -> list[VideoInfo]:
        """Extract track metadata from the URL.

        Returns a list of VideoInfo (one per track, even for playlists).
        """
        ...
