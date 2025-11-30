"""
File operation utilities
"""
import os
import re
import glob
from .colors import print_error, print_process
from .i18n import get_text as _


def create_nomedia_file(folder_path):
    """
    Remove .nomedia file to make files visible in gallery
    """
    nomedia_path = os.path.join(folder_path, ".nomedia")
    if os.path.exists(nomedia_path):
        try:
            os.remove(nomedia_path)
            # print_process(f"Menghapus .nomedia dari {folder_path}")
        except Exception as e:
            print_error(f"Gagal menghapus .nomedia: {e}")


def check_file_exists(title, target_dir, file_type="audio", audio_format=None):
    """
    Check if file already exists in target directory with robust pattern matching
    
    Args:
        title: File title to search for
        target_dir: Target directory to search in
        file_type: Type of file ("audio" or "video")
        audio_format: Specific audio format to check (mp3, m4a, opus) - if None, checks all formats
    
    Returns:
        (exists: bool, file_path: str or None)
    """
    try:
        clean_title = re.sub(r'[<>:"/\\|?*]', '', title)
        
        patterns = []
        
        if file_type == "audio":
            if audio_format:
                extensions = [f'*.{audio_format}']
            else:
                extensions = ['*.mp3', '*.m4a', '*.opus']
        else:
            extensions = ['*.mp4', '*.webm', '*.mkv']
        
        if clean_title:
            for ext in extensions:
                patterns.append(f"*{clean_title}*{ext}")
        
        if len(clean_title) > 30:
            short_title = clean_title[:30]
            for ext in extensions:
                patterns.append(f"*{short_title}*{ext}")
        
        words = re.findall(r'[a-zA-Z0-9\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af]+', title)
        if words:
            for word in words[:3]:
                if len(word) > 2:
                    for ext in extensions:
                        patterns.append(f"*{word}*{ext}")
        
        patterns = list(set(patterns))
        
        for pattern in patterns:
            try:
                for file_path in glob.glob(os.path.join(target_dir, pattern)):
                    if os.path.isfile(file_path):
                        file_size = os.path.getsize(file_path)
                        if file_size > 1024 * 10:
                            filename = os.path.basename(file_path)
                            similarity = calculate_similarity(title, filename)
                            if similarity > 0.3:
                                return True, file_path
            except Exception:
                continue
        
        return False, None
        
    except Exception as e:
        print_error(_('error.file_check_failed', error=str(e)))
        return False, None


def calculate_similarity(str1, str2):
    """
    Calculate simple similarity between two strings using Jaccard similarity
    
    Args:
        str1: First string
        str2: Second string
    
    Returns:
        float: Similarity score between 0 and 1
    """
    try:
        s1 = str1.lower()
        s2 = str2.lower()
        
        words1 = set(re.findall(r'[a-zA-Z0-9\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af]+', s1))
        words2 = set(re.findall(r'[a-zA-Z0-9\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af]+', s2))
        
        if not words1 or not words2:
            return 0
            
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0
    except:
        return 0


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