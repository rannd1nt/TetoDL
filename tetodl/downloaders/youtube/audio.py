"""
Core logic for single audio processing
"""
import os
import re
import glob
from typing import Optional, Tuple, Union

try:
    import yt_dlp as yt
except Exception:
    yt = None

from ...constants import FFMPEG_CMD, RuntimeConfig
from ...utils.i18n import get_text as _
from ...utils.styles import print_process, print_info, print_success, print_error
from ...utils.spinner import Spinner
from ...utils.network import is_forbidden_error
from ...utils.hooks import QuietLogger, get_progress_hook
from ...utils.files import clean_temp_files
from ...utils.processing import get_audio_extension, get_audio_format_string, build_audio_postprocessors
from ...utils.metadata_fetcher import fetcher
from ...core.cache import get_cached_metadata, cache_metadata
from ...core.history import add_to_history
from ...media.scanner import scan_media_files
from ...media.tagger import embed_lyrics, embed_metadata
from ...media.thumbnail import download_and_process_thumbnail

def download_single_audio(
    url: str, 
    target_dir: str, 
    use_cache: bool = True, 
    is_youtube_music: bool = False,
    download_type: str = "Single Track", 
    cut_range: Optional[Tuple[float, float]] = None, 
    quiet: bool = False
) -> Tuple[bool, str, bool]:
    """
    Orchestrates the complete download lifecycle for a single audio track.

    This function handles the entire process: fetching metadata via yt-dlp, itunes & genius, 
    configuring FFmpeg for audio conversion.
    
    The `cut_range` parameter supports precise trimming (e.g., from '58:09' to '1:02:12')
    or open-ended ranges (e.g., '58:09-' for start-to-end), automatically handled 
    via the internal time parser.
    """

    audio_format = get_audio_extension()
    current_style = getattr(RuntimeConfig, 'PROGRESS_STYLE', 'minimal')

    try:
        with yt.YoutubeDL({'quiet': True, 'no_warnings': True, 'extract_flat': False}) as ydl:
            info = ydl.extract_info(url, download=False)
            id = info.get('id')
            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            artist = info.get('artist') or info.get('uploader') or "Unknown Artist"
            album = info.get('album')
            
            if is_youtube_music:
                history_title = f"{artist} - {title}"
            else:
                history_title = title

        if is_youtube_music:
            outtmpl = os.path.join(target_dir, f"%(artist)s - %(title)s.%(ext)s")
        else:
            outtmpl = os.path.join(target_dir, f"%(title)s.%(ext)s")

        
        format_string = get_audio_format_string(audio_format)
        postprocessors = build_audio_postprocessors(audio_format, is_youtube_music)
        hook = [] if quiet else [get_progress_hook(current_style)]

        ydl_opts = {
            'format': format_string,
            'outtmpl': outtmpl,
            'postprocessors': postprocessors,
            'ffmpeg_location': FFMPEG_CMD,
            'quiet': True,
            'no_warnings': True,
            'writethumbnail': False,
            'logger': QuietLogger(),
            'progress_hooks': hook,
            'noprogress': True if quiet else False,
            'retries': RuntimeConfig.MAX_RETRIES, 
            'fragment_retries': RuntimeConfig.MAX_RETRIES,
            'file_access_retries': RuntimeConfig.MAX_RETRIES,
            'extractor_retries': 3,
        }

        if RuntimeConfig.NO_COVER_MODE:
            ydl_opts['postprocessors'] = [
                pp for pp in ydl_opts['postprocessors'] 
                if pp.get('key') != 'FFmpegMetadata'
            ]
            ydl_opts['add_metadata'] = False

        if cut_range:
            start, end = cut_range
            if not quiet: print_info(f"Trimming audio: {start}s to {end}s")
            
            ydl_opts['download_ranges'] = lambda info, ydl: [{'start_time': start, 'end_time': end}]
            ydl_opts['force_keyframes_at_cuts'] = True

        with yt.YoutubeDL(ydl_opts) as ydl:
            if use_cache:
                cached = get_cached_metadata(url)
                if cached:
                    if not quiet: print_info(_('download.youtube.using_cache', title=cached['metadata'].get('title', 'Unknown')))

            temp_filename_template = ydl.prepare_filename(info)
            base_name_clean = os.path.splitext(temp_filename_template)[0]
            possible_part_files = [
                f"{base_name_clean}.{audio_format}.part",
                f"{base_name_clean}.part",
                f"{temp_filename_template}.part"
            ]

            try:
                if cut_range:
                    if not quiet:
                        cut_spinner = Spinner(_('download.youtube.downloading_item', title=title) + ", Cutting...")
                        cut_spinner.start()
                    try:
                        ydl.download([url])
                    finally:
                        if not quiet:
                            cut_spinner.stop()
                else:
                    if not quiet: print_process(_('download.youtube.downloading_item', title=title))
                    ydl.download([url])
            
            except (KeyboardInterrupt, Exception) as e:
                if not quiet: print()
                if isinstance(e, KeyboardInterrupt):
                    if not quiet: print_error("Download cancelled by user.")
                else:
                    if not quiet: print_error(_('download.youtube.error_downloading', type='audio', error=str(e)))
                
                if not quiet: print_process("Cleaning up partial files...\r")
                
                for p_file in possible_part_files:
                    if os.path.exists(p_file):
                        try: os.remove(p_file)
                        except OSError: pass
                
                try:
                    for f in glob.glob(f"{base_name_clean}*"):
                        if f.endswith('.part') or f.endswith('.ytdl'):
                            try: os.remove(f)
                            except OSError: pass
                except Exception: pass
                
                if isinstance(e, KeyboardInterrupt):
                    raise e
                
                return False, str(e), False

            final_scan_path = None
            fetched_metadata = None
            
            if RuntimeConfig.NO_COVER_MODE:
                should_process_cover = False
            else:
                should_process_cover = (
                    (is_youtube_music or RuntimeConfig.SMART_COVER_MODE)
                    and audio_format != "opus"
                )

            if should_process_cover:
                if not quiet: print_process(_('download.youtube.processing_cover'))
                
                uploader = info.get('uploader', '')
                description = info.get('description', '')
                
                is_art_track = (
                    info.get('track') is not None or
                    ' - Topic' in uploader or
                    'Auto-generated by YouTube' in description or
                    'Provided to YouTube by' in description
                )
                
                if is_art_track:
                    should_crop = True
                    smart_search = RuntimeConfig.SMART_COVER_MODE
                else:
                    should_crop = False
                    smart_search = RuntimeConfig.SMART_COVER_MODE

                thumbnail_path, fetched_metadata = download_and_process_thumbnail(
                    info, 
                    target_dir, 
                    should_crop=should_crop, 
                    smart_mode=smart_search,
                    quiet=quiet
                )

                if thumbnail_path and os.path.exists(thumbnail_path):
                    audio_path = f"{base_name_clean}.{audio_format}"
                    
                    if os.path.exists(audio_path):
                        if not quiet: print_process(_('download.youtube.embedding_cover'))
                        final_metadata = {}
                        if fetched_metadata:
                            final_metadata = fetched_metadata
                        elif is_art_track or info.get('artist'):
                            final_metadata = {
                                'artist': info.get('artist') or info.get('uploader', '').replace(' - Topic', ''),
                                'album': info.get('album') or info.get('title'),
                                'title': info.get('track') or info.get('title')
                            }

                        if embed_metadata(audio_path, thumbnail_path, audio_format, final_metadata, quiet):
                            if not quiet: print_success(_('download.youtube.cover_success'))
                        else:
                            if not quiet: print_error(_('download.youtube.cover_failed'))
                            final_scan_path = audio_path
                    else:
                        if not quiet: print_error(_('download.youtube.file_not_found', filename=os.path.basename(audio_path)))
                    clean_temp_files(target_dir, info.get('id', ''), quiet)
                else:
                    if not quiet: print_error(_('download.youtube.cover_process_failed'))

            elif audio_format == "opus":
                if not quiet: print_info(_('download.youtube.skip_cover_opus'))
            else:
                if not quiet: print_info(_('download.youtube.skip_cover'))

            # --- FINISHING ---
            if final_scan_path is None:
                guessed_path = f"{base_name_clean}.{audio_format}"
                if os.path.exists(guessed_path):
                    final_scan_path = guessed_path

            if RuntimeConfig.LYRICS_MODE and final_scan_path and os.path.exists(final_scan_path):
                search_artist = ""
                search_title = ""
                
                if fetched_metadata: 
                    search_artist = fetched_metadata.get('artist')
                    search_title = fetched_metadata.get('title')
                else:
                    raw_video_title = info.get('title', '')
                    match = re.match(r'^(.*?)\s+-\s+(.*)$', raw_video_title)
                    
                    if match:
                        search_artist = match.group(1).strip()
                        raw_extracted_title = match.group(2).strip()
                        search_title = re.sub(r'\s*[\(\[].*?[\)\]]', '', raw_extracted_title).strip()
                    else:
                        search_artist = info.get('artist') or info.get('uploader', '').replace(' - Topic', '')
                        search_title = info.get('track') or info.get('title')

                if not quiet: print_process(f"Searching lyrics for: {search_artist} - {search_title}")
                
                lyrics = fetcher.fetch_lyrics_genius(
                    search_artist,
                    search_title,
                    romaji=RuntimeConfig.ROMAJI_MODE,
                    quiet=quiet
                )
                
                if lyrics:
                    if embed_lyrics(final_scan_path, lyrics, quiet):
                        if not quiet: print_success("Lyrics embedded successfully (Genius)")
                    else:
                        if not quiet: print_error("Failed to embed lyrics")
                else:
                    if not quiet: print_info("Lyrics not found on Genius.")
            
            if use_cache:
                cache_metadata(url, {
                    'title': title,
                    'duration': duration,
                    'uploader': info.get('uploader', ''),
                    'artist': info.get('artist', ''),
                    'album': info.get('album', ''),
                    'track': info.get('track', ''),
                    'thumbnails': info.get('thumbnails', [])
                })

            platform = "YouTube Music" if is_youtube_music else "YouTube Audio"
            artist = info.get('artist') or info.get('uploader') or "Unknown Artist"
            if is_youtube_music:
                history_title = f"{artist} - {title}"
            else:
                history_title = title
            
            final_saved_path = os.path.abspath(final_scan_path if final_scan_path else guessed_path)

            metadata = {
                'artist': artist,
                'album': album,
                'title': title
            }

            add_to_history(
                id=id,
                file_path=final_saved_path,
                success=True,
                title=history_title,
                content_type='audio',
                platform=platform,
                download_type=download_type,
                duration=duration,
                metadata=metadata
            )

            if RuntimeConfig.MEDIA_SCANNER_ENABLED:
                if final_scan_path:
                    abs_path = os.path.abspath(final_scan_path)
                    scan_media_files(abs_path)

        return True, title, False

    except Exception as e:
        if not quiet: print_error(_('download.youtube.error_downloading', type='audio', error=str(e)))
        return False, str(e), False