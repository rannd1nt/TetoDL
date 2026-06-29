"""
ExtractStep — fetch media metadata from YouTube via yt-dlp.
"""

try:
    import yt_dlp as yt
except ImportError:
    yt = None

from ...core.models import MediaInfo
from ...core.step import PipelineStep, PipelineError


class ExtractStep(PipelineStep[str, MediaInfo]):
    """Extract video/playlist metadata from a YouTube URL using yt-dlp.

    Calls ``yt_dlp.YoutubeDL.extract_info(url, download=False)`` and maps
    the result into a :class:`MediaInfo` instance.  If the URL points
    to a playlist the ``entries`` field will contain the individual items.

    Raises :class:`PipelineError` if yt-dlp is unavailable or the
    extraction fails.
    """

    def __call__(self, url: str) -> MediaInfo:
        """Extract metadata for the given URL.

        Parameters
        ----------
        url : str
            YouTube URL (video or playlist).

        Returns
        -------
        MediaInfo
            Structured metadata from yt-dlp.

        Raises
        ------
        PipelineError
            If yt-dlp is not installed or the extraction request fails.
        """
        if yt is None:
            raise PipelineError("yt-dlp is not available", "extract")

        try:
            with yt.YoutubeDL({"quiet": True, "no_warnings": True, "extract_flat": False}) as ydl:
                raw = ydl.extract_info(url, download=False)
        except Exception as exc:
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
            is_playlist=raw.get("_type") == "playlist" or bool(raw.get("entries")),
            entries=entries,
        )
