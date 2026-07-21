"""
Configuration management system for TetoDL.

This module holds the authoritative module-level configuration state that is
shared across the application.  All setter functions immediately persist the
change to ``config.json`` via :func:`save_config`.

See Also
--------
:class:`tetodl.core.models.AppConfig` : Pydantic model that snapshots the
    current module-level state.
:mod:`tetodl.constants` : Default values and path constants.
"""
import os
import json
from ..constants import (
    CONFIG_PATH, VALID_CONTAINERS, VALID_RESOLUTIONS, REGISTRY_PATH,
    DEFAULT_MUSIC_ROOT, DEFAULT_VIDEO_ROOT, DEFAULT_THUMBNAIL_ROOT, VALID_CODECS
)
from ..core.models import AppConfig
from ..utils.console import console
from ..utils.i18n import set_language, detect_system_language
from tetodl.utils.tracer import trace, traced
from ..utils.i18n_keys import Keys

# ==== MODULE-LEVEL CONFIG STATE ====
music_root: str = DEFAULT_MUSIC_ROOT
video_root: str = DEFAULT_VIDEO_ROOT
thumbnail_root: str = DEFAULT_THUMBNAIL_ROOT

user_subfolders: dict = {}

simple_mode: bool = False
async_mode: bool = False
quiet: bool = False
smart_cover_mode: bool = True
thumbnail_format: str = "jpg"
no_cover_mode: bool = False
force_crop: bool = False
group_mode: bool = False
force_grouping_on_share: bool = False
lyrics_mode: bool = False
romaji_mode: bool = False
zip_mode: bool = False
create_m3u: bool = False
skip_existing_files: bool = True
max_video_resolution: str = "720p"
audio_quality: str = "m4a"
video_container: str = "mp4"
video_codec: str = "default"

header_style: str = "default"
progress_style: str = "minimal"

media_scanner_enabled: bool = False
download_delay: float = 2.0
max_retries: int = 3
retry_delay: int = 2
async_workers: int = 3
daemon_default_temp: bool = True
daemon_cleanup_interval: int = 3600

verified_dependencies: bool = False

language: str = "en"


@trace
def load_config():
    """Load application configuration from ``config.json`` into module-level state.

    Reads the JSON file at :data:`~tetodl.constants.CONFIG_PATH` and updates
    every module-level variable with the corresponding key from the file.
    If the file does not exist, module defaults are kept and the system
    language is detected.

    Parameters
    ----------
    None

    Returns
    -------
    None

    Raises
    ------
    None
        Exceptions during file I/O or JSON decoding are silently caught;
        the system language is used as a fallback.

    Example
    -------
    >>> from tetodl.core.config import load_config, music_root
    >>> load_config()
    >>> print(music_root)
    /home/user/Downloads/TetoDL/music

    See Also
    --------
    :func:`save_config` : Persist current module state back to disk.
    :func:`initialize_config` : One-shot setup that calls ``load_config``.
    :func:`reset_to_defaults` : Restore default paths.
    """
    global music_root, video_root, user_subfolders, simple_mode
    global max_video_resolution, video_container, video_codec, audio_quality
    global progress_style, header_style, skip_existing_files
    global verified_dependencies, smart_cover_mode, download_delay, max_retries
    global media_scanner_enabled, daemon_default_temp
    global daemon_cleanup_interval, language

    if not os.path.exists(CONFIG_PATH):
        with traced('no config.json, using defaults'):
            sys_lang = detect_system_language()
            language = sys_lang
            set_language(sys_lang)
            return

    try:
        with open(CONFIG_PATH, "r") as f:
            data = json.load(f)

        music_root = data.get("music_root", music_root)
        video_root = data.get("video_root", video_root)
        user_subfolders = data.get("user_subfolders", user_subfolders)
        simple_mode = data.get("simple_mode", simple_mode)
        max_video_resolution = data.get("max_video_resolution", max_video_resolution)
        video_container = data.get("video_container", video_container)
        video_codec = data.get("video_codec", "default")
        audio_quality = data.get("audio_quality", audio_quality)
        progress_style = data.get("progress_style", "minimal")
        header_style = data.get("header_style", "default")
        skip_existing_files = data.get("skip_existing_files", skip_existing_files)
        verified_dependencies = data.get("verified_dependencies", verified_dependencies)
        smart_cover_mode = data.get("smart_cover_mode", smart_cover_mode)
        download_delay = data.get("download_delay", 2.0)
        max_retries = data.get("max_retries", 3)
        media_scanner_enabled = data.get("media_scanner_enabled", False)
        daemon_default_temp = data.get("daemon_default_temp", True)
        daemon_cleanup_interval = data.get("daemon_cleanup_interval", 3600)

        saved_lang = data.get("language")
        if saved_lang:
            language = saved_lang
        else:
            language = detect_system_language()

        set_language(language)
    except Exception:
        sys_lang = detect_system_language()
        language = sys_lang
        set_language(sys_lang)


def load_app_config() -> AppConfig:
    """Snapshot the current module-level configuration into an :class:`AppConfig` instance.

    Reads every module-level variable and packs them into a frozen
    :class:`~tetodl.core.models.AppConfig` that can be passed through
    the pipeline without risk of accidental mutation.

    Parameters
    ----------
    None

    Returns
    -------
    AppConfig
        A Pydantic model containing the full current configuration state.

    Example
    -------
    >>> from tetodl.core.config import load_app_config
    >>> cfg = load_app_config()
    >>> cfg.music_root
    '/home/user/Downloads/TetoDL/music'
    >>> cfg.simple_mode
    False

    See Also
    --------
    :class:`tetodl.core.models.AppConfig` : The returned model type.
    :class:`tetodl.core.resolver.ConfigResolver` : Merges ``AppConfig``
        with per-request overrides.
    """
    result = AppConfig(
        music_root=music_root,
        video_root=video_root,
        thumbnail_root=thumbnail_root,
        simple_mode=simple_mode,
        async_mode=async_mode,
        quiet=quiet,
        smart_cover_mode=smart_cover_mode,
        no_cover_mode=no_cover_mode,
        force_crop=force_crop,
        thumbnail_format=thumbnail_format,
        group_mode=group_mode,
        lyrics_mode=lyrics_mode,
        romaji_mode=romaji_mode,
        zip_mode=zip_mode,
        create_m3u=create_m3u,
        skip_existing_files=skip_existing_files,
        max_video_resolution=max_video_resolution,
        audio_quality=audio_quality,
        video_container=video_container,
        video_codec=video_codec,
        header_style=header_style,
        progress_style=progress_style,
        language=language,
        media_scanner_enabled=media_scanner_enabled,
        download_delay=download_delay,
        max_retries=max_retries,
        retry_delay=retry_delay,
        async_workers=async_workers,
        daemon_default_temp=daemon_default_temp,
        daemon_cleanup_interval=daemon_cleanup_interval,
        verified_dependencies=verified_dependencies,
    )

    return result


def save_config():
    """Persist the current module-level configuration to ``config.json``.

    Writes a JSON object to :data:`~tetodl.constants.CONFIG_PATH` containing
    all user-configurable settings.  Called automatically by every setter
    function in this module.

    Raises
    ------
    None
        I/O or encoding errors are silently caught and reported via the
        console logger.

    Example
    -------
    >>> from tetodl.core.config import save_config, simple_mode
    >>> simple_mode = True
    >>> save_config()

    See Also
    --------
    :func:`load_config` : Inverse operation — read the file back into state.
    """
    data = {
        "music_root": music_root,
        "video_root": video_root,
        "user_subfolders": user_subfolders,
        "simple_mode": simple_mode,
        "max_video_resolution": max_video_resolution,
        "audio_quality": audio_quality,
        "video_container": video_container,
        "video_codec": video_codec,
        "progress_style": progress_style,
        "header_style": header_style,
        "skip_existing_files": skip_existing_files,
        "download_delay": download_delay,
        "max_retries": max_retries,
        "media_scanner_enabled": media_scanner_enabled,
        "smart_cover_mode": smart_cover_mode,
        "verified_dependencies": verified_dependencies,
        "language": language,
        "daemon_default_temp": daemon_default_temp,
        "daemon_cleanup_interval": daemon_cleanup_interval,
    }

    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        console.err(Keys.core.failed_save_config)


def cleanup_ghost_subfolders():
    """Remove subfolder entries from the config whose directories no longer exist.

    Iterates over every tracked subfolder and deletes entries pointing to
    directories that have been removed from the filesystem.  If any entries
    are cleaned, the config is automatically saved.

    Parameters
    ----------
    None

    Returns
    -------
    None

    Example
    -------
    >>> from tetodl.core.config import cleanup_ghost_subfolders
    >>> cleanup_ghost_subfolders()

    See Also
    --------
    :func:`add_user_subfolder` : Add a subfolder to the tracking list.
    :func:`initialize_config` : Calls ``cleanup_ghost_subfolders`` on startup.
    """
    global user_subfolders
    cleaned = False
    
    current_roots = list(user_subfolders.keys())

    for root_path in current_roots:
        # Clear Config Legacy
        if root_path in ["music", "video"]:
            if not os.path.exists(root_path):
                del user_subfolders[root_path]
                cleaned = True
            continue

        if not os.path.exists(root_path):
            continue

        current_subs = user_subfolders[root_path]
        valid_subs = []
        is_modified = False

        for sub in current_subs:
            full_path = os.path.join(root_path, sub)
            if os.path.exists(full_path):
                valid_subs.append(sub)
            else:
                is_modified = True
                cleaned = True

        if is_modified:
            user_subfolders[root_path] = valid_subs
            
            if not valid_subs:
                del user_subfolders[root_path]
                cleaned = True

    if cleaned:
        save_config()


def initialize_config():
    """One-shot configuration initialisation: load, create directories, clean up.

    Performs the complete startup sequence:
    1. Loads settings from disk via :func:`load_config`.
    2. Creates the music and video root directories if they do not exist.
    3. Removes any ``.nomedia`` files from those roots.
    4. Cleans up ghost (stale) subfolder entries via :func:`cleanup_ghost_subfolders`.

    Parameters
    ----------
    None

    Returns
    -------
    None

    Example
    -------
    >>> from tetodl.core.config import initialize_config
    >>> initialize_config()

    See Also
    --------
    :func:`load_config` : Underlying config loader.
    :func:`cleanup_ghost_subfolders` : Stale-subfolder removal logic.
    :func:`reset_to_defaults` : Reinitialise with factory defaults.
    """
    from ..utils.files import remove_nomedia_file
    load_config()

    # Create root directories
    os.makedirs(music_root, exist_ok=True)
    os.makedirs(video_root, exist_ok=True)

    # Ensure root folders don't have .nomedia
    remove_nomedia_file(music_root)
    remove_nomedia_file(video_root)

    # Cleanup ghost subfolders
    cleanup_ghost_subfolders()


def reset_to_defaults():
    """Restore music and video root directories to their defaults.

    Resets :data:`music_root` and :data:`video_root` to the constants
    defined in :mod:`tetodl.constants`, creates the directories if they
    are missing, removes any ``.nomedia`` files, and persists the change.

    Parameters
    ----------
    None

    Returns
    -------
    None

    Example
    -------
    >>> from tetodl.core.config import reset_to_defaults
    >>> reset_to_defaults()

    See Also
    --------
    :func:`save_config` : Persists the reset values.
    :func:`initialize_config` : Full startup initialisation.
    """
    global music_root, video_root
    from ..utils.files import remove_nomedia_file

    music_root = DEFAULT_MUSIC_ROOT
    video_root = DEFAULT_VIDEO_ROOT

    os.makedirs(music_root, exist_ok=True)
    os.makedirs(video_root, exist_ok=True)

    remove_nomedia_file(music_root)
    remove_nomedia_file(video_root)

    save_config()


def toggle_simple_mode(enabled: bool):
    """Enable or disable simple (minimal-prompt) mode.

    Parameters
    ----------
    enabled : bool
        ``True`` to enable simple mode, ``False`` to disable it.

    Returns
    -------
    None

    Example
    -------
    >>> from tetodl.core.config import toggle_simple_mode
    >>> toggle_simple_mode(True)

    See Also
    --------
    :data:`simple_mode` : Module-level state variable.
    :func:`load_config` : Reads the persisted value on next launch.
    """
    global simple_mode
    simple_mode = enabled
    save_config()

def toggle_smart_cover(enabled: bool):
    """Enable or disable smart cover-art selection.

    When enabled, the most-square thumbnail is automatically chosen;
    when disabled, the first available thumbnail is used.

    Parameters
    ----------
    enabled : bool
        ``True`` to enable smart cover selection, ``False`` to disable it.

    Returns
    -------
    None

    Example
    -------
    >>> from tetodl.core.config import toggle_smart_cover
    >>> toggle_smart_cover(True)

    See Also
    --------
    :data:`smart_cover_mode` : Module-level state variable.
    :func:`toggle_smart_cover` is also used by the daemon API.
    """
    global smart_cover_mode
    smart_cover_mode = enabled
    save_config()

def toggle_skip_existing(enabled: bool):
    """Enable or disable skipping of already-downloaded files.

    When enabled, files that already exist in the target directory are
    skipped during download.

    Parameters
    ----------
    enabled : bool
        ``True`` to skip existing files, ``False`` to overwrite them.

    Returns
    -------
    None

    Example
    -------
    >>> from tetodl.core.config import toggle_skip_existing
    >>> toggle_skip_existing(False)

    See Also
    --------
    :data:`skip_existing_files` : Module-level state variable.
    :meth:`tetodl.core.registry.RegistryManager.is_cached`
    """
    global skip_existing_files
    skip_existing_files = enabled
    save_config()


def toggle_video_container(container):
    """Set the video container format (e.g. ``mp4`` or ``mkv``).

    Parameters
    ----------
    container : str
        Target container format. Must be one of
        :data:`~tetodl.constants.VALID_CONTAINERS`.

    Returns
    -------
    bool
        ``True`` if the container was valid and the config was saved,
        ``False`` otherwise.

    Example
    -------
    >>> from tetodl.core.config import toggle_video_container
    >>> toggle_video_container("mkv")
    True
    >>> toggle_video_container("avi")
    False

    See Also
    --------
    :data:`~tetodl.constants.VALID_CONTAINERS` : Allowed container values.
    :data:`video_container` : Module-level state variable.
    """
    global video_container
    if container in VALID_CONTAINERS:
        video_container = container
        save_config()
        return True
    return False

def set_video_resolution(resolution):
    """Set the maximum video resolution for downloads.

    Parameters
    ----------
    resolution : str
        Target resolution string (e.g. ``"1080p"``, ``"720p"``,
        ``"480p"``). Must be one of
        :data:`~tetodl.constants.VALID_RESOLUTIONS`.

    Returns
    -------
    bool
        ``True`` if the resolution was valid and the config was saved,
        ``False`` otherwise.

    Example
    -------
    >>> from tetodl.core.config import set_video_resolution
    >>> set_video_resolution("1080p")
    True
    >>> set_video_resolution("4k")
    False

    See Also
    --------
    :data:`~tetodl.constants.VALID_RESOLUTIONS` : Allowed resolution values.
    :func:`get_video_format_string` : Produces the yt-dlp format string
        from the current resolution setting.
    """
    global max_video_resolution
    if resolution in VALID_RESOLUTIONS:
        max_video_resolution = resolution
        save_config()
        return True
    return False

def set_video_codec(codec):
    """Set the preferred video codec for downloads.

    Parameters
    ----------
    codec : str
        Target codec identifier (e.g. ``"h264"``, ``"h265"``,
        ``"default"``). Must be one of
        :data:`~tetodl.constants.VALID_CODECS`.

    Returns
    -------
    bool
        ``True`` if the codec was valid and the config was saved,
        ``False`` otherwise.

    Example
    -------
    >>> from tetodl.core.config import set_video_codec
    >>> set_video_codec("h265")
    True

    See Also
    --------
    :data:`~tetodl.constants.VALID_CODECS` : Allowed codec values.
    :data:`video_codec` : Module-level state variable.
    """
    global video_codec
    if codec in VALID_CODECS:
        video_codec = codec
        save_config()
        return True
    return False

def toggle_audio_quality(new_quality):
    """Set the preferred audio quality preset.

    Parameters
    ----------
    new_quality : str
        Quality preset key (e.g. ``"m4a"``, ``"mp3"``, ``"opus"``).
        Must be a key of :data:`~tetodl.constants.AUDIO_QUALITY_OPTIONS`.

    Returns
    -------
    str
        The active quality key — either *new_quality* if it was accepted,
        or the current value if it was rejected.

    Example
    -------
    >>> from tetodl.core.config import toggle_audio_quality
    >>> toggle_audio_quality("opus")
    'opus'
    >>> toggle_audio_quality("wav")   # invalid — returns current value
    'opus'

    See Also
    --------
    :data:`~tetodl.constants.AUDIO_QUALITY_OPTIONS` : Quality preset map.
    :func:`get_audio_quality_info` : Returns the full info dict for the
        current quality preset.
    """
    global audio_quality
    from ..constants import AUDIO_QUALITY_OPTIONS

    if new_quality in AUDIO_QUALITY_OPTIONS:
        audio_quality = new_quality
        save_config()
        return new_quality
    return audio_quality

def set_progress_style(style_name):
    """Set the progress-bar visual style.

    Parameters
    ----------
    style_name : str
        One of ``"minimal"``, ``"classic"``, or ``"modern"``.

    Returns
    -------
    str
        The active style name — either *style_name* if it was accepted,
        or the current value if it was rejected.

    Example
    -------
    >>> from tetodl.core.config import set_progress_style
    >>> set_progress_style("modern")
    'modern'

    See Also
    --------
    :data:`progress_style` : Module-level state variable.
    :func:`tetodl.utils.hooks.get_progress_hook` : Consumes this value.
    """
    global progress_style
    valid_styles = ["minimal", "classic", "modern"]
    if style_name in valid_styles:
        progress_style = style_name
        save_config()
        return style_name
    return progress_style

def set_header_style(style_name):
    """Set the header display style for console output.

    Parameters
    ----------
    style_name : str
        Style identifier (e.g. ``"default"`` or ``"classic"``).

    Returns
    -------
    bool
        Always ``True``.

    Example
    -------
    >>> from tetodl.core.config import set_header_style
    >>> set_header_style("classic")
    True

    See Also
    --------
    :data:`header_style` : Module-level state variable.
    """
    global header_style
    header_style = style_name
    save_config()
    return True

def set_network_config(delay=None, retries=None):
    global download_delay, max_retries
    if delay is not None:
        download_delay = float(delay)
    if retries is not None:
        max_retries = int(retries)
    save_config()
    return True

def set_media_scanner(enable: bool):
    """Enable or disable the background media scanner.

    When enabled, the daemon periodically scans the configured library
    directories for new media files.

    Parameters
    ----------
    enable : bool
        ``True`` to enable the media scanner, ``False`` to disable it.

    Returns
    -------
    bool
        Always ``True``.

    Example
    -------
    >>> from tetodl.core.config import set_media_scanner
    >>> set_media_scanner(True)
    True

    See Also
    --------
    :data:`media_scanner_enabled` : Module-level state variable.
    :mod:`tetodl.utils.media_scanner` : Scanner implementation.
    """
    save_config()
    return True
    
def get_audio_quality_info():
    """Return detailed information about the currently selected audio quality.

    Looks up the active :data:`audio_quality` key in the
    :data:`~tetodl.constants.AUDIO_QUALITY_OPTIONS` map and returns the
    corresponding metadata dict (extension, bitrate, codec name).

    Parameters
    ----------
    None

    Returns
    -------
    dict
        Quality info dict with keys ``"ext"``, ``"bitrate"``, and ``"codec"``.
        Falls back to the ``"m4a"`` entry if the current key is missing.

    Example
    -------
    >>> from tetodl.core.config import get_audio_quality_info
    >>> info = get_audio_quality_info()
    >>> info["ext"]
    'm4a'

    See Also
    --------
    :data:`~tetodl.constants.AUDIO_QUALITY_OPTIONS` : Full preset map.
    :func:`toggle_audio_quality` : Setter for the quality key.
    """
    from ..constants import AUDIO_QUALITY_OPTIONS
    return AUDIO_QUALITY_OPTIONS.get(audio_quality, AUDIO_QUALITY_OPTIONS["m4a"])

def get_video_format_string():
    """Build a yt-dlp format string that limits video height to the configured maximum.

    Produces a string like ``bestvideo[height<=720]+bestaudio/best[height<=720]``
    that tells yt-dlp to prefer separate video+audio streams while capping
    the resolution.

    Parameters
    ----------
    None

    Returns
    -------
    str
        yt-dlp ``-f`` format string.

    Example
    -------
    >>> from tetodl.core.config import get_video_format_string
    >>> get_video_format_string()
    'bestvideo[height<=720]+bestaudio/best[height<=720]'

    See Also
    --------
    :func:`get_fallback_format_string` : Single-stream fallback when the
        combined format selector fails.
    :data:`max_video_resolution` : The resolution value this function reads.
    """
    max_height = max_video_resolution.replace('p', '')
    
    return f'bestvideo[height<={max_height}]+bestaudio/best[height<={max_height}]'

def get_fallback_format_string():
    """Build a fallback yt-dlp format string limited to a single mp4 stream.

    Produces a string like ``best[height<=720][ext=mp4]`` that restricts
    yt-dlp to single-stream mp4 files at or below the configured resolution.
    Used when the primary format selector fails.

    Parameters
    ----------
    None

    Returns
    -------
    str
        yt-dlp ``-f`` format string.

    Example
    -------
    >>> from tetodl.core.config import get_fallback_format_string
    >>> get_fallback_format_string()
    'best[height<=720][ext=mp4]'

    See Also
    --------
    :func:`get_video_format_string` : Primary (multi-stream) format string.
    """
    max_height = max_video_resolution.replace('p', '')
    return f'best[height<={max_height}][ext=mp4]'


def clear_cache():
    """Delete the cache file from disk.

    Removes the file at :data:`~tetodl.constants.CACHE_PATH` if it exists.

    Parameters
    ----------
    None

    Returns
    -------
    bool
        ``True`` if the file was successfully deleted, ``False`` if it did
        not exist or if an error occurred.

    Example
    -------
    >>> from tetodl.core.config import clear_cache
    >>> clear_cache()
    True

    See Also
    --------
    :func:`tetodl.core.cache.reset_cache` : In-memory cache reset.
    :data:`~tetodl.constants.CACHE_PATH` : Cache file location.
    """
    from ..constants import CACHE_PATH
    try:
        if os.path.exists(CACHE_PATH):
            os.remove(CACHE_PATH)
            return True
    except Exception:
        pass
    return False


def clear_history():
    """Reset the download history via the history module.

    Delegates to :func:`tetodl.core.history.reset_history`.

    Parameters
    ----------
    None

    Returns
    -------
    bool
        ``True`` if the history was successfully reset, ``False`` on error.

    Example
    -------
    >>> from tetodl.core.config import clear_history
    >>> clear_history()
    True

    See Also
    --------
    :func:`tetodl.core.history.reset_history` : Underlying history reset.
    """
    from ..core.history import reset_history as _reset_history
    try:
        _reset_history()
        return True
    except Exception:
        pass
    return False

def reset_config():
    """Delete the configuration file to trigger a factory reset on next launch.

    Removes the file at :data:`~tetodl.constants.CONFIG_PATH`.

    Parameters
    ----------
    None

    Returns
    -------
    bool
        ``True`` if the file was successfully deleted, ``False`` if it did
        not exist or if an error occurred.

    Example
    -------
    >>> from tetodl.core.config import reset_config
    >>> reset_config()
    True

    See Also
    --------
    :func:`reset_to_defaults` : In-memory reset without deleting the file.
    :data:`~tetodl.constants.CONFIG_PATH` : Config file location.
    """
    try:
        if os.path.exists(CONFIG_PATH):
            os.remove(CONFIG_PATH)
            return True
    except Exception:
        pass
    return False

def wipe_registry():
    """Delete the registry database file.

    Removes the file at :data:`~tetodl.constants.REGISTRY_PATH`.  The
    registry tracks previously downloaded files to enable skip-existing
    and re-download detection.

    Parameters
    ----------
    None

    Returns
    -------
    bool
        ``True`` if the file was successfully deleted, ``False`` if it did
        not exist or if an error occurred.

    Example
    -------
    >>> from tetodl.core.config import wipe_registry
    >>> wipe_registry()
    True

    See Also
    --------
    :class:`tetodl.core.registry.RegistryManager` : Registry logic.
    :data:`~tetodl.constants.REGISTRY_PATH` : Registry file location.
    """
    try:
        if os.path.exists(REGISTRY_PATH):
            os.remove(REGISTRY_PATH)
            return True
    except Exception:
        pass
    return False

def perform_full_wipe():
    """Perform a complete wipe of all persistent application data.

    Sequentially calls :func:`clear_cache`, :func:`clear_history`,
    :func:`reset_config`, and :func:`wipe_registry`.  Returns ``True``
    only when every individual operation succeeded.

    Parameters
    ----------
    None

    Returns
    -------
    bool
        ``True`` if every sub-operation returned ``True``, ``False``
        otherwise.

    Example
    -------
    >>> from tetodl.core.config import perform_full_wipe
    >>> perform_full_wipe()
    True

    See Also
    --------
    :func:`clear_cache` : Clears the metadata cache.
    :func:`clear_history` : Resets the download history.
    :func:`reset_config` : Removes the config file.
    :func:`wipe_registry` : Removes the registry database.
    """
    c = clear_cache()
    h = clear_history()
    cfg = reset_config()
    reg = wipe_registry()
    return c and h and cfg and reg

def update_language(lang_code: str):
    """Set the application UI language and persist the choice.

    Delegates to :func:`tetodl.utils.i18n.set_language` and, on success,
    updates the module-level :data:`language` variable and saves the config.

    Parameters
    ----------
    lang_code : str
        ISO 639-1 language code (e.g. ``"en"``, ``"id"``).

    Returns
    -------
    bool
        ``True`` if the language was accepted and saved, ``False`` if
        *lang_code* is not recognised by the i18n system.

    Example
    -------
    >>> from tetodl.core.config import update_language
    >>> update_language("id")
    True

    See Also
    --------
    :func:`tetodl.utils.i18n.set_language` : Underlying language setter.
    :func:`get_language_name` : Human-readable display name for a code.
    """
    global language
    
    if set_language(lang_code):
        language = lang_code
        save_config()
        return True
    return False


def add_user_subfolder(root_path: str, folder_name: str):
    """Register a subfolder under *root_path* so it is tracked for cleanup and audit.

    The resolved absolute path of *root_path* is used as the key in the
    :data:`user_subfolders` mapping.  Duplicate folder names are silently
    ignored.  The config is persisted after every addition.

    Parameters
    ----------
    root_path : str
        Parent directory that the subfolder lives under.
    folder_name : str
        Name of the subfolder to track.

    Returns
    -------
    None

    Example
    -------
    >>> from tetodl.core.config import add_user_subfolder
    >>> add_user_subfolder("/home/user/TetoDL/music", "artist_album")

    See Also
    --------
    :func:`cleanup_ghost_subfolders` : Inverse operation — removes stale
        entries when directories are deleted.
    """
    global user_subfolders
    root_key = os.path.abspath(root_path)
    if root_key not in user_subfolders:
        user_subfolders[root_key] = []
    if folder_name not in user_subfolders[root_key]:
        user_subfolders[root_key].append(folder_name)
        save_config()


def get_language_name(lang_code: str) -> str:
    """Return the human-readable display name for an ISO 639-1 language code.

    Parameters
    ----------
    lang_code : str
        A two-letter ISO 639-1 code (e.g. ``"en"``, ``"id"``).

    Returns
    -------
    str
        Localised display name (e.g. ``"English"``, ``"Indonesia"``).
        Returns *lang_code* unchanged if the code is not recognised.

    Example
    -------
    >>> from tetodl.core.config import get_language_name
    >>> get_language_name("en")
    'English'

    See Also
    --------
    :func:`update_language` : Activate a language by code.
    :func:`tetodl.utils.i18n.get_language_display_name` : Broader lookup.
    """
    names = {
        "id": "Indonesia",
        "en": "English"
    }
    return names.get(lang_code, lang_code)