"""
Media file scanner for Android gallery (Optimized & Debugged)
"""
import os
import subprocess
import shutil
from ..utils.spinner import Spinner
from ..constants import IS_TERMUX
from ..utils.styles import print_info, print_error

def scan_media_files(target_path):
    """
    Scan media file.
    """
    if not IS_TERMUX:
        return

    if not os.path.exists(target_path):
        return

    spinner = Spinner("Scanning media...")
    spinner.start()
    try:
        if shutil.which("termux-media-scan"):
            cmd = ["termux-media-scan"]
            if os.path.isdir(target_path):
                cmd.extend(["-r", target_path])
            else:
                cmd.append(target_path)

            subprocess.run(cmd, check=False, timeout=10)
            spinner.stop()
            return

        if os.path.isfile(target_path):
            scan_cmd = [
                "am", "broadcast",
                "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE",
                "-d", f"file://{target_path}"
            ]
            subprocess.run(scan_cmd, capture_output=True, timeout=10)
            spinner.stop()
        else:
            spinner.stop()
            print_error("Scanning Skipped")
            print_error("Termux tools missing. Install 'termux-tools' for folder scanning.")

    except Exception as e:
        print_error(f"Scan error: {e}")