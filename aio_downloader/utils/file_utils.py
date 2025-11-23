"""
File operation utilities
"""
import os
import re
import glob
from .colors import print_error


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


def check_file_exists(title, target_dir, file_type="audio"):
    """
    Check if file already exists in target directory with robust pattern matching
    """
    try:
        # Clean title for pattern matching
        clean_title = re.sub(r'[<>:"/\\|?*]', '', title)
        
        patterns = []
        if file_type == "audio":
            extensions = ['*.mp3', '*.m4a', '*.webm']
        else:  # video
            extensions = ['*.mp4', '*.webm', '*.mkv']
        
        # Pattern 1: Original title (cleaned)
        if clean_title:
            for ext in extensions:
                patterns.append(f"*{clean_title}*{ext}")
        
        # Pattern 2: Truncated title if too long
        if len(clean_title) > 30:
            short_title = clean_title[:30]
            for ext in extensions:
                patterns.append(f"*{short_title}*{ext}")
        
        # Pattern 3: Search by parts (for Japanese characters)
        words = re.findall(r'[a-zA-Z0-9\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff]+', title)
        if words:
            for word in words[:3]:  # Take first 3 words
                if len(word) > 2:  # Minimum 3 characters
                    for ext in extensions:
                        patterns.append(f"*{word}*{ext}")
        
        # Remove duplicate patterns
        patterns = list(set(patterns))
        
        for pattern in patterns:
            try:
                for file_path in glob.glob(os.path.join(target_dir, pattern)):
                    if os.path.isfile(file_path):
                        file_size = os.path.getsize(file_path)
                        # Skip files that are too small (possibly corrupt)
                        if file_size > 1024 * 10:  # Minimum 10KB
                            # Verify with similarity check
                            filename = os.path.basename(file_path)
                            similarity = calculate_similarity(title, filename)
                            if similarity > 0.3:  # 30% similarity threshold
                                return True, file_path
            except Exception:
                continue
        
        return False, None
        
    except Exception as e:
        print_error(f"Error checking existing files: {e}")
        return False, None


def calculate_similarity(str1, str2):
    """
    Calculate simple similarity between two strings
    """
    try:
        # Convert to lowercase for case insensitive comparison
        s1 = str1.lower()
        s2 = str2.lower()
        
        # Calculate Jaccard similarity using words
        words1 = set(re.findall(r'[a-zA-Z0-9\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff]+', s1))
        words2 = set(re.findall(r'[a-zA-Z0-9\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff]+', s2))
        
        if not words1 or not words2:
            return 0
            
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0
    except:
        return 0


def clean_temp_files(download_folder, video_id):
    """
    Clean temporary files after processing
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
                        print_error(f"Gagal menghapus {file_path}: {e}")
        
        # if deleted_files:
        #     print_process(f"Menghapus {len(deleted_files)} file temporary")
            
    except Exception as e:
        print_error(f"Error cleaning temp files: {e}")