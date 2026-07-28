from __future__ import annotations

import re


def clean_title(title: str, artist: str = "") -> str:
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

    clean_base = title.replace("-", " ").replace("/", " ").replace("|", " ").replace("_", " ").replace("×", " ")

    if artist and len(artist) > 2:
        clean_base = re.sub(f"(?i){re.escape(artist)}", "", clean_base)

    clean_base = re.sub(r"\s+", " ", clean_base).strip()
    return clean_base


def normalize_text(s: str) -> str:
    return re.sub(r"[\W_]+", "", s.lower()) if s else ""


def normalize_line(line: str) -> str:
    return re.sub(r"[\W_]+", "", line.lower()).strip()


def has_non_alphabet(text: str) -> bool:
    if not text:
        return False
    non_latin = sum(1 for c in text if ord(c) > 0x2E80)
    return non_latin / max(len(text), 1) >= 0.05


def get_search_queries(artist: str, title: str) -> list[str]:
    queries: list[str] = []
    clean_artist = artist.replace(" - Topic", "").strip()
    cleaned = clean_title(title, artist=clean_artist)
    queries.append(f"{clean_artist} {cleaned}")

    separators = r"\s*(?:/|-|\||×)\s*"
    parts = re.split(separators, title)
    if len(parts) > 1:
        candidate = clean_title(parts[0], clean_artist)
        if len(candidate) > 1:
            queries.append(f"{clean_artist} {candidate}")
            queries.append(candidate)

    queries.append(cleaned)

    seen: set[str] = set()
    unique: list[str] = []
    for q in queries:
        key = q.lower().strip()
        if key and key not in seen:
            seen.add(key)
            unique.append(q)
    return unique
