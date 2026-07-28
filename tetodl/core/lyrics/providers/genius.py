from __future__ import annotations

import re

from bs4 import BeautifulSoup

from tetodl.core.lyrics.matcher import anchor_matches as _anchor_matches
from tetodl.core.lyrics.matcher import is_valid_match as _is_valid_match
from tetodl.core.lyrics.models import LyricsData, LyricsQuery
from tetodl.core.lyrics.providers.base import LyricsProvider
from tetodl.utils.network import get_session
from tetodl.utils.text_cleaner import clean_title, get_search_queries

_GENIUS_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def _clean_genius_lyrics(lyrics_text: str) -> str:
    if not lyrics_text:
        return ""

    match = re.search(r"\[", lyrics_text)
    if match:
        lyrics_text = lyrics_text[match.start():]
    else:
        lyrics_text = re.sub(r"^\d+\s*Contributors.*?Lyrics\s*", "", lyrics_text, flags=re.DOTALL | re.IGNORECASE)

    lyrics_text = re.sub(r"^Translations.*?Lyrics\s*", "", lyrics_text, flags=re.DOTALL | re.IGNORECASE)
    lyrics_text = re.sub(r"\d*Embed$", "", lyrics_text)
    lyrics_text = re.sub(r"You might also like.*", "", lyrics_text, flags=re.DOTALL | re.IGNORECASE)
    lyrics_text = re.sub(r"Get tickets as low as.*", "", lyrics_text, flags=re.DOTALL | re.IGNORECASE)
    lyrics_text = re.sub(r"\n{3,}", "\n\n", lyrics_text).strip()
    return lyrics_text


def _search_genius(artist: str, title: str) -> tuple[str | None, str | None, str | None]:
    target_title = clean_title(title, artist)
    clean_artist = artist.replace(" - Topic", "").strip()

    for search_query in get_search_queries(artist, title):
        try:
            resp = get_session().get(
                "https://genius.com/api/search/multi",
                params={"per_page": "5", "q": search_query},
                headers=_GENIUS_HEADERS,
                timeout=10,
            )
            data = resp.json()

            hits = []
            if "response" in data and "sections" in data["response"]:
                for section in data["response"]["sections"]:
                    if section["type"] == "song":
                        hits = section["hits"]
                        break

            if not hits:
                continue

            for h in hits:
                result = h["result"]
                hit_title = result["title"]
                hit_artist = "Unknown"
                if "primary_artist" in result and "name" in result["primary_artist"]:
                    hit_artist = result["primary_artist"]["name"]

                if _is_valid_match(target_title, hit_title, search_artist=clean_artist, result_artist=hit_artist):
                    return result["url"], hit_artist, hit_title

        except Exception:
            continue

    return None, None, None


def _scrape_lyrics(page_url: str) -> str | None:
    try:
        resp = get_session().get(page_url, headers=_GENIUS_HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        lyrics_divs = soup.find_all("div", attrs={"data-lyrics-container": "true"})
        if not lyrics_divs:
            return None

        lyrics_text = ""
        for div in lyrics_divs:
            for br in div.find_all("br"):
                br.replace_with("\n")
            lyrics_text += div.get_text() + "\n\n"
        return lyrics_text.strip()
    except Exception:
        return None


def _align_with_anchor(raw_lyrics: str, anchor: str) -> str:
    if not raw_lyrics or not anchor:
        return raw_lyrics or ""

    anchor_lines = [line.strip() for line in anchor.strip().split("\n") if line.strip()]
    if not anchor_lines:
        return raw_lyrics

    first_anchor_line = anchor_lines[0]
    genius_lines = raw_lyrics.split("\n")

    match_idx = -1
    for i, line in enumerate(genius_lines):
        if _anchor_matches(first_anchor_line, line):
            match_idx = i
            break

    if match_idx < 0:
        return raw_lyrics

    cut_idx = match_idx
    for i in range(match_idx - 1, -1, -1):
        if re.match(r"^\[.*\]$", genius_lines[i].strip()):
            cut_idx = i
            break

    return "\n".join(genius_lines[cut_idx:]).strip()


def scrape_with_anchor(artist: str, title: str, anchor: str) -> str | None:
    page_url, _, _ = _search_genius(artist, title)
    if not page_url:
        return None

    raw = _scrape_lyrics(page_url)
    if not raw:
        return None

    aligned = _align_with_anchor(raw, anchor)
    cleaned = _clean_genius_lyrics(aligned)
    return cleaned if cleaned else None


class GeniusProvider(LyricsProvider):
    def search(self, query: LyricsQuery) -> list[LyricsData]:
        if not query.artist and not query.title:
            return []

        page_url, hit_artist, hit_title = _search_genius(query.artist, query.title)
        if not page_url:
            return []

        raw = _scrape_lyrics(page_url)
        if not raw:
            return []

        cleaned = _clean_genius_lyrics(raw)
        if not cleaned:
            return []

        return [LyricsData(
            plain_lyrics=cleaned,
            source="genius",
            artist=hit_artist or "",
            title=hit_title or "",
        )]
