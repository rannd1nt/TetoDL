"""
File operation utilities
"""
import os
import glob
import atexit
import shutil
from ..constants import TEMP_DIR
from ..utils.styles import print_error, print_process, print_info, print_success
from ..utils.i18n import get_text as _

class TempManager:
    """Singleton helper for managing temporary files."""
    
    @staticmethod
    def get_temp_dir():
        """Ensure that the temp folder exists and return its path."""
        if not TEMP_DIR.exists():
            TEMP_DIR.mkdir(parents=True, exist_ok=True)
        return TEMP_DIR

    @staticmethod
    def cleanup():
        """Delete all contents of the TetoDL temp folder."""
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

def move_contents_and_cleanup(source_dir, target_dir):
    """
    Move all contents of source_dir to target_dir, then delete source_dir.
    """
    if not os.path.exists(source_dir): return []
    if not os.path.exists(target_dir): os.makedirs(target_dir, exist_ok=True)

    moved_files = []
    
    for item in os.listdir(source_dir):
        s = os.path.join(source_dir, item)
        d = os.path.join(target_dir, item)
        
        if os.path.isfile(s):
            if os.path.exists(d):
                try:
                    os.remove(d)
                except OSError:
                    pass
            
            try:
                shutil.move(s, d)
                moved_files.append(d)
            except Exception as e:
                print_error(f"Failed to move {item}: {e}")

    try:
        os.rmdir(source_dir) 
    except OSError:
        pass
        
    return moved_files

def create_zip_archive(source_dir_path):
    """
    Compress folder into a .zip file.
    Returns the absolute path to the generated zip file.
    """
    if not os.path.exists(source_dir_path):
        return None

    base_name = source_dir_path 
    
    try:
        parent_dir = os.path.dirname(source_dir_path)
        base_dir = os.path.basename(source_dir_path)
        
        zip_path = shutil.make_archive(base_name, 'zip', root_dir=parent_dir, base_dir=base_dir)
        return zip_path
    except Exception as e:
        print_error(f"Failed to create zip: {e}")
        return None

def create_zip_archive(source_dir_path):
    """
    Compress folder into a .zip file.
    Returns the ABSOLUTE PATH to the generated zip file.
    """
    if not os.path.exists(source_dir_path):
        print_error(f"Zip source not found: {source_dir_path}")
        return None

    abs_source = os.path.abspath(source_dir_path)
    parent_dir = os.path.dirname(abs_source)
    base_name = os.path.basename(abs_source)
    
    output_base = os.path.join(parent_dir, base_name)
    
    try:
        print_process(f"Archiving to {base_name}.zip ...")
        
        zip_path = shutil.make_archive(
            output_base, 
            'zip', 
            root_dir=parent_dir, 
            base_dir=base_name
        )
        
        if os.path.exists(zip_path):
            print_success(f"Archive created at: {zip_path}")
            print_success(f"Archive created: {os.path.basename(zip_path)}")
            return zip_path
        else:
            print_error(f"Zip reported success but file missing at: {zip_path}")
            return None

    except Exception as e:
        print_error(f"Failed to create zip: {e}")
        return None

def create_m3u8_playlist(target_dir, playlist_name, file_list):
    """
    Create an .m3u8 playlist file containing a list of file_lists.
    """
    if not file_list:
        return None
        
    safe_name = "".join([c for c in playlist_name if c.isalpha() or c.isdigit() or c in " ._-"]).strip()
    if not safe_name: safe_name = "Playlist"
    
    m3u_path = os.path.join(target_dir, f"{safe_name}.m3u8")
    
    try:
        with open(m3u_path, 'w', encoding='utf-8') as f:
            f.write("#EXTM3U\n")
            
            for filename in file_list:
                f.write(f"{os.path.basename(filename)}\n")
                
        print_success(f"Playlist generated: {os.path.basename(m3u_path)}")
        return m3u_path
    except Exception as e:
        print_error(f"Failed to create playlist: {e}")
        return None

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
    """Helper to get free space in a human-readable GB format"""
    try:
        if not os.path.exists(path):
            check_path = os.path.dirname(path)
        else:
            check_path = path
            
        _, _, free = shutil.disk_usage(check_path)
        return f"{free / (2**30):.1f} GB free"
    except:
        return "N/A"