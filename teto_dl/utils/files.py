"""
File operation utilities
"""
import os
import glob
import atexit
import shutil
from ..constants import TEMP_DIR
from ..utils.styles import print_error, print_process
from ..utils.i18n import get_text as _

class TempManager:
    """Singleton helper untuk mengelola file sementara."""
    
    @staticmethod
    def get_temp_dir():
        """Memastikan folder temp ada dan mengembalikan path-nya."""
        if not TEMP_DIR.exists():
            TEMP_DIR.mkdir(parents=True, exist_ok=True)
        return TEMP_DIR

    @staticmethod
    def cleanup():
        """Menghapus seluruh isi folder temp TetoDL."""
        if TEMP_DIR.exists():
            try:
                for item in TEMP_DIR.iterdir():
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
            except Exception as e:
                pass

atexit.register(TempManager.cleanup)

def remove_nomedia_file(folder_path):
    """
    Remove .nomedia file to make files visible in gallery
    """
    nomedia_path = os.path.join(folder_path, ".nomedia")
    if os.path.exists(nomedia_path):
        try:
            os.remove(nomedia_path)
        except Exception as e:
            print_error(f"Gagal menghapus .nomedia: {e}")


def clean_temp_files(download_folder, video_id):
    """
    Clean temporary files after processing (thumbnails, temp files, etc.)

    Args:
        download_folder: Folder containing temporary files
        video_id: YouTube video ID to identify temp files
    """
    try:
        patterns = [
            f"{video_id}.jpg",
            f"{video_id}.webp",
            f"{video_id}.*.jpg",
            f"{video_id}.*.webp",
            "*.temp.*"
        ]

        deleted_files = []

        for pattern in patterns:
            for file_path in glob.glob(os.path.join(download_folder, pattern)):
                if os.path.isfile(file_path):
                    try:
                        os.remove(file_path)
                        deleted_files.append(os.path.basename(file_path))
                    except Exception as e:
                        print_error(_('media.temp_clean_error', error=str(e)))

        if deleted_files:
            print_process(f"Cleaned {len(deleted_files)} temporary files")

    except Exception as e:
        print_error(_('media.temp_clean_error', error=str(e)))

def get_free_space(path):
    """Helper buat dapetin free space dalam format GB yang manusiawi"""
    try:
        if not os.path.exists(path):
            check_path = os.path.dirname(path)
        else:
            check_path = path
            
        _, _, free = shutil.disk_usage(check_path)
        return f"{free / (2**30):.1f} GB free"
    except:
        return "N/A"