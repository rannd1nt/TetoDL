from tetodl.core.cover.providers.base import CoverProvider
from tetodl.core.cover.providers.deezer import DeezerProvider
from tetodl.core.cover.providers.itunes import ITunesProvider
from tetodl.core.cover.providers.genius import GeniusCoverProvider

_PROVIDERS: list[CoverProvider] | None = None


def get_cover_providers() -> list[CoverProvider]:
    global _PROVIDERS
    if _PROVIDERS is None:
        _PROVIDERS = [
            DeezerProvider(),
            GeniusCoverProvider(),
            ITunesProvider(),
        ]
    return _PROVIDERS


__all__ = ["CoverProvider", "get_cover_providers"]
