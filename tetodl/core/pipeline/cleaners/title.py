from __future__ import annotations

import re

from tetodl.core.lyrics.providers.itunes import search_by_term


def clean_youtube_title(raw_title: str) -> tuple[str | None, str | None]:
    cleaned = raw_title.strip()
    if not cleaned:
        return None, None

    result = search_by_term(cleaned)
    if result:
        return result.get("artist"), result.get("title")

    return _regex_fallback(cleaned)


def _extract_jp_brackets(title: str) -> tuple[str | None, str | None]:
    for open_b, close_b in [("「", "」"), ("『", "』"), ("【", "】")]:
        m = re.match(rf"^(.+?)\s*{re.escape(open_b)}(.+?){re.escape(close_b)}", title)
        if m:
            artist_part = m.group(1).strip()
            title_part = m.group(2).strip()
            if artist_part and title_part:
                return artist_part, title_part
    return None, None


def _regex_fallback(raw_title: str) -> tuple[str | None, str | None]:
    title = raw_title.strip()

    jp_artist, jp_title = _extract_jp_brackets(title)
    if jp_artist and jp_title:
        return jp_artist, jp_title

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

    title = re.sub(r"\s+", " ", title).strip()

    for sep in [" - ", " ~ ", " | ", " – ", " — "]:
        if sep in title:
            parts = title.split(sep, 1)
            artist_part = parts[0].strip()
            title_part = parts[1].strip()
            if artist_part and title_part:
                return artist_part, title_part

    title = title.replace("-", " ").replace("/", " ").replace("|", " ").replace("_", " ").replace("×", " ")
    title = re.sub(r"\s+", " ", title).strip()
    return None, title if title else None
