"""
Media file scanner for Android gallery
"""
import os
import subprocess
from ..utils.spinner import Spinner
from ..utils.colors import print_success, print_error


def scan_media_files(folder_path):
    """
    Scan media files to make them appear in Android gallery
    """
    spinner = Spinner("Memulai memindai file...")
    spinner.start()
    
    try:
        # Use am broadcast for media scanning
        scan_cmd = [
            "am", "broadcast",
            "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE",
            "-d", f"file://{folder_path}"
        ]
        subprocess.run(scan_cmd, capture_output=True)
        
        # Scan all folders
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.endswith(('.mp3', '.mp4', '.m4a', '.webm')):
                    file_path = os.path.join(root, file)
                    scan_cmd_file = [
                        "am", "broadcast",
                        "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE", 
                        "-d", f"file://{file_path}"
                    ]
                    subprocess.run(scan_cmd_file, capture_output=True)
        
        spinner.stop()
        print_success("File selesai dipindai...")
    except Exception as e:
        spinner.stop()
        print_error(f"Gagal memindai media: {e}")