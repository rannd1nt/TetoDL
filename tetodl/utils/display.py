"""
Display utilities and ASCII art
"""
import os
import sys
from rich.text import Text
from rich.table import Table
from rich import box

from ..constants import RuntimeConfig, APP_VERSION, CONFIG_PATH, DATA_DIR
from ..core import cache
from ..utils.files import get_free_space
from ..utils.network import open_url
from ..utils.styles import print_error, clear, console
from ..utils.i18n import get_text as _


def show_ascii(filename=None, str_only=False) -> str | None:
    """Display ASCII art from txt file"""
    header_raw = r'''
  ______     __        ____  __
 /_  __/__  / /_____  / __ \/ /
  / / / _ \/ __/ __ \/ / / / /
 / / /  __/ /_/ /_/ / /_/ / /___
/_/  \___/\__/\____/_____/_____/

'''
    header_text = Text(header_raw, style="bold bright_cyan")

    if not filename or filename == 'classic':
        if str_only:
            return header_raw
        text = Text(header_raw, style="bold bright_cyan")
        console.print(text)
        return None

    target_file = filename if filename else 'default'

    try:
        asset_path = os.path.join("assets", f"{target_file}.txt")
        with open(asset_path, "r", encoding="utf-8") as f:
            content = f.read()
            if str_only:
                return content
            print(content, flush=True)
            return content

    except FileNotFoundError:
        if target_file != 'classic':
            if not str_only:
                print_error(f"Header '{target_file}' not found. Falling back.")
                pass
            return show_ascii('classic', str_only)

    except Exception as e:
        if not str_only:
            print_error(f"Error tak terduga: {e}")
        return None

def show_app_info() -> None:
    """Display System & Configuration Information"""
    
    table = Table(
        title=f"TetoDL v{APP_VERSION} - System & Configuration Info",
        box=box.ROUNDED,
        show_header=True, 
        header_style="bold bright_cyan",
        expand=False
    )
    
    table.add_column("Parameter", style="cyan")
    table.add_column("Value / Status", style="white")

    # --- SECTION 1: SYSTEM INFO ---
    table.add_row("[bold]> System Environment[/]", "")
    table.add_row("Python Version", sys.version.split()[0])
    table.add_row("Config Path", str(CONFIG_PATH))
    table.add_row("Data Path", str(DATA_DIR))
    table.add_row("Cache Size", f"[cyan]{cache.get_cache_size()}[/]")

    # --- SECTION 2: STORAGE & PATHS ---
    table.add_section()
    table.add_row("[bold]> Storage & Paths[/]", "")
    music_space = get_free_space(RuntimeConfig.MUSIC_ROOT)
    music_val = f"{RuntimeConfig.MUSIC_ROOT}\n[cyan]({music_space})[/]" 
    table.add_row("Music Location", music_val)

    video_space = get_free_space(RuntimeConfig.VIDEO_ROOT)
    video_val = f"{RuntimeConfig.VIDEO_ROOT}\n[cyan]({video_space})[/]"
    table.add_row("Video Location", video_val)

    # --- SECTION 3: CONFIGURATION ---
    table.add_section()
    table.add_row("[bold]> User Configuration[/]", "")

    header_val = getattr(RuntimeConfig, 'HEADER_STYLE', 'default')
    p_style = getattr(RuntimeConfig, 'PROGRESS_STYLE', 'minimal')
    lang = getattr(RuntimeConfig, 'LANGUAGE', 'en')
    delay = getattr(RuntimeConfig, 'DOWNLOAD_DELAY', 2)
    retries = getattr(RuntimeConfig, 'MAX_RETRIES', 3)
    scanner = getattr(RuntimeConfig, 'MEDIA_SCANNER_ENABLED', False)

    scanner_str = "[green]Enabled[/]" if scanner else "[dim]Disabled[/]"

    table.add_row("Header Style", str(header_val))
    table.add_row("Progress Style", str(p_style))
    table.add_row("Language", str(lang).upper())
    table.add_row("Network", f"Delay: {delay}s | Retries: {retries}")
    table.add_row("Media Scanner", scanner_str)

    # Video Prefs
    codec = getattr(RuntimeConfig, 'VIDEO_CODEC', 'default')
    res = getattr(RuntimeConfig, 'MAX_VIDEO_RESOLUTION', '720p')
    container = getattr(RuntimeConfig, 'VIDEO_CONTAINER', 'mp4')

    table.add_row("Video Settings", f"{container.upper()} | {res} | {codec.upper()}")

    # Render
    console.print()
    console.print(table)
    console.print()

def visit_instagram():
    """Open Instagram profile"""
    url = "https://www.instagram.com/rannd1nt/"
    if not open_url(url):
        print_error(f"Failed to Load Content. Visit: {url}")


def visit_github():
    """Open GitHub profile"""
    url = "https://github.com/rannd1nt"
    if not open_url(url):
        print_error(f"Failed to Load Content. Visit: {url}")


def wait_and_clear_prompt(msg: str = None):
    """Wait for user input and clear screen"""
    try:
        if msg:
            input(f"\n{msg}")
        else:
            input(f"\n{_('common.press_enter')}")
    except (KeyboardInterrupt, EOFError):
        return
    clear()

def formatted_video_codec(raw_codec: str) -> str | None:
    codec_map = {
        "default": "Default",
        "h264": "H.264",
        "h265": "H.265"
    }

    return codec_map.get(raw_codec, None)