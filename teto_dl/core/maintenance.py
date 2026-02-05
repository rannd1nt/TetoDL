import sys
import subprocess
import os
import shutil
from pathlib import Path
from ..constants import DATA_DIR, CACHE_DIR, CONFIG_DIR
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