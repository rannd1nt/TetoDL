from __future__ import annotations

import re
from typing import Any

from .auth import SpotifyAuth
from .client import SpotifyClient
from .errors import SpotifyParseError
from .models import SpotifyTrack

_URL_PATTERN = re.compile(r"spotify\.com/(track|album|playlist)/([a-zA-Z0-9]+)")


class SpotifyResolver:
    def __init__(self) -> None:
        self._auth = SpotifyAuth()
        self._client = SpotifyClient(self._auth)

    def resolve(self, url: str) -> list[SpotifyTrack]:
        _, tracks = self.resolve_meta(url)
        return tracks

    def resolve_meta(self, url: str) -> tuple[str | None, list[SpotifyTrack]]:
        m = _URL_PATTERN.search(url)
        if not m:
            raise SpotifyParseError(f"Not a valid Spotify URL: {url}")

        item_type, item_id = m.group(1), m.group(2)

        if item_type == "track":
            entity = self._client.get_track(item_id)
            name, tracks = None, [self._entity_to_track(entity)]
        elif item_type == "playlist":
            entity = self._client.get_playlist(item_id)
            name = entity.get("title") or entity.get("name") or "Playlist"
            tracks = [
                self._entry_to_track(e) for e in entity.get("trackList", []) if e.get("uri")
            ]
        elif item_type == "album":
            entity = self._client.get_album(item_id)
            name = entity.get("title") or entity.get("name") or "Album"
            cover_url = self._extract_best_cover(entity)
            tracks = [
                self._entry_to_track(e, cover_url)
                for e in entity.get("trackList", []) if e.get("uri")
            ]
        else:
            return None, []

        return name, tracks

    def fetch_track_cover(self, track_id: str) -> str:
        try:
            entity = self._client.get_track(track_id)
            return self._extract_best_cover(entity)
        except Exception:
            return ""

    @staticmethod
    def _extract_best_cover(entity: dict[str, Any]) -> str:
        images = (entity.get("visualIdentity") or {}).get("image") or []
        if not images:
            return ""
        best = max(
            images,
            key=lambda i: (i.get("maxWidth", 0) or 0) * (i.get("maxHeight", 0) or 0),
        )
        return best.get("url", "")

    @staticmethod
    def _entity_to_track(entity: dict[str, Any]) -> SpotifyTrack:
        artists = [a["name"] for a in (entity.get("artists") or [])]
        cover_url = SpotifyResolver._extract_best_cover(entity)
        return SpotifyTrack(
            title=entity.get("name") or entity.get("title") or "",
            artist=artists[0] if artists else "",
            artists=artists,
            album="",
            duration_ms=entity.get("duration") or 0,
            spotify_id=entity.get("id") or "",
            cover_url=cover_url,
        )

    @staticmethod
    def _entry_to_track(
        entry: dict[str, Any], cover_url: str = "",
    ) -> SpotifyTrack:
        subtitle = entry.get("subtitle") or ""
        artists = [a.strip() for a in subtitle.split(",")] if subtitle else []
        track_id = ""
        if entry.get("uri"):
            track_id = entry["uri"].split(":")[-1]
        return SpotifyTrack(
            title=entry.get("title") or "",
            artist=artists[0] if artists else "",
            artists=artists,
            album="",
            duration_ms=entry.get("duration") or 0,
            spotify_id=track_id,
            cover_url=cover_url,
        )
