from __future__ import annotations

import abc
import importlib.util
import os
import subprocess

from tetodl.core.domain.env import env
from tetodl.utils.console import console
from tetodl.utils.i18n_keys import Keys


class ThumbnailProcessor(abc.ABC):
    @abc.abstractmethod
    def crop_to_square(self, thumbnail_path: str) -> bool:
        ...

    @abc.abstractmethod
    def convert_format(self, thumbnail_path: str, target_format: str = "jpg") -> str | None:
        ...


class FFmpegThumbnailProcessor(ThumbnailProcessor):

    def crop_to_square(self, thumbnail_path: str) -> bool:
        try:
            output_path = thumbnail_path + ".square.jpg"
            cmd = [
                env.get('ffmpeg_cmd'), '-i', thumbnail_path,
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
            cmd = [env.get('ffmpeg_cmd'), '-i', thumbnail_path, '-y', output_path]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0 and os.path.exists(output_path):
                os.remove(thumbnail_path)
                return output_path
            return None
        except Exception:
            return None


class PyAVThumbnailProcessor(ThumbnailProcessor):

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
    if env.get('is_windows') and env.get('is_binary'):
        if importlib.util.find_spec("av") is not None:
            return PyAVThumbnailProcessor()
    return FFmpegThumbnailProcessor()


_processor = None


def _get_processor() -> ThumbnailProcessor:
    global _processor
    if _processor is None:
        _processor = get_thumbnail_processor()
    return _processor


def crop_thumbnail_to_square(thumbnail_path: str) -> bool:
    return _get_processor().crop_to_square(thumbnail_path)


def convert_thumbnail_format(thumbnail_path: str, target_format: str = "jpg") -> str | None:
    return _get_processor().convert_format(thumbnail_path, target_format)
