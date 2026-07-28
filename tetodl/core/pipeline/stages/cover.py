import os

from tetodl.core.cover import CoverData, CoverQuery, CoverService
from tetodl.core.domain.models import CoverResult, LyricsMetadata, MediaInfo, PipelineContext
from tetodl.core.domain.step import PipelineStep
from tetodl.core.domain.tagger import embed_metadata
from tetodl.core.pipeline.cleaners.title import clean_youtube_title
from tetodl.core.pipeline.metadata import resolve_artist_title
from tetodl.utils.console import console
from tetodl.utils.files import clean_temp_files
from tetodl.utils.i18n_keys import Keys
from tetodl.utils.tracer import trace, traced


class CoverStep(PipelineStep[PipelineContext, PipelineContext]):
    _cover_service = CoverService()

    @trace
    def __call__(self, ctx: PipelineContext) -> PipelineContext:
        if ctx.media_info is None or ctx.downloaded_file is None:
            return ctx

        if ctx.config.no_cover_mode or ctx.media_type != "audio":
            return ctx

        if ctx.config.audio_quality == "opus":
            console.warn(Keys.download.youtube.skip_cover_opus)
            return ctx

        if not (ctx.is_youtube_music or ctx.config.smart_cover_mode):
            console.warn(Keys.download.youtube.skip_cover)
            return ctx

        if not ctx.config.quiet:
            console.proc(Keys.download.youtube.processing_cover)

        info = ctx.media_info
        target_dir = ctx.target_dir
        is_art = self._is_art_track(info)
        path = None
        cover_data = None
        spotify_cover = False

        if ctx.cover_url:
            with traced("trying Spotify cover art"):
                path = self._download_url(ctx.cover_url, target_dir, info.id)
            if path is None:
                with traced("Spotify cover failed, falling back to smart download"):
                    path, cover_data = self._smart_download(info, target_dir, ctx)
            else:
                spotify_cover = True
        elif ctx.config.smart_cover_mode:
            with traced("trying smart download (CoverService)"):
                path, cover_data = self._smart_download(info, target_dir, ctx)

        if path is None and not ctx.cover_url:
            with traced("falling back to YouTube thumbnail"):
                path = self._youtube_fallback(
                    info, target_dir, is_art,
                    ctx.config.force_crop, ctx.config.smart_cover_mode,
                )

        if path is None or not os.path.exists(path):
            with traced("no cover art obtained"):
                console.err(Keys.download.youtube.cover_process_failed)
                return ctx

        if ctx.config.smart_cover_mode and not cover_data and spotify_cover:
            with traced("fetching metadata from CoverService"):
                artist, title = resolve_artist_title(info, ctx=ctx)
                if artist and title:
                    cover_data = self._cover_service.search(CoverQuery(artist=artist, title=title))

        if not ctx.config.quiet:
            console.proc(Keys.download.youtube.embedding_cover)
        meta = self._build_metadata(info, cover_data, is_art)

        if embed_metadata(ctx.downloaded_file.path, path, ctx.config.audio_quality, meta):
            if not ctx.config.quiet:
                console.ok(Keys.download.youtube.cover_success)
        else:
            console.err(Keys.download.youtube.cover_failed)

        clean_temp_files(target_dir, info.id)
        cropped = is_art or ctx.config.force_crop
        source = "spotify" if spotify_cover else ("smart" if cover_data else "youtube")
        ctx.cover_result = CoverResult(
            thumbnail_path=path,
            metadata=self._to_lyrics_metadata(cover_data),
            source=source,
            cropped=cropped,
        )
        return ctx

    def _download_url(self, url: str, target_dir: str, file_id: str) -> str | None:
        path = os.path.join(target_dir, f"{file_id}.jpg")
        data = self._cover_service.fetch(url)
        if data is None:
            return None
        with open(path, "wb") as f:
            f.write(data)
        return path

    def _smart_download(
        self,
        info: MediaInfo,
        target_dir: str,
        ctx: PipelineContext | None = None,
    ) -> tuple[str | None, CoverData | None]:
        artist, title = resolve_artist_title(info, ctx=ctx)
        if not artist and not title:
            return None, None

        query = CoverQuery(artist=artist, title=title)
        cover_data = self._cover_service.search(query)
        if cover_data is None:
            return None, None

        img_data = self._cover_service.fetch(cover_data.url)
        if img_data is None:
            return None, None

        thumb_path = os.path.join(target_dir, f"{info.id}.jpg")
        with open(thumb_path, "wb") as f:
            f.write(img_data)

        console.ok(Keys.download.youtube.fetch_success)
        console.ok(Keys.media.cover_art_found_via(source=cover_data.source))
        return thumb_path, cover_data

    @staticmethod
    def _is_art_track(info: MediaInfo) -> bool:
        desc = (info.description or "").lower()
        is_topic = info.uploader.endswith(" - Topic")
        is_auto = "auto-generated by youtube" in desc or "provided to youtube by" in desc
        return info.track is not None or is_topic or is_auto

    def _youtube_fallback(
        self,
        info: MediaInfo,
        target_dir: str,
        is_art: bool,
        force_crop: bool = False,
        smart_mode: bool = False,
    ) -> str | None:
        candidates: list[str] = []
        if info.thumbnail:
            candidates.append(info.thumbnail)
        for t in reversed(info.thumbnails):
            url = t.get("url")
            if url and url not in candidates:
                candidates.append(url)

        thumb_path = os.path.join(target_dir, f"{info.id}.jpg")
        downloaded = False

        for url in candidates:
            data = self._cover_service.fetch(url)
            if data is not None:
                with open(thumb_path, "wb") as f:
                    f.write(data)
                downloaded = True
                break

        if not downloaded:
            return None

        perform_crop = is_art or force_crop or smart_mode
        return self._cover_service.process(
            thumb_path, crop=perform_crop, target_format="jpg")

    @staticmethod
    def _build_metadata(
        info: MediaInfo,
        cover_data: CoverData | None,
        is_art_track: bool,
    ) -> dict:
        if cover_data:
            return {
                "artist": cover_data.artist or info.artist or info.uploader.replace(" - Topic", ""),
                "album": cover_data.album or info.album or info.title,
                "title": cover_data.title or info.track or info.title,
                "album_artist": cover_data.album_artist or "",
                "genre": cover_data.genre or "",
                "year": str(cover_data.year) if cover_data.year else "",
                "composer": cover_data.composer or "",
            }

        artist = info.artist or info.uploader.replace(" - Topic", "")
        title = info.track or info.title

        if not info.artist and not info.track and info.title:
            clean_artist, clean_title = clean_youtube_title(info.title)
            if clean_artist:
                artist = clean_artist
            if clean_title:
                title = clean_title

        return {
            "artist": artist,
            "album": info.album or title,
            "title": title,
        }

    @staticmethod
    def _to_lyrics_metadata(cover_data: CoverData | None) -> LyricsMetadata | None:
        if not cover_data:
            return None
        return LyricsMetadata(
            artist=cover_data.artist,
            title=cover_data.title,
            album=cover_data.album,
            album_artist=cover_data.album_artist,
            genre=cover_data.genre,
            year=cover_data.year,
            composer=cover_data.composer,
            cover_url=cover_data.url,
        )
