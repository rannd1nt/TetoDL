"""
Thumbnail processing and embedding for all audio formats
"""
import os
import subprocess
import requests
from ..constants import FFMPEG_CMD, RuntimeConfig
from ..utils.i18n import get_text as _
from ..utils.styles import print_error, print_success
from ..utils.metadata_fetcher import fetch_cover

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
    
def download_and_process_thumbnail(info_dict, download_folder, should_crop=True, smart_mode=True):
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
        if RuntimeConfig.SMART_COVER_MODE and not should_crop:
            artist = info_dict.get('artist') or info_dict.get('uploader', '').replace(' - Topic', '')
            title = info_dict.get('track') or info_dict.get('title')
            
            try:
                itunes_data = fetch_cover(artist, title)
                
                if itunes_data:
                    image_url = itunes_data.get('url')
                    if image_url:
                        response = requests.get(image_url, headers=FAKE_HEADERS, timeout=10)
                        if response.status_code == 200:
                            print_success(_('download.youtube.fetch_succes'))
                            with open(thumbnail_path, 'wb') as f:
                                f.write(response.content)
                            
                            return thumbnail_path, itunes_data
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
        print_error(_('media.thumbnail_error', error=str(e)))
        return None, None


def embed_thumbnail_to_audio(audio_path, thumbnail_path, audio_format="mp3", metadata=None):
    """
    Embed thumbnail AND Metadata to audio file using FFmpeg.
    
    Args:
        metadata (dict, optional): {'artist': '...', 'album': '...', 'title': '...', 'date': '...'}
    """
    try:
        temp_output = audio_path + ".temp." + audio_format
        
        cmd = [
            FFMPEG_CMD, '-i', audio_path, '-i', thumbnail_path,
            '-map', '0:0', '-map', '1:0', '-c', 'copy'
        ]

        if metadata:
            meta_artist = metadata.get('artist') or ""
            meta_album = metadata.get('album') or ""
            meta_title = metadata.get('title') or ""
            meta_date = metadata.get('date') or ""

            if meta_artist: cmd.extend(['-metadata', f'artist={meta_artist}'])
            if meta_album:  cmd.extend(['-metadata', f'album={meta_album}'])
            if meta_title:  cmd.extend(['-metadata', f'title={meta_title}'])
            if meta_date:   cmd.extend(['-metadata', f'date={meta_date}'])

        if audio_format == "mp3":
            cmd.extend([
                '-id3v2_version', '3',
                '-metadata:s:v', 'title="Album cover"', 
                '-metadata:s:v', 'comment="Cover (front)"'
            ])
        elif audio_format == "m4a":
            cmd.extend(['-disposition:v:0', 'attached_pic'])
        else:
            return False
        
        cmd.extend(['-y', temp_output])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0 and os.path.exists(temp_output):
            os.remove(audio_path)
            os.rename(temp_output, audio_path)
            return True
        else:
            if os.path.exists(temp_output):
                os.remove(temp_output)
            return False
            
    except Exception as e:
        print_error(_('media.embed_error', error=str(e)))
        return False