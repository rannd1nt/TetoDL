"""
Audio metadata tagging utilities using Mutagen.
Handles embedding of Lyrics, Cover Art, and ID3/MP4 tags.
"""
import os
from typing import Any

from tetodl.utils.tracer import trace

from ...utils.console import console
from ...utils.i18n_keys import Keys

try:
    # Import MP3 & ID3 Handlers
    # Import FLAC Handlers
    from mutagen.flac import FLAC
    from mutagen.id3 import (
        APIC,
        ID3,
        TALB,
        TCOM,
        TCON,
        TDRC,
        TIT2,
        TPE1,
        TPE2,
        TPOS,
        TRCK,
        USLT,
        ID3NoHeaderError,
    )
    from mutagen.mp3 import MP3

    # Import MP4/M4A Handlers
    from mutagen.mp4 import MP4, MP4Cover
    
    HAS_MUTAGEN = True
except ImportError:
    HAS_MUTAGEN = False

@trace
def embed_lyrics(file_path: str, lyrics_text: str) -> bool:
    """
    Embeds lyrics into the audio file based on its format.
    
    Supported Formats:
    - MP3: Uses ID3 USLT frame (Unsynchronized Lyric Text).
    - M4A: Uses iTunes '©lyr' atom.
    - FLAC: Uses Vorbis 'LYRICS' comment.
    """
    if not HAS_MUTAGEN:
        console.err(Keys.tagger.mutagen_not_found_lyrics)
        return False

    if not os.path.exists(file_path):
        console.err(Keys.tagger.file_not_found(path=file_path))
        return False

    ext = os.path.splitext(file_path)[1].lower()

    try:
        audio: ID3 | MP4 | FLAC
        # === MP3 (USLT Frame) ===
        if ext == '.mp3':
            try:
                audio = ID3(file_path)
            except ID3NoHeaderError:
                audio = ID3()
            
            # USLT parameters: encoding=3 (UTF-8), lang='eng', desc='Lyrics'
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
        console.err(Keys.tagger.failed_embed_lyrics(error=e))
        return False
        
    return False

@trace
def _open_audio(audio_path: str, audio_format: str):
    """Open audio file and return format-specific handler."""
    if audio_format == 'mp3':
        try:
            audio: MP3 | ID3 = MP3(audio_path, ID3=ID3)
        except Exception:
            audio = ID3(audio_path)
        if isinstance(audio, MP3):
            try:
                audio.add_tags()
            except ID3NoHeaderError:
                pass
        return audio
    elif audio_format == 'm4a':
        return MP4(audio_path)
    return None


def _save_audio(audio, audio_format: str, audio_path: str):
    if audio_format == 'mp3':
        audio.save()
    elif audio_format == 'm4a':
        audio.save()


def _embed_cover_mp3(tag_container: ID3, thumbnail_path: str):
    with open(thumbnail_path, 'rb') as albumart:
        tag_container.add(
            APIC(
                encoding=3,
                mime='image/jpeg',
                type=3,
                desc='Cover',
                data=albumart.read()
            )
        )


def _embed_cover_m4a(audio_m4a: MP4, thumbnail_path: str):
    with open(thumbnail_path, 'rb') as f:
        audio_m4a['covr'] = [MP4Cover(f.read(), imageformat=MP4Cover.FORMAT_JPEG)]


def _embed_tags_mp3(tag_container: ID3, metadata: dict[str, Any]):
    if metadata.get('title'):
        tag_container.add(TIT2(encoding=3, text=metadata['title']))
    if metadata.get('artist'):
        tag_container.add(TPE1(encoding=3, text=metadata['artist']))
    if metadata.get('album'):
        tag_container.add(TALB(encoding=3, text=metadata['album']))
    if metadata.get('album_artist'):
        tag_container.add(TPE2(encoding=3, text=metadata['album_artist']))
    if metadata.get('composer'):
        tag_container.add(TCOM(encoding=3, text=metadata['composer']))
    if metadata.get('genre'):
        tag_container.add(TCON(encoding=3, text=metadata['genre']))
    if metadata.get('date'):
        tag_container.add(TDRC(encoding=3, text=metadata['date']))
    if metadata.get('track_num'):
        tag_container.add(TRCK(encoding=3, text=str(metadata['track_num'])))
    if metadata.get('disc_num'):
        tag_container.add(TPOS(encoding=3, text=str(metadata['disc_num'])))


def _embed_tags_m4a(audio_m4a: MP4, metadata: dict[str, Any]):
    if metadata.get('title'):
        audio_m4a['\xa9nam'] = metadata['title']
    if metadata.get('artist'):
        audio_m4a['\xa9ART'] = metadata['artist']
    if metadata.get('album'):
        audio_m4a['\xa9alb'] = metadata['album']
    if metadata.get('album_artist'):
        audio_m4a['aART'] = metadata['album_artist']
    if metadata.get('composer'):
        audio_m4a['\xa9wrt'] = metadata['composer']
    if metadata.get('genre'):
        audio_m4a['\xa9gen'] = metadata['genre']
    if metadata.get('date'):
        audio_m4a['\xa9day'] = metadata['date']
    if metadata.get('track_num'):
        try:
            tn = str(metadata['track_num']).split('/')
            current = int(tn[0])
            total = int(tn[1]) if len(tn) > 1 else 0
            audio_m4a['trkn'] = [(current, total)]
        except Exception:
            pass
    if metadata.get('disc_num'):
        try:
            dn = str(metadata['disc_num']).split('/')
            current = int(dn[0])
            total = int(dn[1]) if len(dn) > 1 else 0
            audio_m4a['disk'] = [(current, total)]
        except Exception:
            pass


@trace
def embed_cover(audio_path: str, thumbnail_path: str, audio_format: str) -> bool:
    """Embed cover art image only (no text tags)."""
    if not HAS_MUTAGEN:
        console.err(Keys.tagger.mutagen_not_found_metadata)
        return False
    if not os.path.exists(audio_path) or not os.path.exists(thumbnail_path):
        return False

    try:
        if audio_format == 'mp3':
            audio = _open_audio(audio_path, audio_format)
            tag_container = audio.tags if isinstance(audio, MP3) else audio
            if tag_container is not None:
                _embed_cover_mp3(tag_container, thumbnail_path)
            _save_audio(audio, audio_format, audio_path)
            return True

        elif audio_format == 'm4a':
            audio_m4a = _open_audio(audio_path, audio_format)
            _embed_cover_m4a(audio_m4a, thumbnail_path)
            _save_audio(audio_m4a, audio_format, audio_path)
            return True

    except Exception as e:
        console.err(Keys.tagger.metadata_embedding_error(error=e))
    return False


@trace
def embed_metadata_tags(audio_path: str, audio_format: str, metadata: dict[str, Any]) -> bool:
    """Embed rich metadata text tags only (no cover art)."""
    if not HAS_MUTAGEN:
        console.err(Keys.tagger.mutagen_not_found_metadata)
        return False
    if not os.path.exists(audio_path):
        return False
    if not metadata:
        return True

    try:
        if audio_format == 'mp3':
            audio = _open_audio(audio_path, audio_format)
            tag_container = audio.tags if isinstance(audio, MP3) else audio
            if tag_container is not None:
                _embed_tags_mp3(tag_container, metadata)
            _save_audio(audio, audio_format, audio_path)
            return True

        elif audio_format == 'm4a':
            audio_m4a = _open_audio(audio_path, audio_format)
            _embed_tags_m4a(audio_m4a, metadata)
            _save_audio(audio_m4a, audio_format, audio_path)
            return True

    except Exception as e:
        console.err(Keys.tagger.metadata_embedding_error(error=e))
    return False


@trace
def embed_metadata(
    audio_path: str,
    thumbnail_path: str,
    audio_format: str,
    metadata: dict[str, Any] | None = None
) -> bool:
    """Embed cover art + metadata (wrapper around embed_cover + embed_metadata_tags)."""
    ok = embed_cover(audio_path, thumbnail_path, audio_format)
    if metadata:
        ok = embed_metadata_tags(audio_path, audio_format, metadata) and ok
    return ok