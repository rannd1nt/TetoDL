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

def convert_thumbnail_to_jpg(thumbnail_path):
    """
    Convert image to JPG without cropping.
    Fixes issue where YouTube serves WebP files even with .jpg extension.
    """
    try:
        output_path = thumbnail_path + ".fixed.jpg"
        
        # Command simple: Input -> Output (FFmpeg otomatis convert ke JPG karena ekstensi outputnya .jpg)
        cmd = [
            FFMPEG_CMD,
            '-i', thumbnail_path,
            '-y',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0 and os.path.exists(output_path):
            os.remove(thumbnail_path)
            os.rename(output_path, thumbnail_path)
            return True
        else:
            print_error(f"{_('media.convert_error')} {result.stderr}")
            return False
            
    except Exception as e:
        print_error(f"Error converting thumbnail: {str(e)}")
        return False
    
def download_and_process_thumbnail(info_dict, download_folder, should_crop=True, smart_mode=False):
    """
    smart_mode=True: Jika ini bukan Art Track, coba cari cover asli di internet (iTunes).
    should_crop=True: Paksa crop thumbnail YouTube (Logic lama untuk Art Track).
    """
    try:
        thumbnail_filename = f"{info_dict['id']}.jpg"
        thumbnail_path = os.path.join(download_folder, thumbnail_filename)
        
        # --- SMART COVER SEARCH ---
        if RuntimeConfig.SMART_COVER_MODE and not should_crop:
            artist = info_dict.get('artist') or info_dict.get('uploader', '').replace(' - Topic', '')
            title = info_dict.get('track') or info_dict.get('title')
            
            itunes_url = fetch_cover(artist, title)
            
            if itunes_url:
                response = requests.get(itunes_url, timeout=10)
                if response.status_code == 200:
                    print_success(_('download.youtube.fetch_succes'))
                    with open(thumbnail_path, 'wb') as f:
                        f.write(response.content)
                    return thumbnail_path
            
        if info_dict.get('thumbnails'):
            thumbnail = info_dict['thumbnails'][-1]
            thumbnail_url = thumbnail.get('url')
            
            response = requests.get(thumbnail_url, timeout=10)
            if response.status_code == 200:
                with open(thumbnail_path, 'wb') as f:
                    f.write(response.content)
                
                if should_crop:
                    # Art Track: Crop 1:1
                    if crop_thumbnail_to_square(thumbnail_path):
                        return thumbnail_path
                else:
                    # MV: Convert to JPG (No Crop)
                    if convert_thumbnail_to_jpg(thumbnail_path):
                        return thumbnail_path

        return None
    except Exception as e:
        print_error(_('media.thumbnail_error', error=str(e)))
        return None


def embed_thumbnail_to_audio(audio_path, thumbnail_path, audio_format="mp3"):
    """
    Embed thumbnail to audio file (MP3, M4A, OPUS) using FFmpeg
    Supports all three formats with proper metadata handling
    """
    try:
        temp_output = audio_path + ".temp." + audio_format
        
        # Build FFmpeg command based on format
        if audio_format == "mp3":
            cmd = [
                FFMPEG_CMD,
                '-i', audio_path,
                '-i', thumbnail_path,
                '-map', '0:0',
                '-map', '1:0',
                '-c', 'copy',
                '-id3v2_version', '3',
                '-metadata:s:v', 'title="Album cover"',
                '-metadata:s:v', 'comment="Cover (front)"',
                '-y',
                temp_output
            ]
        
        elif audio_format == "m4a":
            cmd = [
                FFMPEG_CMD,
                '-i', audio_path,
                '-i', thumbnail_path,
                '-map', '0:0',
                '-map', '1:0',
                '-c', 'copy',
                '-disposition:v:0', 'attached_pic',
                '-y',
                temp_output
            ]
        
        # elif audio_format == "opus":
        #     cmd = [
        #         FFMPEG_CMD,
        #         '-i', audio_path,
        #         '-i', thumbnail_path,
        #         '-map', '0:0',
        #         '-map', '1:0',
        #         '-c:a', 'copy',
        #         '-c:v', 'copy',
        #         '-disposition:v:0', 'attached_pic',
        #         '-metadata:s:v', 'title="Album cover"',
        #         '-metadata:s:v', 'comment="Cover (front)"',
        #         '-y',
        #         temp_output
        #     ]
        
        else:
            print_error(f"Unsupported audio format: {audio_format}")
            return False
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0 and os.path.exists(temp_output):
            os.remove(audio_path)
            os.rename(temp_output, audio_path)
            return True
        else:
            print_error(f"{result.stderr}")
            if os.path.exists(temp_output):
                os.remove(temp_output)
            return False
            
    except Exception as e:
        print_error(_('media.embed_error', error=str(e)))
        return False