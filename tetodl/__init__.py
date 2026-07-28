"""
TetoDL - An User Friendly and Configurable TUI/CLI Media Downloader
"""
import os
import sys

from .constants import APP_VERSION

__version__ = APP_VERSION
__author__ = "rannd1nt"

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

if hasattr(sys, '_MEIPASS'):
    _mei = sys._MEIPASS # pyright: ignore[reportAttributeAccessIssue]
    if _mei not in os.environ.get('PATH', ''):
        os.environ['PATH'] = _mei + os.pathsep + os.environ.get('PATH', '')

# yt-dlp override injection (binary mode — lazy, cached env)
try:
    from pathlib import Path
    from tetodl.core.domain.env import env
    _override = Path(env.get("ytdlp_override_dir"))
    if _override.exists() and (_override / "yt_dlp").is_dir():
        sys.path.insert(0, str(_override))
except Exception:
    pass