from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SpotifyTrack:
    title: str
    artist: str
    artists: list[str] = field(default_factory=list)
    album: str = ""
    duration_ms: int = 0
    spotify_id: str = ""
    cover_url: str = ""


@dataclass
class SpotifyPlaylist:
    name: str
    owner: str = ""
    tracks: list[SpotifyTrack] = field(default_factory=list)
    total: int = 0
