from __future__ import annotations

from tetodl.lyrics.providers.itunes import search as itunes_search
from tetodl.services.cover.models import CoverData, CoverQuery
from tetodl.services.cover.providers.base import CoverProvider


class ITunesProvider(CoverProvider):
    def search(self, query: CoverQuery) -> CoverData | None:
        if not query.artist and not query.title:
            return None

        try:
            result = itunes_search(query.artist, query.title)
        except Exception:
            return None

        if not result or not result.get("url"):
            return None

        year_raw: str | int | None = result.get("year") or result.get("date")
        year: int | None = None
        if year_raw is not None:
            if isinstance(year_raw, str):
                try:
                    year = int(year_raw[:4])
                except (ValueError, IndexError):
                    pass
            else:
                year = year_raw

        return CoverData(
            url=result["url"],
            source="iTunes",
            artist=result.get("artist", ""),
            title=result.get("title", ""),
            album=result.get("album"),
            album_artist=result.get("album_artist"),
            genre=result.get("genre"),
            year=year,
            composer=result.get("composer", ""),
        )
