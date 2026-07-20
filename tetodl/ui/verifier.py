import time
import sys
import os
import subprocess
import questionary
from questionary import Style
from ..core.dependency import (
    verify_core_dependencies,
    get_ytdlp_version_info
)
from ..core.config import save_config, update_language
from ..ui.navigation import navigate_folders
from ..constants import (
    DEFAULT_MUSIC_ROOT, DEFAULT_VIDEO_ROOT,
    IS_WSL, IS_TERMUX, 
)
from ..core import config as cfg
from ..utils.display import wait_and_clear_prompt
from ..ui.components import verification_header
from ..utils.console import console
from ..utils.i18n_keys import Keys
from ..utils.formatters import (
    clear, color, menu_style
)
from ..utils.i18n import (
    set_language, detect_system_language, get_language_display_name,
)

def _verif_style():
    return Style([
                        ('question', 'fg:white'),
                        ('answer', 'fg:white'),
                        ('pointer', 'fg:cyan bold'),
                        ('highlighted', 'fg:cyan bold'),
                        ('selected', 'fg:cyan'),
                        ('separator', 'fg:grey'),
                        ('instruction', 'fg:grey'),
                    ])

def _prompt_and_update_ytdlp(current, latest):
    """
    Helper function to handle yt-dlp update logic within Verifier.
    Avoids circular import with menu.py.
    """
    print()
    console.warn(Keys.ui.dependency_update_available)
    print(f"      {color('Current:', 'y')} {current}")
    print(f"      {color('Latest :', 'g')} {latest}")
    print()
    
    should_update = False

    if not IS_TERMUX:
        should_update = questionary.confirm(
            "Do you want to update yt-dlp now?",
            qmark=' ', default=True, style=menu_style()
        ).ask()
    else:
        try:
            res = input(f"{color('Update yt-dlp now? (Y/n) > ', 'c')}").strip().lower()
            should_update = res in ['', 'y', 'yes']
        except KeyboardInterrupt:
            pass

    if should_update:
        print()
        console.warn(Keys.ui.updating_ytdlp)
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"])
            console.ok(Keys.ui.update_complete)
            time.sleep(1)
            return True
        except subprocess.CalledProcessError:
            console.err(Keys.ui.update_failed_check_connection)
            time.sleep(2)
            return False
    return False

def verify_dependencies(header_title=None):
    """Main dependency verification function"""

    set_language("en")
    verification_header(title=header_title)

    if not header_title:
        console.warn(Keys.dependency.verifying)
        console.warn(Keys.dependency.once_only)

    time.sleep(1.2)
    
    core_ok = verify_core_dependencies()
    print()
    
    if not core_ok:
        cfg.verified_dependencies = False
        save_config()
        console.err(Keys.dependency.verification_failed)
        console.warn(Keys.dependency.install_and_retry)
        input("Press enter to exit...")
        return False

    console.warn(Keys.ui.checking_core_engine)
    try:
        is_outdated, current, latest = get_ytdlp_version_info()
        
        if is_outdated:
            updated = _prompt_and_update_ytdlp(current, latest)
            if updated:
                a, new_curr, c = get_ytdlp_version_info()
                console.ok(Keys.ui.core_engine_updated_to(version=new_curr))
        else:
            if current != "unknown":
                console.ok(Keys.ui.core_engine_up_to_date(version=current))
            else:
                console.warn(Keys.ui.core_engine_installed(version=current))
                
    except Exception as e:
        console.err(Keys.ui.failed_check_engine_version(error=str(e)))

    cfg.verified_dependencies = True 
    save_config()
    
    print()

    if not header_title:
        console.proc(Keys.ui.initializing_language_setup)
        time.sleep(0.5)

        detected_code = detect_system_language()
        display_name = get_language_display_name(detected_code)

        console.warn(f"Detected System Language: {color(display_name, 'g')} | ({detected_code})")
        
        confirm_lang = False

        if not IS_TERMUX:
            confirm_lang = questionary.confirm(
                f"   Do you want to use {display_name}?",
                qmark='',
                default=True,
                style=_verif_style()
            ).ask()
        else:
            try:
                res = input(f"{color(f'Use {display_name}? (Y/n) > ', 'c')}").strip().lower()
                confirm_lang = res in ['', 'y', 'yes']
            except KeyboardInterrupt:
                confirm_lang = True

        if confirm_lang:
            set_language(detected_code)
            cfg.language = detected_code
            clear()
            verification_header()
            console.ok(Keys.ui.language_set_to(name=display_name))
            time.sleep(1)
        else:
            clear()
            verification_header()
            from ..ui.settings import prompt_language_selection
            
            selected_code = prompt_language_selection(force_selection=True)
            
            if selected_code:
                update_language(selected_code)
                final_display = get_language_display_name(selected_code)
                clear()
                verification_header()
                console.ok(Keys.ui.language_set_to(name=final_display))
                time.sleep(1)
            else:
                update_language(detected_code) 
                console.warn(Keys.ui.selection_cancelled_defaulting(name=display_name))
                time.sleep(2.3)

            clear()
        verification_header()
        
        # 2. Environment & Path Setup
        env_display = "LINUX"
        if IS_TERMUX:
            env_display = "TERMUX (Android)"
        elif IS_WSL:
            env_display = "WSL (Windows)"
        
        console.warn(f"Environment Detected: {color(env_display, 'c')}")
        print()

        proposed_music = DEFAULT_MUSIC_ROOT
        proposed_video = DEFAULT_VIDEO_ROOT
        
        # Pesan khusus untuk WSL
        if IS_WSL:
            console.warn(f"{color('WSL Detected:', 'y')} We recommend saving files to Windows folders")
            console.warn(Keys.ui.wsl_file_explorer_access)
            print()

        console.warn(Keys.ui.default_download_locations)
        print(f"    Default Music Path : {color(proposed_music, 'g')}")
        print(f"    Default Video Path : {color(proposed_video, 'g')}")
        print()

        # Tanya User
        use_default = False
        if not IS_TERMUX:
            use_default = questionary.confirm(
                "Use these default paths? (You can change this later in Settings)",
                qmark=' ', default=True, style=_verif_style()
            ).ask()
        else:
            try:
                res = input(f"{color('Use default paths? (Configurable later) (Y/n) > ', 'c')}").strip().lower()
                use_default = res in ['', 'y', 'yes']
            except KeyboardInterrupt:
                use_default = True

        if use_default:
            cfg.music_root = proposed_music
            cfg.video_root = proposed_video
            clear()
            verification_header()
            console.ok(Keys.ui.default_paths_applied)
        else:
            console.warn(Keys.ui.select_custom_music_folder)
            start_nav_music = os.path.dirname(DEFAULT_MUSIC_ROOT)
            if not os.path.exists(start_nav_music):
                start_nav_music = os.path.expanduser("~")

            custom_music = navigate_folders(start_nav_music, "Select Music Folder", False)
            if custom_music:
                cfg.music_root = custom_music
                clear()
                verification_header()
                console.ok(Keys.ui.music_path_set_to(path=custom_music))
            else:
                cfg.music_root = DEFAULT_MUSIC_ROOT
                clear()
                verification_header()
                console.warn(Keys.ui.cancelled_default_music_path)
                time.sleep(1.4)
            
            console.warn(Keys.ui.select_custom_video_folder)
            start_nav_vid = os.path.dirname(DEFAULT_VIDEO_ROOT)
            if not os.path.exists(start_nav_vid):
                start_nav_vid = os.path.expanduser("~")
            custom_video = navigate_folders(start_nav_vid, "Select Video Folder", False)
            if custom_video:
                cfg.video_root = custom_video
                clear()
                verification_header()
                console.ok(Keys.ui.video_path_set_to(path=custom_video))
            else:
                cfg.video_root = DEFAULT_VIDEO_ROOT
                clear()
                verification_header()
                console.warn(Keys.ui.cancelled_default_video_path)
                time.sleep(1.4)
    
    else:
        console.ok(Keys.ui.verification_completed)
    
    save_config()
    clear()
    verification_header()

    if not header_title:
        wait_and_clear_prompt(msg="Setup Complete! Press enter to start TetoDL...")
    else:
        wait_and_clear_prompt(msg="Press enter to continue...")
    
    return True