import os
from ..utils.styles import print_error, print_success, print_info

try:
    # Import MP3 & ID3 Handlers
    from mutagen.mp3 import MP3
    from mutagen.id3 import (
        ID3, USLT, APIC, TIT2, TPE1, TALB, TPE2, TCOM, TCON, TDRC, TRCK, TPOS, ID3NoHeaderError
    )
    
    # Import MP4/M4A Handlers
    from mutagen.mp4 import MP4, MP4Cover
    
    # Import FLAC Handlers
    from mutagen.flac import FLAC
    
    HAS_MUTAGEN = True
except ImportError:
    HAS_MUTAGEN = False

def embed_lyrics(file_path, lyrics_text):
    """
    Embed lyrics into audio file (MP3/M4A/FLAC).
    """
    if not HAS_MUTAGEN:
        print_error("Mutagen library not found. Cannot embed lyrics.")
        return False

    if not os.path.exists(file_path):
        return False
        
    ext = os.path.splitext(file_path)[1].lower()
    
    try:
        # === MP3 (USLT Frame) ===
        if ext == '.mp3':
            try:
                audio = ID3(file_path)
            except ID3NoHeaderError:
                audio = ID3()
            
            # USLT: Unsynchronized Lyric Text
            # encoding=3 (UTF-8), lang='eng', desc='Lyrics'
            audio.add(USLT(encoding=3, lang='eng', desc='Lyrics', text=lyrics_text))
            audio.save(file_path)
            return True

        # === M4A (iTunes Atom) ===
        elif ext == '.m4a':
            audio = MP4(file_path)
            # iTunes atom for lyrics is ©lyr
            audio['\xa9lyr'] = lyrics_text
            audio.save()
            return True
            
        # === FLAC (Vorbis Comment) ===
        elif ext == '.flac':
            audio = FLAC(file_path)
            audio['LYRICS'] = lyrics_text
            audio.save()
            return True
            
    except Exception as e:
        print_error(f"Failed to embed lyrics: {e}")
        return False
        
    return False

def embed_metadata(audio_path, thumbnail_path, audio_format, metadata=None):
    """
    Embed Cover Art AND Rich Metadata (Composer, Album Artist, Year, etc.).
    Replaces the old simple embedding function.
    """
    if not HAS_MUTAGEN:
        return False

    if not os.path.exists(audio_path):
        return False

    has_cover = thumbnail_path and os.path.exists(thumbnail_path)

    try:
        # ==================================================
        # FORMAT MP3 (ID3v2.4)
        # ==================================================
        if audio_format == 'mp3':
            try:
                audio = MP3(audio_path, ID3=ID3)
            except Exception:
                audio = ID3(audio_path)
            
            try:
                audio.add_tags()
            except ID3NoHeaderError:
                pass
            
            # 1. Embed Cover Art (APIC)
            if has_cover:
                with open(thumbnail_path, 'rb') as albumart:
                    audio.tags.add(
                        APIC(
                            encoding=3, # 3 is UTF-8
                            mime='image/jpeg', # Default yt-dlp thumb is jpg
                            type=3, # 3 is Cover (front)
                            desc=u'Cover',
                            data=albumart.read()
                        )
                    )

            # 2. Embed Rich Metadata
            if metadata:
                # Basic Tags
                if metadata.get('title'): audio.tags.add(TIT2(encoding=3, text=metadata['title']))
                if metadata.get('artist'): audio.tags.add(TPE1(encoding=3, text=metadata['artist']))
                if metadata.get('album'): audio.tags.add(TALB(encoding=3, text=metadata['album']))
                
                # Advanced Tags ("Sultan" Metadata)
                if metadata.get('album_artist'): 
                    audio.tags.add(TPE2(encoding=3, text=metadata['album_artist'])) # Album Artist
                if metadata.get('composer'): 
                    audio.tags.add(TCOM(encoding=3, text=metadata['composer']))     # Composer
                if metadata.get('genre'): 
                    audio.tags.add(TCON(encoding=3, text=metadata['genre']))        # Genre
                if metadata.get('date'): 
                    audio.tags.add(TDRC(encoding=3, text=metadata['date']))         # Recording Date (YYYY)
                if metadata.get('track_num'):
                    audio.tags.add(TRCK(encoding=3, text=str(metadata['track_num']))) # Track Num
                if metadata.get('disc_num'):
                    audio.tags.add(TPOS(encoding=3, text=str(metadata['disc_num'])))  # Disc Num

            audio.save()
            return True

        # ==================================================
        # FORMAT M4A (MP4 Atoms)
        # ==================================================
        elif audio_format == 'm4a':
            audio = MP4(audio_path)
            
            # 1. Embed Cover Art (covr)
            if has_cover:
                with open(thumbnail_path, 'rb') as f:
                    # M4A butuh wrapper MP4Cover
                    audio['covr'] = [MP4Cover(f.read(), imageformat=MP4Cover.FORMAT_JPEG)]

            # 2. Embed Rich Metadata
            if metadata:
                # Basic Atoms
                if metadata.get('title'): audio['\xa9nam'] = metadata['title']
                if metadata.get('artist'): audio['\xa9ART'] = metadata['artist']
                if metadata.get('album'): audio['\xa9alb'] = metadata['album']
                
                # Advanced Atoms
                if metadata.get('album_artist'): 
                    audio['aART'] = metadata['album_artist'] # Album Artist
                if metadata.get('composer'): 
                    audio['\xa9wrt'] = metadata['composer']  # Composer/Writer
                if metadata.get('genre'): 
                    audio['\xa9gen'] = metadata['genre']     # Genre
                if metadata.get('date'): 
                    audio['\xa9day'] = metadata['date']      # Release Date
                
                # Track & Disc parsing (String '1/12' -> Tuple (1, 12))
                if metadata.get('track_num'):
                    try:
                        tn = str(metadata['track_num']).split('/')
                        current = int(tn[0])
                        total = int(tn[1]) if len(tn) > 1 else 0
                        audio['trkn'] = [(current, total)]
                    except: pass
                
                if metadata.get('disc_num'):
                    try:
                        dn = str(metadata['disc_num']).split('/')
                        current = int(dn[0])
                        total = int(dn[1]) if len(dn) > 1 else 0
                        audio['disk'] = [(current, total)]
                    except: pass

            audio.save()
            return True

    except Exception as e:
        print_error(f"Metadata embedding error: {e}")
        return False
    
    return False