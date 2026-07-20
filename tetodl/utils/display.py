"""
Display utilities and ASCII art
"""
import os
import sys
from rich.text import Text
from rich.table import Table
from rich import box

from ..constants import APP_VERSION, CONFIG_PATH, DATA_DIR
from ..core import config as cfg
from ..core import cache
from ..utils.files import get_free_space
from ..utils.network import open_url
from .formatters import clear, console as rich_console
from ..utils.console import console
from ..utils.i18n import get_text as _
from ..utils.i18n_keys import Keys


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
        rich_console.print(text)
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
                console.err(Keys.ui.header_not_found(file=target_file))
                pass
            return show_ascii('classic', str_only)

    except Exception as e:
        if not str_only:
            console.err(Keys.ui.unexpected_error(error=e))
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
    music_space = get_free_space(cfg.music_root)
    music_val = f"{cfg.music_root}\n[cyan]({music_space})[/]" 
    table.add_row("Music Location", music_val)

    video_space = get_free_space(cfg.video_root)
    video_val = f"{cfg.video_root}\n[cyan]({video_space})[/]"
    table.add_row("Video Location", video_val)

    # --- SECTION 3: CONFIGURATION ---
    table.add_section()
    table.add_row("[bold]> User Configuration[/]", "")

    header_val = getattr(cfg, 'header_style', 'default')
    p_style = getattr(cfg, 'progress_style', 'minimal')
    lang = getattr(cfg, 'language', 'en')
    delay = getattr(cfg, 'download_delay', 2)
    retries = getattr(cfg, 'max_retries', 3)
    scanner = getattr(cfg, 'media_scanner_enabled', False)

    scanner_str = "[green]Enabled[/]" if scanner else "[dim]Disabled[/]"

    table.add_row("Header Style", str(header_val))
    table.add_row("Progress Style", str(p_style))
    table.add_row("Language", str(lang).upper())
    table.add_row("Network", f"Delay: {delay}s | Retries: {retries}")
    table.add_row("Media Scanner", scanner_str)

    # Video Prefs
    codec = getattr(cfg, 'video_codec', 'default')
    res = getattr(cfg, 'max_video_resolution', '720p')
    container = getattr(cfg, 'video_container', 'mp4')

    table.add_row("Video Settings", f"{container.upper()} | {res} | {codec.upper()}")

    # Render
    rich_console.print()
    rich_console.print(table)
    rich_console.print()

def visit_instagram():
    """Open Instagram profile"""
    url = "https://www.instagram.com/rannd1nt/"
    if not open_url(url):
        console.err(Keys.ui.failed_load_content(url=url))


def visit_github():
    """Open GitHub profile"""
    url = "https://github.com/rannd1nt"
    if not open_url(url):
        console.err(Keys.ui.failed_load_content(url=url))


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