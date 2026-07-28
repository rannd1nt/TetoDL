from __future__ import annotations

from abc import ABC, abstractmethod

from tetodl.core.cover.models import CoverData, CoverQuery


class CoverProvider(ABC):
    @abstractmethod
    def search(self, query: CoverQuery) -> CoverData | None:
        ...
