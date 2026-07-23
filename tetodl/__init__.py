"""
TetoDL - An User Friendly and Configurable TUI/CLI Media Downloader
"""
import sys
import os

from .constants import APP_VERSION
__version__ = APP_VERSION
__author__ = "rannd1nt"

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

if hasattr(sys, '_MEIPASS'):
    _mei = sys._MEIPASS
    if _mei not in os.environ.get('PATH', ''):
        os.environ['PATH'] = _mei + os.pathsep + os.environ.get('PATH', '')

# yt-dlp override injection (binary mode)
try:
    from tetodl.constants import YTDLP_OVERRIDE_DIR
    if YTDLP_OVERRIDE_DIR.exists() and (YTDLP_OVERRIDE_DIR / "yt_dlp").is_dir():
        sys.path.insert(0, str(YTDLP_OVERRIDE_DIR))
except Exception:
    pass