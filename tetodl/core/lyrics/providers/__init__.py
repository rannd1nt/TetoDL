from tetodl.core.lyrics.providers.base import LyricsProvider
from tetodl.core.lyrics.providers.genius import GeniusProvider
from tetodl.core.lyrics.providers.lrclib import LRCLIBProvider

_PROVIDERS: list[LyricsProvider] | None = None


def get_lyrics_providers() -> list[LyricsProvider]:
    global _PROVIDERS
    if _PROVIDERS is None:
        _PROVIDERS = [LRCLIBProvider(), GeniusProvider()]
    return _PROVIDERS


__all__ = ["LyricsProvider", "get_lyrics_providers"]
