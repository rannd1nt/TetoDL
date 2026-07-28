from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LyricsQuery:
    artist: str = ""
    title: str = ""
    duration: float = 0.0
    album: str = ""


@dataclass
class LyricsData:
    plain_lyrics: str
    source: str
    score: float = 0.0
    artist: str = ""
    title: str = ""
    album: str = ""
    duration: float = 0.0
