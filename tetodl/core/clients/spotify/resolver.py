# Copyright 2026 rannd1nt
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import re
from typing import Any

from .auth import SpotifyAuth
from .client import SpotifyClient
from .errors import SpotifyParseError
from .models import SpotifyTrack

_URL_PATTERN = re.compile(
    r"(?:spotify\.com|spotify\.link)"
    r"(?:/[^/?#]+)*"
    r"/(track|album|playlist)/([a-zA-Z0-9]+)",
    re.IGNORECASE,
)


class SpotifyResolver:
    def __init__(self) -> None:
        self._auth = SpotifyAuth()
        self._client = SpotifyClient(self._auth)

    def expand_url(self, url: str) -> str:
        """Expand short URLs (e.g. open.spotify.com/s/..., spotify.link/...) or Spotify URIs."""
        if not url:
            return url
        url = url.strip()

        # Handle Spotify URIs: spotify:track:id or spotify://track/id
        m_uri = re.match(r"spotify:(?://)?(track|album|playlist)[:/]([a-zA-Z0-9]+)", url, re.IGNORECASE)
        if m_uri:
            return f"https://open.spotify.com/{m_uri.group(1).lower()}/{m_uri.group(2)}"

        if _URL_PATTERN.search(url):
            return url

        # Handle shortened or dynamic links (/s/..., spotify.link/..., link.tospotify.com/...)
        if "/s/" in url or "spotify.link" in url or "link.tospotify.com" in url:
            import base64
            import json
            import urllib.parse
            import requests

            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            }
            try:
                resp = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
                if _URL_PATTERN.search(resp.url):
                    return resp.url

                # Check urlSchemeConfig base64 in HTML
                m_cfg = re.search(
                    r'<script[^>]*id=["\']urlSchemeConfig["\'][^>]*>(.*?)</script>',
                    resp.text,
                    re.DOTALL,
                )
                if m_cfg:
                    raw_b64 = m_cfg.group(1).strip()
                    payload = json.loads(base64.b64decode(raw_b64).decode("utf-8"))
                    redirect_url = payload.get("redirectUrl")
                    if redirect_url and _URL_PATTERN.search(redirect_url):
                        return redirect_url
                    url_scheme = payload.get("urlScheme")
                    if url_scheme:
                        m_scheme = re.match(
                            r"spotify:(?://)?(track|album|playlist)[:/]([a-zA-Z0-9]+)",
                            url_scheme,
                            re.IGNORECASE,
                        )
                        if m_scheme:
                            return f"https://open.spotify.com/{m_scheme.group(1).lower()}/{m_scheme.group(2)}"

                # Check for browser_fallback_url in HTML or intent
                m_fallback = re.search(r"browser_fallback_url=([^&;\"\'\s]+)", resp.text)
                if m_fallback:
                    decoded = urllib.parse.unquote(m_fallback.group(1))
                    if _URL_PATTERN.search(decoded):
                        return decoded
            except Exception:
                pass

        return url

    def resolve(self, url: str) -> list[SpotifyTrack]:
        _, tracks = self.resolve_meta(url)
        return tracks

    def resolve_meta(self, url: str) -> tuple[str | None, list[SpotifyTrack]]:
        url = self.expand_url(url)
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
