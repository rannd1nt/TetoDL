"""
TetoDL - An User Friendly and Configurable TUI/CLI Media Downloader
"""
import sys
import os

__version__ = "1.3.0"
__author__ = "rannd1nt"

# ── PyInstaller bundled ffmpeg PATH fix ──────────────────────────────
# yt-dlp searches for ffmpeg via PATH. When running as a PyInstaller
# binary, ffmpeg.exe is extracted to sys._MEIPASS (a temp directory)
# which is NOT on PATH by default. Add it so yt-dlp can find it.
if hasattr(sys, '_MEIPASS'):
    _mei = sys._MEIPASS
    if _mei not in os.environ.get('PATH', ''):
        os.environ['PATH'] = _mei + os.pathsep + os.environ.get('PATH', '')