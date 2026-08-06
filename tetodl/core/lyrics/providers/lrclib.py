from __future__ import annotations

from tetodl.core.lyrics.headers import get_headers
from tetodl.core.lyrics.models import LyricsData, LyricsQuery
from tetodl.core.lyrics.providers.base import LyricsProvider
from tetodl.utils.network import get_session


class LRCLIBProvider(LyricsProvider):
    BASE_URL = "https://lrclib.net/api"

    def search(self, query: LyricsQuery) -> list[LyricsData]:
        seen = set()
        results: list[LyricsData] = []

        strategies = [
            {"track_name": query.title, "artist_name": query.artist},
        ]
        if query.title and query.artist:
            strategies.append({"track_name": query.artist, "artist_name": query.title})
        if query.title:
            strategies.append({"track_name": query.title})
        if query.artist:
            strategies.append({"artist_name": query.artist})

        for params in strategies:
            for item in self._fetch(params):
                key = (item.get("artistName") or "", item.get("trackName") or "")
                if key in seen:
                    continue
                seen.add(key)

                plain = (item.get("plainLyrics") or "").strip()
                if not plain:
                    continue

                results.append(LyricsData(
                    plain_lyrics=plain,
                    source="lrclib",
                    artist=item.get("artistName") or "",
                    title=item.get("trackName") or "",
                    album=item.get("albumName") or "",
                    duration=float(item.get("duration") or 0),
                ))

        return results

    def _fetch(self, params: dict[str, str]) -> list[dict]:
        if not params:
            return []
        try:
            resp = get_session().get(
                f"{self.BASE_URL}/search",
                params=params,
                headers=get_headers(),
                timeout=10,
            )
            if resp.status_code != 200:
                return []
            data = resp.json()
            if isinstance(data, list):
                return data
        except Exception:
            pass
        return []
