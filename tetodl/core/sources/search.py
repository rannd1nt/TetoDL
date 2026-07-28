from tetodl.core.domain.env import env
from tetodl.core.extractor import Extractor, register_extractor
from tetodl.core.domain.models import MediaInfo
from tetodl.core.domain.step import PipelineError

try:
    import yt_dlp as yt
except ImportError:
    yt = None


class SearchExtractor(Extractor):
    @staticmethod
    def handles(url: str) -> bool:
        return url.startswith("ytsearch")

    def extract(self, url: str) -> MediaInfo:
        if yt is None:
            raise PipelineError("yt-dlp is not available", "extract")

        try:
            with yt.YoutubeDL({
                "quiet": True,
                "no_warnings": True,
                "extract_flat": False,
                "cachedir": env.get('ytdlp_cache_dir'),
            }) as ydl:
                raw = ydl.extract_info(url, download=False)
        except Exception as exc:
            raise PipelineError(
                f"Search extraction failed: {exc}", "extract"
            ) from exc

        return MediaInfo(
            id=raw.get("id") or "",
            title=raw.get("title") or "",
            url=raw.get("webpage_url") or url,
            duration=raw.get("duration") or 0,
            uploader=raw.get("uploader") or "",
            artist=raw.get("artist"),
            track=raw.get("track"),
            thumbnail=raw.get("thumbnail"),
            thumbnails=raw.get("thumbnails") or [],
            webpage_url=raw.get("webpage_url") or url,
        )


register_extractor(SearchExtractor)
