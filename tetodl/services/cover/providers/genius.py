from __future__ import annotations

from tetodl.lyrics.matcher import is_valid_match
from tetodl.lyrics.providers.genius import (
    _GENIUS_HEADERS,
    _clean_title as _genius_clean_title,
)
from tetodl.services.cover.models import CoverData, CoverQuery
from tetodl.services.cover.providers.base import CoverProvider
from tetodl.utils.network import get_session


def _get_search_queries(artist: str, title: str) -> list[str]:
    import re

    queries: list[str] = []
    clean_artist = artist.replace(" - Topic", "").strip()
    clean_title = _genius_clean_title(title, artist=clean_artist)
    queries.append(f"{clean_artist} {clean_title}")

    separators = r"\s*(?:/|-|\||\u00d7)\s*"
    parts = re.split(separators, title)
    if len(parts) > 1:
        candidate = _genius_clean_title(parts[0], clean_artist)
        if len(candidate) > 1:
            queries.append(f"{clean_artist} {candidate}")
            queries.append(candidate)

    queries.append(clean_title)

    seen: set[str] = set()
    unique: list[str] = []
    for q in queries:
        key = q.lower().strip()
        if key and key not in seen:
            seen.add(key)
            unique.append(q)
    return unique


class GeniusCoverProvider(CoverProvider):
    def search(self, query: CoverQuery) -> CoverData | None:
        if not query.artist and not query.title:
            return None

        artist = query.artist.strip()
        title = query.title.strip()

        for search_query in _get_search_queries(artist, title):
            result = self._search_genius_cover(search_query, artist, title)
            if result:
                return result

        return None

    def _search_genius_cover(
        self, search_query: str, orig_artist: str, orig_title: str,
    ) -> CoverData | None:
        try:
            resp = get_session().get(
                "https://genius.com/api/search/multi",
                params={"per_page": "5", "q": search_query},
                headers=_GENIUS_HEADERS,
                timeout=10,
            )
            data = resp.json()
        except Exception:
            return None

        hits = self._extract_song_hits(data)
        if not hits:
            return None

        for h in hits:
            result = h.get("result", {})
            hit_title = result.get("title", "")
            hit_artist = ""
            py_artist = result.get("primary_artist") or {}
            if isinstance(py_artist, dict):
                hit_artist = py_artist.get("name", "")

            if not is_valid_match(orig_title, hit_title, search_artist=orig_artist, result_artist=hit_artist):
                continue

            cover_url = result.get("song_art_image_url") or result.get("og_image")
            if not cover_url:
                continue

            clean_artist = hit_artist
            if orig_artist and orig_artist.lower() in hit_artist.lower():
                clean_artist = orig_artist

            return CoverData(
                url=cover_url,
                source="Genius",
                artist=clean_artist,
                title=hit_title,
                album=str(result.get("album", {}).get("name", "") if isinstance(result.get("album"), dict) else ""),
            )

        return None

    @staticmethod
    def _extract_song_hits(data: dict) -> list[dict]:
        sections = data.get("response", {}).get("sections") or []
        for section in sections:
            if section.get("type") == "song":
                return section.get("hits") or []
        return []
