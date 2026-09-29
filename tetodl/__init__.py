# Copyright 2026 rannd1nt
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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

# yt-dlp override injection (binary mode only — lazy, cached env)
if getattr(sys, 'frozen', False) or hasattr(sys, '_MEIPASS'):
    try:
        from pathlib import Path
        from tetodl.core.domain.env import env
        _override = Path(env.get("ytdlp_override_dir"))
        if _override.exists() and (_override / "yt_dlp").is_dir():
            sys.path.insert(0, str(_override))
    except Exception:
        pass