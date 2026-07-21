"""
TetoDL - An User Friendly and Configurable TUI/CLI Media Downloader
"""
import sys
import os

__version__ = "2.1.0"
__author__ = "rannd1nt"

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

if hasattr(sys, '_MEIPASS'):
    _mei = sys._MEIPASS
    if _mei not in os.environ.get('PATH', ''):
        os.environ['PATH'] = _mei + os.pathsep + os.environ.get('PATH', '')