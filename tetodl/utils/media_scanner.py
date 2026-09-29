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
Media file scanner for Android gallery (moved from legacy ``media/scanner``)
"""
import os
import shutil
import subprocess

from tetodl.utils.tracer import trace, traced

from ..utils.console import console
from ..utils.i18n_keys import Keys


@trace
def scan_media_files(target_path):
    """
    Register a media file or directory with the Android media scanner.

    On Termux the function delegates to ``termux-media-scan`` for efficient
    recursive scanning.  If that utility is unavailable it falls back to
    sending a ``MEDIA_SCANNER_SCAN_FILE`` broadcast intent via ``am``.

    Parameters
    ----------
    target_path : str
        Absolute path to a media file or directory to scan.  Directories are
        scanned recursively when ``termux-media-scan`` is available.

    Returns
    -------
    None
        This function does not return a value.  Success or failure is
        reported through the console.

    Raises
    ------
    None
        All exceptions are caught internally and logged via the console.

    Example
    -------
    >>> scan_media_files('/storage/emulated/0/Music/track.mp3')

    See Also
    --------
    :data:`tetodl.constants.IS_TERMUX` : Platform constant that gates the scan logic.
    """
    _is_termux = shutil.which("termux-media-scan") is not None
    if not _is_termux:
        return

    if not os.path.exists(target_path):
        with traced('path does not exist'):
            return

    try:
        with traced('starting media scan'), console.spin(Keys.media.scanning):
            if shutil.which("termux-media-scan"):
                cmd = ["termux-media-scan"]
                if os.path.isdir(target_path):
                    cmd.extend(["-r", target_path])
                else:
                    cmd.append(target_path)
                subprocess.run(cmd, check=False, timeout=10)
                return

            if os.path.isfile(target_path):
                scan_cmd = [
                    "am", "broadcast",
                    "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE",
                    "-d", f"file://{target_path}"
                ]
                subprocess.run(scan_cmd, capture_output=True, timeout=10)
            else:
                console.err(Keys.media.scan_skipped)
                console.err(Keys.media.termux_tools_missing)

    except Exception as e:
        console.err(Keys.media.scan_error(error=str(e)))
