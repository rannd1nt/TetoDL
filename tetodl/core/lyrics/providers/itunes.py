from __future__ import annotations

from typing import Any

from tetodl.core.lyrics.matcher import is_valid_match
from tetodl.utils.network import get_session
from tetodl.utils.text_cleaner import clean_title


def search(artist: str, title: str) -> dict[str, Any] | None:
    clean_artist = artist.replace(" - Topic", "").strip()
    cleaned = clean_title(title, artist=clean_artist)
    if not cleaned:
        cleaned = title

    return _search_itunes(f"{clean_artist} {cleaned}", target_title=cleaned, target_artist=clean_artist)


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

                if is_valid_match(target_title, itunes_title, search_artist=target_artist, result_artist=itunes_artist):
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
