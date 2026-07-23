"""
YouTubeExtractor — extract metadata from YouTube/YT Music URLs via yt-dlp.
"""

try:
    import yt_dlp as yt
except ImportError:
    yt = None

from ..constants import YTDLP_CACHE_DIR
from ..core.extractor import Extractor, register_extractor
from ..core.models import MediaInfo
from ..core.step import PipelineError
from ..utils.tracer import trace, traced


class YouTubeExtractor(Extractor):
    """Extract metadata from YouTube URLs using yt-dlp.

    Supports single videos, playlists, and YouTube Music links.
    Registered automatically at import time.
    """

    @staticmethod
    def handles(url: str) -> bool:
        """Return ``True`` for ``youtube.com`` or ``youtu.be`` URLs."""
        return "youtube.com" in url or "youtu.be" in url

    @trace
    def extract(self, url: str) -> MediaInfo:
        """Extract metadata from a YouTube URL.

        Parameters
        ----------
        url : str
            Full YouTube URL (video, playlist, or music link).

        Returns
        -------
        MediaInfo
            Structured metadata from yt-dlp.

        Raises
        ------
        PipelineError
            If yt-dlp is unavailable or extraction fails.
        """
        if yt is None:
            raise PipelineError("yt-dlp is not available", "extract")

        try:
            with yt.YoutubeDL({"quiet": True, "no_warnings": True, "extract_flat": False, "cachedir": YTDLP_CACHE_DIR}) as ydl:
                raw = ydl.extract_info(url, download=False)
        except Exception as exc:
            with traced(f'extract failed — {exc}'):
                raise PipelineError(f"Failed to extract info: {exc}", "extract") from exc

        entries = None
        if raw.get("entries"):
            entries = [
                MediaInfo(
                    id=e.get("id", ""),
                    title=e.get("title", ""), # pyright: ignore[reportArgumentType]
                    url=e.get("webpage_url", ""), # pyright: ignore[reportArgumentType]
                    duration=e.get("duration", 0), # pyright: ignore[reportArgumentType]
                    uploader=e.get("uploader", ""), # pyright: ignore[reportArgumentType]
                    artist=e.get("artist"),
                    track=e.get("track"),
                    album=e.get("album"),
                    description=e.get("description", ""), # pyright: ignore[reportArgumentType]
                    thumbnail=e.get("thumbnail"),
                    thumbnails=e.get("thumbnails", []), # pyright: ignore[reportArgumentType]
                )
                for e in raw["entries"] # pyright: ignore[reportTypedDictNotRequiredAccess]
                if e
            ]

        is_pl = raw.get("_type") == "playlist" or bool(raw.get("entries"))
        with traced(f'is_playlist={is_pl}, entries={len(entries) if entries else 0}'):
            return MediaInfo(
                id=raw.get("id", ""),
                title=raw.get("title", ""), # pyright: ignore[reportArgumentType]
                url=raw.get("webpage_url", url), # pyright: ignore[reportArgumentType]
                duration=raw.get("duration", 0), # pyright: ignore[reportArgumentType]
                uploader=raw.get("uploader", ""), # pyright: ignore[reportArgumentType]
                artist=raw.get("artist"),
                track=raw.get("track"),
                album=raw.get("album"),
                description=raw.get("description", ""), # pyright: ignore[reportArgumentType]
                thumbnail=raw.get("thumbnail"),
                thumbnails=raw.get("thumbnails", []), # pyright: ignore[reportArgumentType]
                webpage_url=raw.get("webpage_url", url), # pyright: ignore[reportArgumentType]
                is_playlist=is_pl,
                entries=entries,
            )


register_extractor(YouTubeExtractor)