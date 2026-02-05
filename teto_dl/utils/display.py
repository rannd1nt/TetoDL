"""
Display utilities and ASCII art
"""
import os
from rich.text import Text

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


def wait_and_clear_prompt():
    """Wait for user input and clear screen"""
    try:
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