from __future__ import annotations

from abc import ABC, abstractmethod

from tetodl.lyrics.models import LyricsData, LyricsQuery


class LyricsProvider(ABC):
    @abstractmethod
    def search(self, query: LyricsQuery) -> list[LyricsData]:
        ...
