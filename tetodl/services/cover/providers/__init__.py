from tetodl.services.cover.providers.base import CoverProvider
from tetodl.services.cover.providers.deezer import DeezerProvider
from tetodl.services.cover.providers.itunes import ITunesProvider
from tetodl.services.cover.providers.genius import GeniusCoverProvider

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
