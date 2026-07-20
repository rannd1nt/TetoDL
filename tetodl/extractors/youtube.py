"""
YouTubeExtractor — extract metadata from YouTube/YT Music URLs via yt-dlp.
"""

try:
    import yt_dlp as yt
except ImportError:
    yt = None

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
            with yt.YoutubeDL({"quiet": True, "no_warnings": True, "extract_flat": False}) as ydl:
                raw = ydl.extract_info(url, download=False)
        except Exception as exc:
            with traced(f'extract failed — {exc}'):
                raise PipelineError(f"Failed to extract info: {exc}", "extract") from exc

        entries = None
        if raw.get("entries"):
            entries = [
                MediaInfo(
                    id=e.get("id", ""),
                    title=e.get("title", ""),
                    url=e.get("webpage_url", ""),
                    duration=e.get("duration", 0),
                    uploader=e.get("uploader", ""),
                    artist=e.get("artist"),
                    track=e.get("track"),
                    album=e.get("album"),
                    description=e.get("description", ""),
                    thumbnail=e.get("thumbnail"),
                    thumbnails=e.get("thumbnails", []),
                )
                for e in raw["entries"]
                if e
            ]

        is_pl = raw.get("_type") == "playlist" or bool(raw.get("entries"))
        with traced(f'is_playlist={is_pl}, entries={len(entries) if entries else 0}'):
            return MediaInfo(
                id=raw.get("id", ""),
                title=raw.get("title", ""),
                url=raw.get("webpage_url", url),
                duration=raw.get("duration", 0),
                uploader=raw.get("uploader", ""),
                artist=raw.get("artist"),
                track=raw.get("track"),
                album=raw.get("album"),
                description=raw.get("description", ""),
                thumbnail=raw.get("thumbnail"),
                thumbnails=raw.get("thumbnails", []),
                webpage_url=raw.get("webpage_url", url),
                is_playlist=is_pl,
                entries=entries,
            )


register_extractor(YouTubeExtractor)