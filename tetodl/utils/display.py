"""
Display utilities and ASCII art
"""
import sys
from pathlib import Path

from rich import box
from rich.table import Table
from rich.text import Text

from ..utils.console import console
from ..utils.files import get_free_space
from ..utils.i18n import get_text as _
from ..utils.i18n_keys import Keys
from ..utils.network import open_url
from .formatters import clear
from .formatters import console as rich_console


def _assets_dir(is_binary: bool = False) -> Path:
    """Resolve the assets directory regardless of CWD or binary bundle mode."""
    if is_binary:
        meipass = Path(getattr(sys, '_MEIPASS', sys.executable)).parent
        candidate = meipass / "assets"
        if candidate.is_dir():
            return candidate
    candidate = Path(__file__).resolve().parent.parent.parent / "assets"
    if candidate.is_dir():
        return candidate
    return Path("assets")


def show_ascii(filename=None, str_only=False, is_binary: bool = False) -> str | None:
    """Display ASCII art — built-in default or from assets/*.txt file."""
    header_raw = r'''
  ______     __        ____  __
 /_  __/__  / /_____  / __ \/ /
  / / / _ \/ __/ __ \/ / / / /
 / / /  __/ /_/ /_/ / /_/ / /___
/_/  \___/\__/\____/_____/_____/

'''
    if not filename or filename in ('classic', 'default'):
        if str_only:
            return header_raw
        text = Text(header_raw, style="bold bright_cyan")
        rich_console.print(text)
        return None

    target_file = filename
    asset_dir = _assets_dir(is_binary)
    asset_path = asset_dir / f"{target_file}.txt"

    try:
        content = asset_path.read_text(encoding="utf-8")
        if str_only:
            return content
        print(content, flush=True)
        return content

    except FileNotFoundError:
        if not str_only:
            console.err(Keys.ui.header_not_found(file=target_file))
        return show_ascii('classic', str_only, is_binary)

    except Exception as e:
        if not str_only:
            console.err(Keys.ui.unexpected_error(error=str(e)))
        return None

def show_app_info(
    version: str = "",
    config_path: str | Path | None = None,
    data_dir: str | Path | None = None,
    cache_mod=None,
    config_mod=None,
) -> None:
    """Display System & Configuration Information"""
    from ..utils.formatters import console as _console

    table = Table(
        title=f"TetoDL v{version} - System & Configuration Info",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold bright_cyan",
        expand=False
    )

    table.add_column("Parameter", style="cyan")
    table.add_column("Value / Status", style="white")

    cpath = str(config_path) if config_path else "N/A"
    dpath = str(data_dir) if data_dir else "N/A"
    cache_sz = f"[cyan]{cache_mod.get_cache_size()}[/]" if cache_mod else "N/A"
    _cfg = config_mod

    # --- SECTION 1: SYSTEM INFO ---
    table.add_row("[bold]> System Environment[/]", "")
    table.add_row("Python Version", sys.version.split()[0])
    table.add_row("Config Path", cpath)
    table.add_row("Data Path", dpath)
    table.add_row("Cache Size", cache_sz)

    # --- SECTION 2: STORAGE & PATHS ---
    table.add_section()
    table.add_row("[bold]> Storage & Paths[/]", "")
    if _cfg:
        music_space = get_free_space(_cfg.music_root)
        music_val = f"{_cfg.music_root}\n[cyan]({music_space})[/]"
        table.add_row("Music Location", music_val)

        video_space = get_free_space(_cfg.video_root)
        video_val = f"{_cfg.video_root}\n[cyan]({video_space})[/]"
        table.add_row("Video Location", video_val)
    else:
        table.add_row("Music Location", "[dim]N/A[/]")
        table.add_row("Video Location", "[dim]N/A[/]")

    # --- SECTION 3: CONFIGURATION ---
    table.add_section()
    table.add_row("[bold]> User Configuration[/]", "")

    if _cfg:
        header_val = getattr(_cfg, 'header_style', 'default')
        p_style = getattr(_cfg, 'progress_style', 'minimal')
        lang = getattr(_cfg, 'language', 'en')
        jitter_min = getattr(_cfg, 'jitter_min', 3.0)
        jitter_max = getattr(_cfg, 'jitter_max', 5.0)
        retries = getattr(_cfg, 'max_retries', 3)
        scanner = getattr(_cfg, 'media_scanner_enabled', False)

        scanner_str = "[green]Enabled[/]" if scanner else "[dim]Disabled[/]"

        table.add_row("Header Style", str(header_val))
        table.add_row("Progress Style", str(p_style))
        table.add_row("Language", str(lang).upper())
        table.add_row("Network", f"Jitter: {jitter_min}-{jitter_max}s | Retries: {retries}")
        table.add_row("Media Scanner", scanner_str)

        codec = getattr(_cfg, 'video_codec', 'default')
        res = getattr(_cfg, 'max_video_resolution', '720p')
        container = getattr(_cfg, 'video_container', 'mp4')
        table.add_row("Video Settings", f"{container.upper()} | {res} | {codec.upper()}")
    else:
        table.add_row("Header Style", "[dim]N/A[/]")

    # Render
    _console.print()
    _console.print(table)
    _console.print()

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


def wait_and_clear_prompt(msg: str | None = None):
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