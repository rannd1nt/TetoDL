import time
import sys
import os
import shutil
import subprocess
from pathlib import Path
from ..constants import DATA_DIR, CACHE_DIR, CONFIG_DIR, HISTORY_PATH, CONFIG_PATH, REGISTRY_PATH, CACHE_PATH, TEMP_DIR
from ..core.registry import registry
from ..core.history import reset_history
from ..core.config import reset_config
from ..core.cache import reset_cache
from ..utils.files import TempManager
from ..utils.styles import print_error, print_success, print_info, print_neutral, color

def get_project_root() -> Path:
    """
    Locate project root (where main.py and uninstall.sh reside).
    Path: teto_dl/core/maintenance.py -> teto_dl/core -> teto_dl -> ROOT
    """
    return Path(__file__).resolve().parent.parent.parent

def perform_update() -> bool:
    """Execute git pull to update the application."""
    root_dir = get_project_root()
    git_dir = root_dir / ".git"

    if not git_dir.exists():
        print_error("Not a Git repository.")
        print_info("Manual update required (please re-download the source code).")
        return False

    # print_info(f"Checking for updates in {root_dir}...")
    
    git_env = os.environ.copy()
    git_env["LC_ALL"] = "C"

    try:
        subprocess.check_call(["git", "fetch"], cwd=root_dir, env=git_env)
        
        commits_behind = subprocess.check_output(
            ["git", "rev-list", "HEAD..origin/main", "--count"], 
            cwd=root_dir, 
            env=git_env
        ).decode().strip()

        if commits_behind == "0":
            print_success("TetoDL is already up to date.")
            return True
        else:
            print_info(f"Found {commits_behind} new commit(s)! Updating...")
            
            subprocess.check_call(["git", "pull"], cwd=root_dir, env=git_env)
            
            print_success("Update successful! Please restart TetoDL.")
            return True

    except subprocess.CalledProcessError as e:
        print_error(f"Update failed: {e}")
        print_info("Your repository might be broken or incompatible.")
        print_info("Try reinstalling TetoDL using the installer.")
        return False
    except FileNotFoundError:
        print_error("Command 'git' not found. Please install git.")
        return False

def perform_uninstall():
    """Trigger the bash uninstaller script and manage user data cleanup."""
    root_dir = get_project_root()
    script_path = root_dir / "uninstall.sh"

    if not script_path.exists():
        print_error(f"Uninstaller script not found at: {script_path}")
        return

    # Warning Header
    print_info("WARNING: You are about to uninstall TetoDL.")
    print_info("This will remove global shortcuts, the launcher, and the virtual environment.")
    print()

    # Opsi Cleanup Data User
    print(f"{color('Do you want to delete configuration & data files?', 'y')}")
    print(f"  {color('[1]', 'y')} No, keep everything (Safe for reinstall)")
    print(f"  {color('[2]', 'y')} Delete Config & Cache ONLY (Keep Registry/Stats)")
    print(f"  {color('[3]', 'r')} Delete EVERYTHING (Full Wipe inc. Registry)")
    print()

    try:
        choice = input(f"{color('Choice (1/2/3) > ', 'y')}").strip()
    except KeyboardInterrupt:
        print()
        return

    wipe_mode = "none"
    if choice == '2': wipe_mode = "partial"
    elif choice == '3': wipe_mode = "full"
    elif choice != '1':
        print_neutral("Invalid choice. Aborting uninstall.", "[-]")
        return

    print()
    if wipe_mode == "full":
        print_info("ALERT: This will permanently delete EVERYTHING. Including your download statistics (Registry) !!")
    
    try:
        confirm = input(f"{color('Are you sure you want to proceed? (y/N) > ', 'y')}").strip().lower()
    except KeyboardInterrupt:
        print()
        return

    if confirm != 'y':
        print_neutral("Uninstall cancelled.", "[-]")
        return

    # --- EXECUTE CLEANUP DATA ---
    if wipe_mode != "none":
        print_info("Cleaning up user data...")
        try:
            # Delete Cache
            if CACHE_DIR.exists():
                shutil.rmtree(CACHE_DIR)
                print_success("Cache directory removed")

            # Delete Config
            if CONFIG_DIR.exists():
                shutil.rmtree(CONFIG_DIR)
                print_success("Config directory removed")

            # Logic Data Dir (History & Registry)
            if DATA_DIR.exists():
                if wipe_mode == "full":
                    shutil.rmtree(DATA_DIR)
                    print_success("Data directory (History & Registry) removed")
                else:
                    # Partial: Delete history.json but kept registry.json
                    history_file = DATA_DIR / "history.json"
                    if history_file.exists():
                        os.remove(history_file)
                        print_success("History file removed")
                    
                    print_info("Registry/Stats file kept safe.")

        except Exception as e:
            print_error(f"Failed to clean some data: {e}")

    # --- EXECUTE BASH UNINSTALLER ---
    print_info("Launching system uninstaller script...")
    
    try:
        subprocess.run(["chmod", "+x", str(script_path)], check=False)
        sys.stdout.flush()
        subprocess.call(["bash", str(script_path)])
        sys.exit(0)
        
    except Exception as e:
        print_error(f"Error executing uninstaller: {e}")

def reset_data(targets: list[str]):
    """
    Reset application data based on targets list with smart feedback.
    """
    # 1. Expand 'all' shortcut
    if 'all' in targets:
        targets = ['history', 'cache', 'config', 'registry']

    # 2. Handle CACHE first
    if 'cache' in targets:
        has_garbage = False
        
        if os.path.exists(CACHE_PATH):
            has_garbage = True
            
        if not has_garbage and os.path.exists(TEMP_DIR):
            try:
                if len(os.listdir(TEMP_DIR)) > 0:
                    has_garbage = True
            except OSError: pass

        if not has_garbage and os.path.exists(CACHE_DIR):
            try:
                for item in os.listdir(CACHE_DIR):
                    item_path = os.path.join(CACHE_DIR, item)

                    if item == "temp": continue
                    if item == "cache.json": continue

                    has_garbage = True
                    break
            except OSError: pass

        if not has_garbage:
            print_info("Cache: Nothing to clean")
        else:
            TempManager.cleanup()
            
            if os.path.exists(CACHE_PATH):
                try: os.remove(CACHE_PATH)
                except OSError: pass
            
            if os.path.exists(CACHE_DIR):
                try: shutil.rmtree(CACHE_DIR)
                except OSError: pass
                
            print_success("Cache cleared.")

        if len(targets) == 1:
            return

    # 3. Identify Dangerous Targets
    danger_targets = [t for t in targets if t in ['history', 'config', 'registry']]
    if not danger_targets:
        return

    files_to_check = {
        'history': HISTORY_PATH,
        'config': CONFIG_PATH,
        'registry': REGISTRY_PATH
    }
    
    valid_targets = []
    nothing_to_clean = []
    
    for t in danger_targets:
        path = files_to_check.get(t)
        if path and os.path.exists(path):
            valid_targets.append(t)
        else:
            nothing_to_clean.append(t)

    for t in nothing_to_clean:
        print_info(f"{t.capitalize()}: Nothing to clean")

    if not valid_targets:
        return

    if 'registry' in valid_targets:
        print()
        print_info(f"{color('Warning:', 'y')} You are about to wipe the DOWNLOAD REGISTRY.")
        print_info("TetoDL will lose track of ALL downloaded files.")
        
        other_valid = [t for t in valid_targets if t != 'registry']
        if other_valid:
            print_info(f"This will also reset: {', '.join([t.upper() for t in other_valid])}")
        
        print()
        
        try:
            confirm = input(f"{color('Are you sure? This cannot be undone. (y/N) > ', 'y')}").strip().lower()
        except KeyboardInterrupt:
            print("\nOperation cancelled.")
            return

        if confirm not in ['y', 'yes']:
            print_info("Reset cancelled.")
            return

        try:
            for i in range(5, 0, -1):
                msg = f"[!] Nuking Data In {color(str(i), 'r')}... (Press Ctrl+C to CANCEL)"
                sys.stdout.write(f"\r{color(msg, 'y')}")
                sys.stdout.flush()
                time.sleep(1)
            
            sys.stdout.write("\r" + " " * 60 + "\r")
            
            if 'history' in valid_targets:
                reset_history()
                print_success("Download history cleared.")

            if 'config' in valid_targets:
                reset_config()
                print_success("Configuration reset to defaults.")

            if 'registry' in valid_targets:
                registry.reset()
                print_success("Registry database has been nuked.")
            
        except KeyboardInterrupt:
            sys.stdout.write("\r" + " " * 60 + "\r")
            print(color("\n[!] Reset ABORTED by user.", "g", True))
            return

    else:
        print_info(f"You are about to reset: {', '.join([t.upper() for t in valid_targets])}")
        
        try:
            confirm = input(f"{color('Are you sure? (y/N) > ', 'y')}").strip().lower()
        except KeyboardInterrupt:
            print("\nOperation cancelled.")
            return

        if confirm not in ['y', 'yes']:
            print_info("Reset cancelled.")
            return

        if 'history' in valid_targets:
            reset_history()
            print_success("Download history cleared.")

        if 'config' in valid_targets:
            reset_config()
            print_success("Configuration reset to defaults.")