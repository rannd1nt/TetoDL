import time
import sys
import subprocess
import questionary
from questionary import Style
from ..core.dependency import (
    verify_core_dependencies, verify_spotify_dependency, verify_platform_compatibility,
    get_ytdlp_version_info
)
from ..core.config import save_config, update_language
from ..constants import RuntimeConfig, IS_TERMUX
from ..utils.display import wait_and_clear_prompt
from ..ui.components import verification_header
from ..utils.styles import (
    print_info, print_success, print_error, print_process,
    clear, color, menu_style
)
from ..utils.i18n import (
    set_language, detect_system_language, get_language_display_name,
    get_text as _
)

def _prompt_and_update_ytdlp(current, latest):
    """
    Helper function to handle yt-dlp update logic within Verifier.
    Avoids circular import with menu.py.
    """
    print()
    print("  " + print_info(f"Dependency Update Available!", True))
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
        print_info("Updating yt-dlp...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"])
            print_success("Update complete!")
            time.sleep(1)
            return True
        except subprocess.CalledProcessError:
            print_error("Update failed. Please check your connection.")
            time.sleep(2)
            return False
    return False

def verify_dependencies(header_title=None):
    """Main dependency verification function"""

    set_language("en")
    verification_header(title=header_title)

    is_compatible, error_msg = verify_platform_compatibility()
    if not is_compatible:
        print_error("Fatal Error: Unsupported Platform")
        print_info(error_msg or "This application does not support native Windows (CMD/PowerShell).")
        print_info("Please use WSL2 (Ubuntu/Debian) or Linux/Termux.")
        print()
        input("Press enter to exit...")
        sys.exit(1)
    
    
    if not header_title:
        print_info(_("dependency.verifying"))
        print_info(_("dependency.once_only"))

    print()
    time.sleep(1.5)
    
    core_ok = verify_core_dependencies()
    print()
    
    if not core_ok:
        RuntimeConfig.VERIFIED_DEPENDENCIES = False
        save_config()
        print_error(_("dependency.verification_failed"))
        print_info(_("dependency.install_and_retry") + "\n")
        input("Press enter to exit...")
        return False

    # ============================================================

    spotify_ok = verify_spotify_dependency()
    RuntimeConfig.SPOTIFY_AVAILABLE = spotify_ok 
    
    print()

    print_info("Checking Core Engine (yt-dlp) status...")
    try:
        is_outdated, current, latest = get_ytdlp_version_info()
        
        if is_outdated:
            updated = _prompt_and_update_ytdlp(current, latest)
            if updated:
                a, new_curr, c = get_ytdlp_version_info()
                print_success(f"Core Engine updated to: {new_curr}")
        else:
            if current != "unknown":
                print_success(f"Core Engine is up to date: {current}")
            else:
                print_info(f"Core Engine installed: {current} (Network check skipped)")
                
    except Exception as e:
        print_error(f"Failed to check engine version: {e}")

    RuntimeConfig.VERIFIED_DEPENDENCIES = True 
    save_config()
    
    # print_success(_("dependency.verification_complete"))
    
    if not spotify_ok:
        print_info(_("dependency.spotify_hidden"))
    
    print()

    if not header_title:
        print_process("Initializing Language Setup...")
        time.sleep(0.5)

        detected_code = detect_system_language()
        display_name = get_language_display_name(detected_code)

        print_info(f"Detected System Language: {color(display_name, 'g')} | ({detected_code})")
        
        confirm_lang = False

        if not IS_TERMUX:
            confirm_lang = questionary.confirm(
                f"   Do you want to use {display_name}?",
                qmark='',
                default=True,
                style=Style([
                        ('question', 'fg:white'),
                        ('answer', 'fg:white'),
                        ('pointer', 'fg:cyan bold'),
                        ('highlighted', 'fg:cyan bold'),
                        ('selected', 'fg:cyan'),
                        ('separator', 'fg:grey'),
                        ('instruction', 'fg:grey'),
                    ])
            ).ask()
        else:
            try:
                res = input(f"{color(f'Use {display_name}? (Y/n) > ', 'c')}").strip().lower()
                confirm_lang = res in ['', 'y', 'yes']
            except KeyboardInterrupt:
                confirm_lang = True

        if confirm_lang:
            set_language(detected_code)
            RuntimeConfig.LANGUAGE = detected_code
            clear()
            verification_header()
            print_success(f"Language set to: {display_name}")
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
                print_success(f"Language set to: {final_display}")
                time.sleep(1)
            else:
                update_language(detected_code) 
                print_info(f"Selection cancelled. Defaulting to use detected system language: {display_name}.")
                time.sleep(2.3)
    else:
        print_success("Verification Completed!")
        time.sleep(1)
    
    wait_and_clear_prompt(msg="Press enter to continue...")
    save_config()
    clear()
    return True