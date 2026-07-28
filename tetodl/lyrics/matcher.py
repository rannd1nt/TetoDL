from __future__ import annotations

import re
from difflib import SequenceMatcher

from tetodl.lyrics.models import LyricsData, LyricsQuery

TITLE_WEIGHT = 0.55
ARTIST_WEIGHT = 0.30
DURATION_WEIGHT = 0.15
DURATION_TOLERANCE = 10.0
MIN_SCORE = 0.4
NON_ALPHABET_BONUS = 0.05
SHORT_NAME_LENGTH = 3


def _normalize(s: str) -> str:
    return re.sub(r'[\W_]+', '', s.lower()) if s else ""


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, _normalize(a), _normalize(b)).ratio()


def _contains_based_similarity(a: str, b: str) -> float:
    na, nb = _normalize(a), _normalize(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    if na in nb:
        return len(na) / len(nb)
    if nb in na:
        return len(nb) / len(na)
    return SequenceMatcher(None, na, nb).ratio()


def _has_non_alphabet(text: str) -> bool:
    if not text:
        return False
    non_latin = sum(1 for c in text if ord(c) > 0x2E80)
    return non_latin / max(len(text), 1) >= 0.05


def _normalize_line(line: str) -> str:
    return re.sub(r'[\W_]+', '', line.lower()).strip()


def anchor_matches(anchor_line: str, genius_line: str) -> bool:
    a = _normalize_line(anchor_line)
    g = _normalize_line(genius_line)
    if not a or not g:
        return False
    if a == g:
        return True
    return SequenceMatcher(None, a, g).ratio() >= 0.99


def is_valid_match(
    search_title: str,
    result_title: str,
    search_artist: str | None = None,
    result_artist: str | None = None,
    threshold: float = 0.4,
) -> bool:
    s1 = _normalize(search_title)
    s2 = _normalize(result_title)

    if not s1 or not s2:
        return False

    title_match = s1 in s2 or s2 in s1 or _similarity(search_title, result_title) >= threshold
    if not title_match:
        return False

    if search_artist and result_artist:
        a1 = _normalize(search_artist)
        a2 = _normalize(result_artist)

        if len(a1) < 2 or len(a2) < 2:
            return True

        if a1 not in a2 and a2 not in a1 and _similarity(search_artist, result_artist) < 0.6:
            return False

    return True


def calculate_score(query: LyricsQuery, candidate: LyricsData) -> float:
    title_score = _contains_based_similarity(query.title, candidate.title) if query.title and candidate.title else 0.0
    artist_score = _contains_based_similarity(query.artist, candidate.artist) if query.artist and candidate.artist else 0.0

    if query.artist and candidate.artist:
        a1 = _normalize(query.artist)
        a2 = _normalize(candidate.artist)
        if len(a1) <= SHORT_NAME_LENGTH or len(a2) <= SHORT_NAME_LENGTH:
            if a1 != a2 and title_score < 0.85:
                return 0.0
            if a1 != a2:
                artist_score *= 0.5

    if query.title and candidate.title:
        t1 = _normalize(query.title)
        t2 = _normalize(candidate.title)
        if t1 == t2 and len(t1) <= SHORT_NAME_LENGTH:
            if query.artist and candidate.artist:
                a1 = _normalize(query.artist)
                a2 = _normalize(candidate.artist)
                if a1 != a2 and not (a1 in a2 or a2 in a1):
                    return 0.0

    duration_score = 0.0
    if query.duration > 0 and candidate.duration > 0:
        delta = abs(query.duration - candidate.duration)
        if delta <= 2.0:
            duration_score = 1.0
        elif delta <= DURATION_TOLERANCE:
            duration_score = 1.0 - (delta - 2.0) / (DURATION_TOLERANCE - 2.0)
        else:
            duration_score = 0.0

    score = (title_score * TITLE_WEIGHT) + (artist_score * ARTIST_WEIGHT) + (duration_score * DURATION_WEIGHT)
    if candidate.plain_lyrics and _has_non_alphabet(candidate.plain_lyrics):
        score += NON_ALPHABET_BONUS
    return score
