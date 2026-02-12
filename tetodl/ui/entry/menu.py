"""
Menu: Handles TUI rendering, User Input, and Display Logic.
"""
import sys
import time
import subprocess
import questionary
from questionary import Choice

from tetodl.constants import RuntimeConfig, IS_TERMUX
from tetodl.utils.i18n import get_text as _
from tetodl.utils.styles import (
    print_info, print_error, print_success, clear, color, menu_style
)
from tetodl.core.config import get_audio_quality_info
from tetodl.ui.components import header

def get_menu_labels():
    """Generate dynamic menu labels."""
    audio_info = get_audio_quality_info()
    return {
        "yt_audio": f"- {_('menu.main.youtube_audio', format=audio_info['ext'].upper(), bitrate=audio_info['bitrate'])}",
        "yt_video": f"- {_('menu.main.youtube_video', container=RuntimeConfig.VIDEO_CONTAINER.upper(), resolution=RuntimeConfig.MAX_VIDEO_RESOLUTION)}",
        "spotify": f"- {_('menu.main.spotify')}" if RuntimeConfig.SPOTIFY_AVAILABLE else f"{_('menu.main.spotify_unavailable')}",
        "folder": f"- {_('menu.main.root_folder')}",
        "settings": f"- {_('menu.main.settings')}",
        "history": f"- {_('menu.settings.history')}",
        "about": f"- {_('menu.main.about')}",
        "exit": f"- {_('menu.main.exit')}"
    }

def show_main_menu():
    """Render main menu and return user selection."""
    clear()
    header()
    
    lbl = get_menu_labels()
    is_spotify_disabled = not RuntimeConfig.SPOTIFY_AVAILABLE

    # --- LINUX / WINDOWS / MACOS ---
    if not IS_TERMUX:
        choices = [
            Choice(title=lbl["yt_audio"], value="1"),
            Choice(title=lbl["yt_video"], value="2"),
            Choice(title=lbl["spotify"], value="3", disabled=is_spotify_disabled),
            Choice(title=lbl["folder"], value="4"),
            Choice(title=lbl["settings"], value="5"),
            Choice(title=lbl["history"], value="6"),
            Choice(title=lbl["about"], value="7"),
            Choice(title=lbl["exit"], value="8"),
        ]
        
        selection = questionary.select(
            _('menu.main.choose'), choices=choices, style=menu_style(),
            qmark='', pointer=">", use_indicator=False, 
            show_description=False, instruction=' '
        ).ask()
        
        return selection

    # --- TERMUX (Simple Input) ---
    else:
        print(color(f"{_('menu.main.choose')}", "c"))
        for key in ["yt_audio", "yt_video", "spotify", "folder", "settings", "history", "about", "exit"]:
            print(lbl[key])
        print()

        try:
            return input(f"{color('Pilihan > ', 'c')}").strip()
        except KeyboardInterrupt:
            return None

def handle_update_prompt(update_status):
    """Handle UI for update availability."""
    current, latest = update_status
    
    clear()
    header()
    print("  " + print_info(f"Dependency Update Available!", True))
    print(f"      {color('Current:', 'y')} {current}")
    print(f"      {color('Latest :', 'g')} {latest}")
    print()
    
    should_update = False

    if not IS_TERMUX:
        should_update = questionary.confirm(
            "Do you want to update now?",
            qmark=' ', default=True, style=menu_style()
        ).ask()
    else:
        try:
            res = input(f"{color('Update now? (Y/n) > ', 'c')}").strip().lower()
            should_update = res in ['', 'y', 'yes']
        except KeyboardInterrupt:
            pass

    if should_update:
        print()
        print_info("Updating yt-dlp...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"])
            print_success("Update complete!")
            time.sleep(1)
        except subprocess.CalledProcessError:
            print_error("Update failed. Please check your connection.")
            time.sleep(2)

def prompt_download_url(title_key):
    """Show header and ask for URL."""
    clear()
    header()
    lbl = get_menu_labels()
    print(color(f"[{lbl.get(title_key, '').replace('- ', '')}]", 'c'))
    try:
        return input("Link => ").strip()
    except KeyboardInterrupt:
        return None