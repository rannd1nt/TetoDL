"""
Thumbnail processing and embedding for all audio formats
"""
import os
import subprocess
import requests
from ..constants import FFMPEG_CMD
from ..utils.i18n import get_text as _
from ..utils.colors import print_error


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


def download_and_process_thumbnail(info_dict, download_folder):
    """
    Download and process thumbnail - crop to square ratio
    """
    try:
        if info_dict.get('thumbnails') and len(info_dict['thumbnails']) > 0:
            thumbnail = info_dict['thumbnails'][-1]
            thumbnail_url = thumbnail.get('url')
            
            if thumbnail_url:
                thumbnail_filename = f"{info_dict['id']}.jpg"
                thumbnail_path = os.path.join(download_folder, thumbnail_filename)
                
                response = requests.get(thumbnail_url, timeout=10)
                if response.status_code == 200:
                    with open(thumbnail_path, 'wb') as f:
                        f.write(response.content)
                    
                    if crop_thumbnail_to_square(thumbnail_path):
                        return thumbnail_path
                    else:
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
        
        elif audio_format == "opus":
            cmd = [
                FFMPEG_CMD,
                '-i', audio_path,
                '-i', thumbnail_path,
                '-map', '0',
                '-map', '1',
                '-c:a', 'copy',
                '-c:v', 'libtheora',
                '-q:v', '8',
                '-y',
                temp_output
            ]
        
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