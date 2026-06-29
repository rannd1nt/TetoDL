"""
Media file scanner for Android gallery (Optimized & Debugged)
"""
import os
import subprocess
import shutil
from ..utils.console import console
from ..utils.i18n_keys import Keys
from ..constants import IS_TERMUX

def scan_media_files(target_path):
    """
    Scan media file.
    """
    if not IS_TERMUX:
        return

    if not os.path.exists(target_path):
        return

    try:
        with console.spin("Scanning media..."):
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
        console.err(Keys.media.scan_error(error=e))