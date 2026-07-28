from __future__ import annotations

import json
import re
from typing import Any

from .auth import SpotifyAuth
from .errors import SpotifyParseError
from .ratelimit import SpotifyRateLimiter

EMBED_BASE = "https://open.spotify.com/embed"

_NEXT_DATA_RE = re.compile(
    r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>',
    re.DOTALL,
)


class SpotifyClient:
    def __init__(self, auth: SpotifyAuth) -> None:
        self._auth = auth
        self._rate_limiter = SpotifyRateLimiter()

    @property
    def _session(self):
        return self._auth.session

    def _fetch_embed(self, path: str) -> dict[str, Any]:
        self._rate_limiter.wait()
        resp = self._session.get(f"{EMBED_BASE}/{path}", timeout=15)
        if resp.status_code == 429:
            if self._rate_limiter.report_429():
                return self._fetch_embed(path)
            raise SpotifyParseError("Rate limited by Spotify")
        self._rate_limiter.report_success()
        if resp.status_code != 200:
            raise SpotifyParseError(
                f"Failed to fetch embed page: HTTP {resp.status_code}"
            )

        match = _NEXT_DATA_RE.search(resp.text)
        if not match:
            raise SpotifyParseError("No __NEXT_DATA__ found in embed page")

        try:
            data = json.loads(match.group(1))
        except json.JSONDecodeError as exc:
            raise SpotifyParseError(
                f"Invalid JSON in __NEXT_DATA__: {exc}"
            ) from exc

        status = data.get("props", {}).get("pageProps", {}).get("status")
        if status == 404:
            raise SpotifyParseError(
                "This content is private or no longer available"
            )

        entity = (
            data.get("props", {})
            .get("pageProps", {})
            .get("state", {})
            .get("data", {})
            .get("entity")
        )
        if not entity:
            raise SpotifyParseError("No entity found in embed data")

        return entity

    def get_track(self, track_id: str) -> dict[str, Any]:
        return self._fetch_embed(f"track/{track_id}")

    def get_playlist(self, playlist_id: str) -> dict[str, Any]:
        return self._fetch_embed(f"playlist/{playlist_id}")

    def get_album(self, album_id: str) -> dict[str, Any]:
        return self._fetch_embed(f"album/{album_id}")
