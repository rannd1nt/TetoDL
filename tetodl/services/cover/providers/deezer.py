from __future__ import annotations

from difflib import SequenceMatcher

from tetodl.lyrics.matcher import is_valid_match
from tetodl.services.cover.models import CoverData, CoverQuery
from tetodl.services.cover.providers.base import CoverProvider
from tetodl.utils.network import get_session


def _clean_title(title: str, artist: str = "") -> str:
    import re

    if not title:
        return ""

    title = re.sub(r"【.*?】", "", title)
    title = re.sub(r"\[.*?\]", "", title)
    title = re.sub(r"\(.*?\)", "", title)
    title = re.sub(r"「.*?」", "", title)
    title = re.sub(r"『.*?』", "", title)

    remove_words = [
        "official video", "official audio", "lyrics", "lyric video",
        "music video", "mv", "full audio", "official music video",
        "full ver", "full version", "hq", "hd", "4k", "remastered",
        "sub thai", "sub indo", "eng sub", "live", "video clip",
        "cover", "self cover", "synthesizer v", "vocaloid",
        "feat.", "ft.", "featuring", "album version",
    ]
    for word in remove_words:
        title = re.sub(f"(?i){re.escape(word)}", "", title)

    clean_base = title.replace("-", " ").replace("/", " ").replace("|", " ").replace("_", " ").replace("\u00d7", " ")

    if artist and len(artist) > 2:
        clean_base = re.sub(f"(?i){re.escape(artist)}", "", clean_base)

    clean_base = re.sub(r"\s+", " ", clean_base).strip()
    return clean_base


class DeezerProvider(CoverProvider):
    def search(self, query: CoverQuery) -> CoverData | None:
        if not query.artist and not query.title:
            return None

        artist = query.artist.strip()
        title = query.title.strip()

        for search_term in self._get_search_terms(artist, title):
            result = self._search_deezer(search_term, artist, title)
            if result:
                return result

        return None

    def _get_search_terms(self, artist: str, title: str) -> list[str]:
        terms: list[str] = []

        cleaned = _clean_title(title, artist)
        if cleaned and len(cleaned) > 1:
            terms.append(f"{artist} {cleaned}")

        if cleaned and cleaned != title:
            terms.append(f"{artist} {title}")

        terms.append(f"{artist} {title}")

        seen: set[str] = set()
        unique: list[str] = []
        for t in terms:
            key = t.lower().strip()
            if key not in seen:
                seen.add(key)
                unique.append(t)
        return unique

    def _search_deezer(self, search_term: str, orig_artist: str, orig_title: str) -> CoverData | None:
        try:
            resp = get_session().get(
                "https://api.deezer.com/search",
                params={"q": search_term, "limit": 10, "output": "json"},
                timeout=8,
            )
            data = resp.json()
        except Exception:
            return None

        results = data.get("data") or []
        if not results:
            return None

        for r in results:
            deezer_title = r.get("title", "")
            deezer_artist = r.get("artist", {}).get("name", "")

            if not is_valid_match(
                orig_title, deezer_title,
                search_artist=orig_artist, result_artist=deezer_artist,
            ):
                continue

            album = r.get("album", {})
            cover_url = (
                album.get("cover_xl")
                or album.get("cover_big")
                or album.get("cover_medium")
                or album.get("cover_small")
            )
            if not cover_url:
                continue

            release_date = r.get("release_date", "")
            year: int | None = None
            if release_date and len(release_date) >= 4:
                try:
                    year = int(release_date[:4])
                except ValueError:
                    pass

            return CoverData(
                url=cover_url,
                source="Deezer",
                artist=deezer_artist,
                title=deezer_title,
                album=album.get("title"),
                album_artist=album.get("artist", {}).get("name"),
                genre=str(r.get("genre_id") or ""),
                year=year,
            )

        return None
