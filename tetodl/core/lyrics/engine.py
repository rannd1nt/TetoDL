from __future__ import annotations

from tetodl.core.domain.cache import get_cache
from tetodl.core.lyrics.matcher import MIN_SCORE, calculate_score
from tetodl.core.lyrics.models import LyricsData, LyricsQuery
from tetodl.core.lyrics.providers import get_lyrics_providers
from tetodl.core.lyrics.providers.genius import scrape_with_anchor


def _pick_best(candidates: list[LyricsData], query: LyricsQuery, fallback_query: LyricsQuery | None = None) -> LyricsData | None:
    best: LyricsData | None = None
    for candidate in candidates:
        candidate.score = calculate_score(query, candidate)
        if candidate.score >= MIN_SCORE:
            if best is None or candidate.score > best.score:
                best = candidate

    if best is not None:
        return best

    if fallback_query is not None:
        for candidate in candidates:
            score = calculate_score(fallback_query, candidate)
            if score >= MIN_SCORE:
                candidate.score = score
                if best is None or score > best.score:
                    best = candidate

    return best


def search_lyrics(artist: str, title: str, duration: float = 0.0) -> str | None:
    query = LyricsQuery(artist=artist, title=title, duration=duration)
    swapped = LyricsQuery(artist=title, title=artist, duration=duration)

    cache = get_cache("lyrics")
    cache_key = f"lyr:{artist}||{title}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    all_providers = get_lyrics_providers()
    lrclib_provider = next((p for p in all_providers if type(p).__name__ == "LRCLIBProvider"), None)

    lrclib_candidates: list[LyricsData] = []
    if lrclib_provider is not None:
        try:
            lrclib_candidates = lrclib_provider.search(query)
        except Exception:
            lrclib_candidates = []

    best = _pick_best(lrclib_candidates, query, fallback_query=swapped)

    if best is not None:
        anchor = best.plain_lyrics
        clean_artist = best.artist
        clean_title = best.title

        try:
            aligned = scrape_with_anchor(clean_artist, clean_title, anchor)
            if aligned:
                cache.set(cache_key, aligned)
                return aligned
        except Exception:
            pass

        cache.set(cache_key, anchor)
        return anchor

    for provider in all_providers:
        if provider is lrclib_provider:
            continue
        try:
            candidates = provider.search(query)
        except Exception:
            continue
        best = _pick_best(candidates, query, fallback_query=swapped)
        if best is not None:
            cache.set(cache_key, best.plain_lyrics)
            return best.plain_lyrics

    cache.set(cache_key, None)
    return None
