"""
Thumbnail processing and embedding for all audio formats
"""
import os
import subprocess
import requests
from ..constants import FFMPEG_CMD, RuntimeConfig
from ..utils.i18n import get_text as _
from ..utils.styles import print_error, print_success, print_process
from ..utils.metadata_fetcher import fetcher

FAKE_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def crop_thumbnail_to_square(thumbnail_path):
    """
    Crop landscape 16:9 thumbnail to square 1:1 using FFmpeg
    """
    try:
        output_path = thumbnail_path + ".square.jpg"
        
        cmd = [
            FFMPEG_CMD,
            '-i', thumbnail_path,
            '-vf', r'crop=min(iw\,ih):min(iw\,ih)',
            '-y',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0 and os.path.exists(output_path):
            os.remove(thumbnail_path)
            os.rename(output_path, thumbnail_path)
            return True
        else:
            print_error(_('media.crop_failed', error=result.stderr))
            return False
            
    except Exception as e:
        print_error(_('media.crop_error', error=str(e)))
        return False

def convert_thumbnail_format(thumbnail_path, target_format="jpg"):
    """
    Convert image to target format (jpg, png, webp) using FFmpeg.
    """
    try:
        ext = target_format.lower().replace('jpeg', 'jpg')
        output_path = f"{os.path.splitext(thumbnail_path)[0]}.converted.{ext}"
        
        cmd = [
            FFMPEG_CMD,
            '-i', thumbnail_path,
            '-y',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0 and os.path.exists(output_path):
            os.remove(thumbnail_path)
            return output_path 
        else:
            return None
            
    except Exception:
        return None
    
def download_and_process_thumbnail(info_dict, download_folder, should_crop=True, smart_mode=True, quiet=False):
    """
    Downloads thumbnail with robust fallback strategy.
    
    Returns: 
        tuple(thumbnail_path, metadata_dict)
        
    * metadata_dict is None if using YouTube source.
    * metadata_dict contains Artist/Album/Title if found on iTunes.
    """
    try:
        thumbnail_filename = f"{info_dict['id']}.jpg"
        thumbnail_path = os.path.join(download_folder, thumbnail_filename)
        
        # --- SMART COVER ---
        if RuntimeConfig.SMART_COVER_MODE:
            artist = info_dict.get('artist') or info_dict.get('uploader', '').replace(' - Topic', '')
            title = info_dict.get('track') or info_dict.get('title')
            
            fetched_data = None

            try:
                fetched_data = fetcher.fetch_metadata(artist, title)
            except Exception:
                pass
            
            if fetched_data:
                try:
                    image_url = fetched_data.get('url')
                    if image_url:
                        response = requests.get(image_url, headers=FAKE_HEADERS, timeout=10)
                        if response.status_code == 200:
                            source = 'Genius' if fetched_data.get('source') == 'Genius' else 'iTunes'
                            if not quiet:
                                print_success(_('download.youtube.fetch_success'))
                                print_success(f"Cover art found via {source}!")
                            
                            with open(thumbnail_path, 'wb') as f:
                                f.write(response.content)
                            
                            return thumbnail_path, fetched_data
                except Exception:
                    pass

        # --- YOUTUBE FALLBACK ---
        candidate_urls = []
        if info_dict.get('thumbnail'):
            candidate_urls.append(info_dict.get('thumbnail'))
        if info_dict.get('thumbnails'):
            for t in reversed(info_dict['thumbnails']):
                if t.get('url') and t.get('url') not in candidate_urls:
                    candidate_urls.append(t['url'])

        downloaded = False
        for url in candidate_urls:
            try:
                response = requests.get(url, headers=FAKE_HEADERS, timeout=10)
                if response.status_code == 200:
                    with open(thumbnail_path, 'wb') as f:
                        f.write(response.content)
                    downloaded = True
                    break 
            except Exception:
                continue
        
        if downloaded:
            perform_crop = should_crop or RuntimeConfig.FORCE_CROP

            if perform_crop:
                if crop_thumbnail_to_square(thumbnail_path):
                    return thumbnail_path, None # Metadata None
            else:
                converted_path = convert_thumbnail_format(thumbnail_path, "jpg")
                if converted_path:
                    return converted_path, None # Metadata None
            
            return thumbnail_path, None

        return None, None

    except Exception as e:
        if not quiet:
            print_error(_('media.thumbnail_error', error=str(e)))
        return None, None