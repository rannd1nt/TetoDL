from __future__ import annotations

import re

from bs4 import BeautifulSoup

from tetodl.lyrics.matcher import anchor_matches as _anchor_matches
from tetodl.lyrics.matcher import is_valid_match as _is_valid_match
from tetodl.lyrics.models import LyricsData, LyricsQuery
from tetodl.lyrics.providers.base import LyricsProvider
from tetodl.utils.network import get_session

_GENIUS_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def _clean_title(title: str, artist: str = "") -> str:
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
        "feat.", "ft.", "featuring",
    ]
    for word in remove_words:
        title = re.sub(f"(?i){re.escape(word)}", "", title)

    clean_base = title.replace("-", " ").replace("/", " ").replace("|", " ").replace("_", " ").replace("×", " ")

    if artist and len(artist) > 2:
        clean_base = re.sub(f"(?i){re.escape(artist)}", "", clean_base)

    clean_base = re.sub(r"\s+", " ", clean_base).strip()
    return clean_base


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


def _get_search_queries(artist: str, title: str) -> list[str]:
    clean_artist = artist.replace(" - Topic", "").strip()
    clean_title = _clean_title(title, artist=clean_artist)
    queries: list[str] = []

    queries.append(f"{clean_artist} {clean_title}")

    separators = r"\s*(?:/|-|\||×)\s*"
    parts = re.split(separators, title)
    if len(parts) > 1:
        candidate = _clean_title(parts[0], artist)
        if len(candidate) > 1:
            queries.append(f"{clean_artist} {candidate}")
            queries.append(candidate)

    queries.append(clean_title)
    return queries


def _search_genius(artist: str, title: str) -> tuple[str | None, str | None, str | None]:
    """Search Genius API for the given artist/title.

    Returns
    -------
    tuple[str | None, str | None, str | None]
        ``(page_url, hit_artist, hit_title)`` or ``(None, None, None)``.
    """
    target_title = _clean_title(title, artist)
    clean_artist = artist.replace(" - Topic", "").strip()

    for search_query in _get_search_queries(artist, title):
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
    """Scrape lyrics HTML from a Genius page."""
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
    """Align Genius lyrics start point using the first line of LRCLIB anchor."""
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
    """Scrape Genius lyrics, aligned with LRCLIB anchor.

    Parameters
    ----------
    artist : str
        Clean artist name (from LRCLIB result).
    title : str
        Clean track title (from LRCLIB result).
    anchor : str
        Plain lyrics from LRCLIB used as alignment anchor.

    Returns
    -------
    str | None
        Aligned Genius lyrics, or ``None``.
    """
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
