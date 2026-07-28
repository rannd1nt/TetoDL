from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CoverQuery:
    artist: str = ""
    title: str = ""
    album: str = ""
    duration: float = 0.0


@dataclass
class CoverData:
    url: str
    source: str
    artist: str = ""
    title: str = ""
    album: str = ""
    album_artist: str = ""
    genre: str = ""
    year: int | None = None
    composer: str = ""
    track_number: str = ""
    disc_number: str = ""
