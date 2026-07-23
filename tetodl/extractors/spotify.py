from ..core.extractor import Extractor, register_extractor
from ..core.models import MediaInfo
from ..core.spotify import SpotifyResolver
from ..core.step import PipelineError


class SpotifyExtractor(Extractor):
    @staticmethod
    def handles(url: str) -> bool:
        return "spotify.com" in url

    def extract(self, url: str) -> MediaInfo:
        try:
            resolver = SpotifyResolver()
            tracks = resolver.resolve(url)
        except Exception as exc:
            raise PipelineError(f"Spotify extraction failed: {exc}", "extract") from exc

        if not tracks:
            raise PipelineError("No tracks found", "extract")

        entries = [
            MediaInfo(
                id=t.spotify_id or "",
                title=f"{t.title} - {t.artist}",
                url="",
                artist=t.artist or "",
                track=t.title or "",
                album=t.album or "",
                duration=(t.duration_ms or 0) // 1000,
                thumbnail=t.cover_url or "",
            )
            for t in tracks
        ]

        playlist_title = (
            tracks[0].album if len(tracks) > 1 else tracks[0].title
        )

        return MediaInfo(
            id="spotify",
            title=playlist_title,
            url=url,
            is_playlist=len(tracks) > 1,
            entries=entries if len(tracks) > 1 else None,
            artist=tracks[0].artist or "",
            track=tracks[0].title or "",
        )


register_extractor(SpotifyExtractor)

