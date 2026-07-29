import glob
import os

try:
    import yt_dlp as yt
except ImportError:
    yt = None  # type: ignore[assignment]

from yt_dlp.utils import sanitize_filename

from tetodl.core.domain.env import env
from tetodl.core.domain.models import DownloadedFile, MediaInfo, PipelineContext
from tetodl.core.domain.step import PipelineStep
from tetodl.utils.console import console
from tetodl.utils.hooks import QuietLogger, get_postprocessor_hook, get_progress_hook
from tetodl.utils.i18n_keys import Keys
from tetodl.utils.processing import (
    build_audio_postprocessors,
    get_audio_format_string,
)
from tetodl.utils.tracer import trace


class DownloadStep(PipelineStep[PipelineContext, PipelineContext]):
    def __init__(self) -> None:
        pass

    @trace
    def __call__(self, ctx: PipelineContext) -> PipelineContext:
        if ctx.media_info is None:
            ctx.error = "No media info available for download"
            return ctx
        if yt is None:
            ctx.error = "yt-dlp is not available"
            return ctx

        info = ctx.media_info
        target_dir = ctx.target_dir

        output_title = ctx.spotify_title or (info.title if info else "")
        safe = sanitize_filename(output_title) if ctx.spotify_title else output_title
        try:
            result = self._download(info, target_dir, ctx)
            ctx.downloaded_file = result
            return ctx
        except KeyboardInterrupt:
            self._cleanup_partial(target_dir, safe)
            raise
        except Exception as exc:
            self._cleanup_partial(target_dir, safe)
            ctx.error = str(exc)
            return ctx

    def _download(
        self,
        info: MediaInfo,
        target_dir: str,
        ctx: PipelineContext,
    ) -> DownloadedFile:
        title = ctx.spotify_title or info.title
        artist = ctx.spotify_artist or info.artist or info.uploader or ""
        safe = sanitize_filename(title)

        opts = self._build_ydl_opts(ctx)
        if ctx.spotify_title:
            opts["outtmpl"] = os.path.join(target_dir, f"{safe}.%(ext)s")

        if ctx.cut_range:
            start, end = ctx.cut_range
            console.warn(Keys.media.trimming_audio(start=str(start), end=str(end)))
            opts["download_ranges"] = lambda info, ydl: [{"start_time": start, "end_time": end}]
            opts["force_keyframes_at_cuts"] = True

        console.proc(Keys.download.youtube.downloading_item(title=title))
        with yt.YoutubeDL(opts) as ydl:  # type: ignore[arg-type]
            ydl.download([info.url])

        container = ctx.config.audio_quality if ctx.media_type == "audio" else ctx.config.video_container
        path = os.path.join(target_dir, f"{safe}.{container}")
        if not os.path.exists(path):
            guessed = self._find_file(target_dir, safe)
            path = guessed or path

        return DownloadedFile(
            path=os.path.abspath(path),
            container=container,
            title=title,
            artist=artist,
            duration=info.duration,
            info=info,
        )

    def _build_ydl_opts(self, ctx: PipelineContext) -> dict:
        if ctx.media_type == "video":
            return self._video_opts(ctx)
        return self._audio_opts(ctx)

    def _audio_opts(self, ctx: PipelineContext) -> dict:
        config = ctx.config
        fmt = get_audio_format_string(config.audio_quality)
        pps = build_audio_postprocessors(config.audio_quality)
        if config.no_cover_mode:
            pps = [pp for pp in pps if pp.get("key") != "FFmpegMetadata"]

        return {
            "format": fmt,
            "outtmpl": os.path.join(ctx.target_dir, "%(title)s.%(ext)s"),
            "postprocessors": pps,
            "ffmpeg_location": env.get('ffmpeg_cmd'),
            "quiet": True,
            "no_warnings": True,
            "writethumbnail": False,
            "logger": QuietLogger(),
            "progress_hooks": [get_progress_hook(config.progress_style)],
            "noprogress": False,
            "retries": config.max_retries,
            "fragment_retries": config.max_retries,
            "file_access_retries": config.max_retries,
            "extractor_retries": config.max_retries,
            "sleep_interval": config.jitter_min,
            "max_sleep_interval": config.jitter_max,
            "cachedir": env.get('ytdlp_cache_dir'),
        }

    def _video_opts(self, ctx: PipelineContext) -> dict:
        config = ctx.config
        pp_args: list[str] = []
        if config.video_codec == "h264":
            pp_args = [
                "-c:v", "libx264",
                "-profile:v", "main",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-movflags", "+faststart",
            ]
        elif config.video_codec == "h265":
            pp_args = ["-c:v", "libx265", "-c:a", "aac"]

        max_h = config.max_video_resolution.replace("p", "")
        video_fmt = f"bestvideo[height<={max_h}]+bestaudio/best[height<={max_h}]"
        progress = get_progress_hook(config.progress_style)
        pp_hook = [get_postprocessor_hook(
            f"Re-encoding video to {config.video_codec.upper()}..."
        )]

        return {
            "format": video_fmt,
            "merge_output_format": config.video_container,
            "outtmpl": os.path.join(ctx.target_dir, "%(title)s.%(ext)s"),
            "ffmpeg_location": env.get('ffmpeg_cmd'),
            "quiet": True,
            "no_warnings": True,
            "logger": QuietLogger(),
            "progress_hooks": [progress],
            "postprocessor_hooks": pp_hook,
            "postprocessor_args": pp_args if pp_args else None,
            "retries": config.max_retries,
            "fragment_retries": config.max_retries,
            "file_access_retries": config.max_retries,
            "extractor_retries": config.max_retries,
            "sleep_interval": config.jitter_min,
            "max_sleep_interval": config.jitter_max,
            "cachedir": env.get('ytdlp_cache_dir'),
        }

    @staticmethod
    def _cleanup_partial(target_dir: str, title: str) -> None:
        base = os.path.join(target_dir, title)
        for pattern in (f"{base}.*.part", f"{base}.part", f"{base}.ytdl"):
            for f in glob.glob(pattern):
                try:
                    os.remove(f)
                except OSError:
                    pass

    @staticmethod
    def _find_file(target_dir: str, title: str) -> str | None:
        base = os.path.join(target_dir, title)
        for f in glob.glob(f"{base}.*"):
            if not f.endswith(".part") and not f.endswith(".ytdl"):
                return f
        return None
