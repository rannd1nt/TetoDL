from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any

from tetodl.utils.network import get_session


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


def _is_valid_match(
    search_title: str,
    result_title: str,
    search_artist: str | None = None,
    result_artist: str | None = None,
    threshold: float = 0.4,
) -> bool:
    def normalize(s):
        return re.sub(r"[\W_]+", "", s.lower()) if s else ""

    s1 = normalize(search_title)
    s2 = normalize(result_title)

    if not s1 or not s2:
        return False

    title_match = s1 in s2 or s2 in s1 or SequenceMatcher(None, s1, s2).ratio() >= threshold
    if not title_match:
        return False

    if search_artist and result_artist:
        a1 = normalize(search_artist)
        a2 = normalize(result_artist)

        if len(a1) < 2 or len(a2) < 2:
            return True

        is_artist_match = a1 in a2 or a2 in a1 or SequenceMatcher(None, a1, a2).ratio() >= 0.6
        if not is_artist_match:
            return False

    return True


def search(artist: str, title: str) -> dict[str, Any] | None:
    clean_artist = artist.replace(" - Topic", "").strip()
    clean_title = _clean_title(title, artist=clean_artist)
    if not clean_title:
        clean_title = title

    return _search_itunes(f"{clean_artist} {clean_title}", target_title=clean_title, target_artist=clean_artist)


def search_by_term(term: str) -> dict[str, Any] | None:
    return _search_itunes(term, target_title=term, target_artist=None)


def _search_itunes(term: str, target_title: str, target_artist: str | None) -> dict[str, Any] | None:
    try:
        resp = get_session().get(
            "https://itunes.apple.com/search",
            params={"term": term, "media": "music", "entity": "song", "limit": "10"},
            timeout=5,
        )
        data = resp.json()

        if data.get("resultCount", 0) > 0:
            for result in data["results"]:
                itunes_title = result.get("trackName")
                itunes_artist = result.get("artistName")

                if _is_valid_match(target_title, itunes_title, search_artist=target_artist, result_artist=itunes_artist):
                    artwork = result["artworkUrl100"].replace("100x100bb", "600x600bb")

                    release_date = result.get("releaseDate", "")
                    if release_date:
                        release_date = release_date.split("T")[0]

                    return {
                        "url": artwork,
                        "title": itunes_title,
                        "artist": result.get("artistName"),
                        "album": result.get("collectionName"),
                        "album_artist": result.get("collectionArtistName", result.get("artistName")),
                        "date": release_date,
                        "genre": result.get("primaryGenreName"),
                        "composer": result.get("composerName"),
                        "track_num": f"{result.get('trackNumber')}/{result.get('trackCount')}" if result.get("trackCount") else None,
                        "disc_num": f"{result.get('discNumber')}/{result.get('discCount')}" if result.get("discCount") else None,
                        "source": "iTunes",
                    }
        return None
    except Exception:
        return None
