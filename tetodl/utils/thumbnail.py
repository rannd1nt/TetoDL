"""
Thumbnail processing — download, crop, convert, and smart-cover lookup.
Merged from legacy ``media/thumbnail`` and ``downloaders/youtube/tasks``.
"""
from __future__ import annotations
import os
import abc
import subprocess
from ..constants import FFMPEG_CMD, IS_WINDOWS, IS_BINARY, YTDLP_CACHE_DIR
from ..core import config as cfg
from ..core.image_cache import fetch_image
from ..core.models import DownloadResult
from ..utils.i18n_keys import Keys
from ..utils.console import console
from ..core.metadata_fetcher import fetcher
from ..utils.network import check_internet
from tetodl.utils.tracer import trace

try:
    import yt_dlp as yt
    from yt_dlp.utils import sanitize_filename
except Exception:
    yt = None


class ThumbnailProcessor(abc.ABC):
    """Abstract base for thumbnail image operations."""

    @abc.abstractmethod
    def crop_to_square(self, thumbnail_path: str) -> bool:
        ...

    @abc.abstractmethod
    def convert_format(self, thumbnail_path: str, target_format: str = "jpg") -> str | None:
        ...


class FFmpegThumbnailProcessor(ThumbnailProcessor):
    """Thumbnail processing via FFmpeg subprocess."""

    def crop_to_square(self, thumbnail_path: str) -> bool:
        try:
            output_path = thumbnail_path + ".square.jpg"
            cmd = [
                FFMPEG_CMD, '-i', thumbnail_path,
                '-vf', r'crop=min(iw\,ih):min(iw\,ih)',
                '-y', output_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0 and os.path.exists(output_path):
                os.remove(thumbnail_path)
                os.rename(output_path, thumbnail_path)
                return True
            console.err(Keys.media.crop_failed(error=result.stderr))
            return False
        except Exception as e:
            console.err(Keys.media.crop_error(error=str(e)))
            return False

    def convert_format(self, thumbnail_path: str, target_format: str = "jpg") -> str | None:
        try:
            ext = target_format.lower().replace('jpeg', 'jpg')
            output_path = f"{os.path.splitext(thumbnail_path)[0]}.converted.{ext}"
            cmd = [FFMPEG_CMD, '-i', thumbnail_path, '-y', output_path]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0 and os.path.exists(output_path):
                os.remove(thumbnail_path)
                return output_path
            return None
        except Exception:
            return None


class PyAVThumbnailProcessor(ThumbnailProcessor):
    """Thumbnail processing via PyAV (av) library — Windows binary fallback."""

    def crop_to_square(self, thumbnail_path: str) -> bool:
        try:
            import av
            container = av.open(thumbnail_path)
            frame = next(container.decode(video=0))
            img = frame.to_image()
            w, h = img.size
            size = min(w, h)
            left = (w - size) // 2
            top = (h - size) // 2
            cropped = img.crop((left, top, left + size, top + size))
            cropped.save(thumbnail_path)
            container.close()
            return True
        except Exception as e:
            console.err(Keys.media.crop_error(error=str(e)))
            return False

    def convert_format(self, thumbnail_path: str, target_format: str = "jpg") -> str | None:
        try:
            ext = target_format.lower().replace('jpeg', 'jpg')
            output_path = f"{os.path.splitext(thumbnail_path)[0]}.converted.{ext}"
            from PIL import Image
            img = Image.open(thumbnail_path)
            img.save(output_path)
            os.remove(thumbnail_path)
            return output_path
        except Exception:
            return None


def get_thumbnail_processor() -> ThumbnailProcessor:
    """Factory: pick the best thumbnail processor for the current platform."""
    if IS_WINDOWS and IS_BINARY:
        try:
            import av  # noqa: F401
            return PyAVThumbnailProcessor()
        except ImportError:
            pass
    return FFmpegThumbnailProcessor()


_processor = None


def _get_processor() -> ThumbnailProcessor:
    global _processor
    if _processor is None:
        _processor = get_thumbnail_processor()
    return _processor
def crop_thumbnail_to_square(thumbnail_path):
    return _get_processor().crop_to_square(thumbnail_path)


def convert_thumbnail_format(thumbnail_path, target_format="jpg"):
    return _get_processor().convert_format(thumbnail_path, target_format)

@trace
def download_and_process_thumbnail(info_dict, download_folder, should_crop=True, smart_mode=True, force_crop=False):
    """
    Download a thumbnail with a robust fallback strategy.

    Attempts to fetch cover art from external metadata sources (Genius /
    iTunes) when *smart_mode* is enabled, then falls back to the candidate
    URLs provided by yt-dlp.  Optionally crops the result to a square or
    converts it to a standard format.

    Parameters
    ----------
    info_dict : dict
        Video / track information dictionary as returned by yt-dlp.
    download_folder : str
        Directory path where the thumbnail file should be saved.
    should_crop : bool, optional
        Whether to crop the downloaded thumbnail to a 1:1 square.
        Defaults to ``True``.
    smart_mode : bool, optional
        Whether to attempt a smart cover-art lookup (Genius / iTunes) before
        falling back to yt-dlp thumbnails.  Defaults to ``True``.
    force_crop : bool, optional
        Override configuration and force cropping regardless of other flags.
        Defaults to ``False``.

    Returns
    -------
    tuple of (str or None, dict or None)
        A ``(thumbnail_path, metadata_dict)`` tuple where *thumbnail_path*
        is the path to the saved thumbnail (or ``None`` on failure) and
        *metadata_dict* contains additional metadata from the smart lookup
        (or ``None`` when not available).

    Raises
    ------
    None
        All exceptions are caught internally and result in ``(None, None)``.

    Example
    -------
    >>> info = {'id': 'abc123', 'title': 'Song Title', 'uploader': 'Artist'}
    >>> path, meta = download_and_process_thumbnail(info, '/tmp/downloads')
    >>> path
    '/tmp/downloads/abc123.jpg'

    See Also
    --------
    :func:`crop_thumbnail_to_square` : Square-crop a downloaded thumbnail.
    :func:`convert_thumbnail_format` : Convert a thumbnail to a different format.
    :func:`download_thumbnail_task` : Standalone entry point for the ``--thumbnail-only`` flag.
    """
    try:
        thumbnail_filename = f"{info_dict['id']}.jpg"
        thumbnail_path = os.path.join(download_folder, thumbnail_filename)

        if smart_mode:
            artist = info_dict.get('artist') or info_dict.get('uploader', '').replace(' - Topic', '')
            title = info_dict.get('track') or info_dict.get('title')
            fetched_data = None
            try:
                fetched_data = fetcher.fetch_metadata(artist, title)
            except Exception:
                pass
            if fetched_data:
                image_url = fetched_data.get('url')
                if image_url:
                    img_data = fetch_image(image_url)
                    if img_data is not None:
                        source = 'Genius' if fetched_data.get('source') == 'Genius' else 'iTunes'
                        console.ok(Keys.download.youtube.fetch_success)
                        console.ok(Keys.media.cover_art_found_via(source=source))
                        with open(thumbnail_path, 'wb') as f:
                            f.write(img_data)
                        return thumbnail_path, fetched_data

        candidate_urls = []
        if info_dict.get('thumbnail'):
            candidate_urls.append(info_dict.get('thumbnail'))
        if info_dict.get('thumbnails'):
            for t in reversed(info_dict['thumbnails']):
                if t.get('url') and t.get('url') not in candidate_urls:
                    candidate_urls.append(t['url'])

        downloaded = False
        for url in candidate_urls:
            img_data = fetch_image(url)
            if img_data is not None:
                with open(thumbnail_path, 'wb') as f:
                    f.write(img_data)
                downloaded = True
                break

        if downloaded:
            perform_crop = should_crop or (force_crop or cfg.force_crop)
            if perform_crop:
                if crop_thumbnail_to_square(thumbnail_path):
                    return thumbnail_path, None
            else:
                converted_path = convert_thumbnail_format(thumbnail_path, "jpg")
                if converted_path:
                    return converted_path, None
            return thumbnail_path, None

        return None, None
    except Exception as e:
        console.err(Keys.media.thumbnail_error(error=str(e)))
        return None, None

@trace
def download_thumbnail_task(url, target_format='jpg', ui=None):
    """
    Run the standalone ``--thumbnail-only`` task.

    Downloads cover art (via smart lookup or yt-dlp) based on the current
    configuration without downloading the actual media file.  Handles both
    single videos and playlists, and optionally converts the result to the
    requested format.

    Parameters
    ----------
    url : str
        YouTube video or playlist URL to extract thumbnails from.
    target_format : str, optional
        Desired output format extension (``'jpg'``, ``'png'``, or
        ``'webp'``).  Defaults to ``'jpg'``.
    ui : :class:`~tetodl.ui.provider.UIProvider` or None, optional
        Optional user-interface provider for folder selection and display.
        When ``None`` a :class:`~tetodl.ui.provider.NullUI` instance is
        created internally.

    Returns
    -------
    :class:`~tetodl.core.models.DownloadResult`
        Result object indicating success status, the saved file path, and
        the number of files processed.

    Raises
    ------
    None
        All errors (network, extraction, I/O) are caught internally and
        reported through the console.

    Example
    -------
    >>> result = download_thumbnail_task('https://www.youtube.com/watch?v=abc123')
    >>> result.success
    True

    See Also
    --------
    :func:`download_and_process_thumbnail` : Core download-and-process logic.
    :func:`_process_single_thumbnail` : Per-item processing helper.
    """
    if ui is None:
        from ..ui.provider import NullUI
        ui = NullUI()

    target_dir = cfg.thumbnail_root
    if not os.path.exists(target_dir):
        try:
            os.makedirs(target_dir, exist_ok=True)
        except OSError as e:
            console.err(Keys.media.cannot_create_thumb_dir(error=str(e)))
            return DownloadResult(success=False)

    ui.clear()
    ui.header()

    if not check_internet():
        console.err(Keys.download.youtube.no_internet)
        return DownloadResult(success=False)

    try:
        with console.spin("Extracting information..."):
            with yt.YoutubeDL({'quiet': True, 'no_warnings': True, 'cachedir': YTDLP_CACHE_DIR}) as ydl:
                info = ydl.extract_info(url, download=False)
    except Exception as e:
        console.err(Keys.media.extraction_failed(error=str(e)))
        return DownloadResult(success=False)

    if 'entries' in info:
        console.warn(Keys.media.playlist_detected(title=info.get('title')))
        entries = list(info['entries'])
        total = len(entries)
        console.proc(Keys.media.found_items_processing(count=total))
        success_count = 0
        first_path = None
        for i, entry in enumerate(entries, 1):
            console.proc(Keys.media.processing_entry(current=i, total=total, title=entry.get('title')))
            fpath = _process_single_thumbnail(entry, target_dir, target_format=target_format)
            if fpath:
                success_count += 1
                if not first_path:
                    first_path = fpath
        console.ok(Keys.media.processed_thumbnails(success=success_count, total=total))
        ui.wait_and_clear_prompt()
        target_dir_abs = os.path.abspath(target_dir)
        return DownloadResult(success=success_count > 0, file_path=target_dir_abs, file_count=success_count)
    else:
        fpath = _process_single_thumbnail(info, target_dir, target_format=target_format)
        ui.wait_and_clear_prompt()
        return DownloadResult(success=bool(fpath), file_path=fpath, file_count=1 if fpath else 0)

def _process_single_thumbnail(info, target_dir, target_format='jpg'):
    """Download, crop, convert, and rename a single thumbnail entry."""
    title = info.get('title', 'Unknown')
    console.proc(Keys.media.processing_cover_for(title=title))

    uploader = info.get('uploader', '')
    description = info.get('description', '')

    is_art_track = (
        info.get('track') is not None or
        ' - Topic' in uploader or
        'Auto-generated by YouTube' in description or
        'Provided to YouTube by' in description
    )

    should_crop = is_art_track
    smart_search = cfg.smart_cover_mode and not is_art_track

    thumb_path, metadata = download_and_process_thumbnail(
        info, target_dir, should_crop=should_crop, smart_mode=smart_search
    )

    if thumb_path and os.path.exists(thumb_path):
        final_path = thumb_path
        if target_format != 'jpg':
            converted = convert_thumbnail_format(thumb_path, target_format)
            if converted:
                final_path = converted

        try:
            final_title = metadata.get('title') if metadata else title
            final_artist = metadata.get('artist') if metadata else info.get('uploader')

            ext = target_format

            if final_artist and final_title:
                new_name = f"{final_artist} - {final_title}.{ext}"
            else:
                new_name = f"{final_title}.{ext}"

            safe_name = sanitize_filename(new_name)
            new_path = os.path.join(target_dir, safe_name)

            if os.path.exists(new_path):
                os.remove(new_path)
            os.rename(final_path, new_path)

            console.ok(Keys.media.thumbnail_saved(name=safe_name))
            return os.path.abspath(new_path)
        except Exception:
            console.err(Keys.media.thumbnail_saved_as(name=os.path.basename(final_path)))
            return os.path.abspath(final_path)
    else:
        console.err(Keys.media.failed_to_download_thumbnail)
        return None
