"""
Menu system for AIO Downloader
"""
import os
import sys
import time
import threading
from ..constants import RuntimeConfig

from ..utils.i18n import get_text as _
from ..utils.colors import (    
    print_process, print_info, print_success, 
    print_error, print_neutral, clear, colored_switch, color, Colors as C
)
from ..core.config import (
    initialize_config, save_config, reset_to_defaults,
    toggle_simple_mode, toggle_skip_existing, toggle_video_resolution,
    clear_cache, clear_history, get_language_name, toggle_language
)
from ..core.history import display_history, load_history
from ..core.cache import get_cache_size
from ..core.dependency import reset_verification
from ..utils.file_utils import create_nomedia_file
from ..ui.navigation import navigate_folders
from ..ui.display import (
    show_ascii, visit_instagram, visit_github, wait_and_clear_prompt
)
from ..downloaders.youtube import download_audio_youtube, download_video_youtube
from ..downloaders.spotify import download_spotify


def run_in_thread(fn, *args):
    """Run function in a separate thread"""
    t = threading.Thread(target=fn, args=args, daemon=True)
    t.start()
    return t


def menu_folder():
    """Menu for managing root download folders"""
    while True:
        clear()
        print(color("\n=== Root Download Folder Settings ===\n", "c"))

        print(color(f"1) Music root: {color(RuntimeConfig.MUSIC_ROOT, 'lgrn')}", "c"))
        print(color(f"2) Video root: {color(RuntimeConfig.VIDEO_ROOT, 'lgrn')}\n", "c"))

        print(color(f"3) {_('menu.root_folder.reset')}", "c"))
        print(color(f"4) {_('common.back')}\n", "c"))

        choice = input(_('common.choose')).strip()

        if choice == "1":
            new_dir = navigate_folders("/storage/emulated/0", _('download.navigation.title'), restrict_to_start=False)
            if new_dir:
                RuntimeConfig.MUSIC_ROOT = new_dir
                os.makedirs(RuntimeConfig.MUSIC_ROOT, exist_ok=True)
                create_nomedia_file(RuntimeConfig.MUSIC_ROOT)
                save_config()
                print_success(_('download.navigation.setted_music', music_root=color(RuntimeConfig.MUSIC_ROOT, 'lgrn')))
                time.sleep(1)

        elif choice == "2":
            new_dir = navigate_folders("/storage/emulated/0", _('download.navigation.title'), restrict_to_start=False)
            if new_dir:
                RuntimeConfig.VIDEO_ROOT = new_dir
                os.makedirs(RuntimeConfig.VIDEO_ROOT, exist_ok=True)
                create_nomedia_file(RuntimeConfig.VIDEO_ROOT)
                save_config()
                print_success(_('download.navigation.setted_video', video_root=color(RuntimeConfig.VIDEO_ROOT, 'lgrn')))
                time.sleep(1)

        elif choice == "3":
            reset_to_defaults()
            print_success("Reset ke default.")
            time.sleep(1)

        elif choice == "4":
            return

        else:
            print_error("Input tidak valid!")
            time.sleep(0.6)


def menu_settings():
    """Menu for app settings"""
    while True:
        clear()
        lang_name = get_language_name(RuntimeConfig.LANGUAGE)

        print(color(f"\n======== {_('menu.settings.title')} ========\n", "c"))

        # Simple Mode
        simple_status = colored_switch(RuntimeConfig.SIMPLE_MODE, _('common.active'), _('common.inactive'))
        print(color(f"1) {_('menu.settings.simple_mode', status=simple_status)}", "c"))
        print(f"{_('menu.settings.simple_mode_desc')}\n")
        
        # Skip Existing
        skip_status = colored_switch(RuntimeConfig.SKIP_EXISTING_FILES, _('common.active'), _('common.inactive'))
        print(color(f"2) {_('menu.settings.skip_existing', status=skip_status)}", "c"))
        print(f"{_('menu.settings.skip_existing_desc')}\n")

        # Max Resolution
        print(color(f"3) {_('menu.settings.max_resolution', resolution=color(RuntimeConfig.MAX_VIDEO_RESOLUTION, 'g'))}", "c"))
        print(f"{_('menu.settings.max_resolution_desc_1')}")
        print(f"{_('menu.settings.max_resolution_desc_2')}\n")

        # History
        print(color(f"4) {_('menu.settings.history')}", "c"))
        print(f"{_('menu.settings.history_desc')}\n")

        # Clear Cache
        print(color(f"5) {_('menu.settings.clear_cache')} {color(f'(Total Cache: {get_cache_size()})', 'g')}", "c"))
        print(f"{_('menu.settings.clear_cache_desc')}\n")

        # Clear History
        print(color(f"6) {_('menu.settings.clear_history')} {color(f'({len(RuntimeConfig.DOWNLOAD_HISTORY)} Entries)', 'lgrn')}", "c"))
        print(f"{_('menu.settings.clear_history_desc')}\n")

        # Reset Verification
        print(color(f"7) {_('menu.settings.reset_verification')}", "c"))
        print(f"{_('menu.settings.reset_verification_desc')}\n")

        # Language
        print(color(f"8) {_('menu.settings.language', lang=color(lang_name, 'g'))}", "c"))
        print(f"{_('menu.settings.language_desc')}\n")

        # Back
        print(color(f"9) {_('common.back')}", "c"))

        choice = input(_('common.choose')).strip()

        if choice == "1":
            toggle_simple_mode(not RuntimeConfig.SIMPLE_MODE)
            status = _('config.simple_mode_enabled') if RuntimeConfig.SIMPLE_MODE else _('config.simple_mode_disabled')
            print_success(status)
            time.sleep(1)

        elif choice == "2":
            toggle_skip_existing(not RuntimeConfig.SKIP_EXISTING_FILES)
            status = _('config.skip_existing_enabled') if RuntimeConfig.SKIP_EXISTING_FILES else _('config.skip_existing_disabled')
            print_success(status)
            time.sleep(1)

        elif choice == "3":
            new_resolution = toggle_video_resolution()
            print_success(_('config.resolution_changed', resolution=new_resolution))
            time.sleep(1)

        elif choice == "4":
            display_history()
            wait_and_clear_prompt()

        elif choice == "5":
            confirm = input(_('config.confirm_clear_cache')).strip().lower()
            if confirm == _('common.yes'):
                if clear_cache():
                    print_success(_('config.cache_deleted'))
                else:
                    print_info(_('config.cache_empty'))
            time.sleep(1)

        elif choice == "6":
            confirm = input(_('config.confirm_clear_history')).strip().lower()
            if confirm == _('common.yes'):
                if clear_history():
                    print_success(_('config.history_deleted'))
                else:
                    print_info(_('config.history_empty'))
            time.sleep(1)

        elif choice == "7":
            reset_verification()
            time.sleep(1)

        elif choice == "8":
            # Toggle Language
            new_lang = toggle_language()
            lang_name = get_language_name(new_lang)
            print_success(_('config.language_changed', lang=lang_name))
            time.sleep(2)

        elif choice == "9":
            return

        else:
            print_error(_('error.invalid_input'))
            time.sleep(0.6)

def menu_about():
    """About menu"""
    while True:
        clear()
        print(color(f"\n> {_('menu.about.title')} <", "c"))
        print(f"{color(_('menu.about.subtitle'), 'r')}\n")
        print(f"1) {color(_('menu.about.documentation'), 'c')}")
        print(f"2) {color(_('menu.about.github'), 'c')}")
        print(f"3) {color(_('menu.about.instagram'), 'c')}")
        print(f"4) {color(_('common.back'), 'c')}")
        
        choice = input("\nPilihan > ").strip()

        if choice == "1":
            print_info(_('error.document_unavailable'))
            time.sleep(1)
        elif choice == "2":
            visit_github()
        elif choice == "3":
            visit_instagram()
        elif choice == "4":
            break
        else:
            print_error("Input tidak valid!")
            time.sleep(0.6)

def main_menu():
    """Main menu loop"""
    
    initialize_config()
    load_history()
    
    if not RuntimeConfig.VERIFIED_DEPENDENCIES:
        from ..core.dependency import verify_dependencies
        if not verify_dependencies():
            sys.exit(1)
    
    while True:
        clear()
        show_ascii()
        print(
            color(
                f"\n{_('menu.main.title')} ", 
                "c"
            ) +
            color(f"{_('menu.main.subtitle')}", "r")
        )
        
        print(C.CYAN)
        print(f"{_('menu.main.choose')}")
        print("1) " + _('menu.main.youtube_audio'))
        print("2) " + _('menu.main.youtube_video', resolution=RuntimeConfig.MAX_VIDEO_RESOLUTION))

        if RuntimeConfig.SPOTIFY_AVAILABLE:
            print("3) " + _('menu.main.spotify'))
        else:
            print("3) " + _('menu.main.spotify_unavailable'))

        print("4) " + _('menu.main.root_folder'))
        print("5) " + _('menu.main.settings'))
        print("6) " + _('menu.main.about'))
        print("7) " + _('menu.main.exit'))

        print(C.RESET)
        choice = input(_('common.choose')).strip()

        if choice == "1":
            url = input(_('download.youtube.url_input_ytm')).strip()
            if RuntimeConfig.SIMPLE_MODE:
                print_process(_('download.youtube.simple_mode_start', type='audio'))
            t = run_in_thread(download_audio_youtube, url)
            t.join()
            wait_and_clear_prompt()

        elif choice == "2":
            url = input(_('download.youtube.url_input_ytv')).strip()
            if RuntimeConfig.SIMPLE_MODE:
                print_process(_('download.youtube.simple_mode_start', type='video'))
            t = run_in_thread(download_video_youtube, url)
            t.join()
            wait_and_clear_prompt()

        elif choice == "3":
            if RuntimeConfig.SPOTIFY_AVAILABLE:
                url = input(_('download.spotify.url_input')).strip()
                if RuntimeConfig.SIMPLE_MODE:
                    print_process(_('download.youtube.simple_mode_start', type='spotify'))
                download_spotify(url)
                wait_and_clear_prompt()
            else:
                print_error(_('download.spotify.not_available'))
                print_info(_('download.spotify.install_instruction'))
                print_info(_('download.spotify.reset_verification_hint'))
                time.sleep(3.5)

        elif choice == "4":
            menu_folder()

        elif choice == "5":
            menu_settings()

        elif choice == "6":
            menu_about()

        elif choice == "7":
            save_config()
            print_neutral(_('menu.main.exit'), "[-]")
            break

        else:
            print_error(_('error.invalid_input'))
            time.sleep(0.6)


