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
from ..utils.files import TempManager
from ..utils.console import console
from ..utils.i18n_keys import Keys
from ..utils.formatters import color

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
        console.err(Keys.maint.not_git_repo)
        console.warn(Keys.maint.manual_update_required)
        return False

    # console.warn(f"Checking for updates in {root_dir}...")
    
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
            console.ok(Keys.maint.already_up_to_date)
            return True
        else:
            console.warn(Keys.maint.found_new_commits(count=commits_behind))
            
            subprocess.check_call(["git", "pull"], cwd=root_dir, env=git_env)
            
            console.ok(Keys.maint.update_successful)
            return True

    except subprocess.CalledProcessError as e:
        console.err(Keys.maint.update_failed(error=e))
        console.warn(Keys.maint.repo_broken)
        console.warn(Keys.maint.try_reinstall)
        return False
    except FileNotFoundError:
        console.err(Keys.maint.git_not_found)
        return False

def perform_uninstall():
    """Trigger the bash uninstaller script and manage user data cleanup."""
    root_dir = get_project_root()
    script_path = root_dir / "uninstall.sh"

    if not script_path.exists():
        console.err(Keys.maint.uninstaller_script_not_found(path=script_path))
        return

    # Warning Header
    console.warn(Keys.maint.uninstall_warning)
    console.warn(Keys.maint.uninstall_details)
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
        console.neutral(Keys.maint.invalid_choice_aborting)
        return

    print()
    if wipe_mode == "full":
        console.warn(Keys.maint.alert_permanent_delete)
    
    try:
        confirm = input(f"{color('Are you sure you want to proceed? (y/N) > ', 'y')}").strip().lower()
    except KeyboardInterrupt:
        print()
        return

    if confirm != 'y':
        console.neutral(Keys.maint.uninstall_cancelled)
        return

    # --- EXECUTE CLEANUP DATA ---
    if wipe_mode != "none":
        console.warn(Keys.maint.cleaning_user_data)
        try:
            # Delete Cache
            if CACHE_DIR.exists():
                shutil.rmtree(CACHE_DIR)
                console.ok(Keys.maint.cache_dir_removed)

            # Delete Config
            if CONFIG_DIR.exists():
                shutil.rmtree(CONFIG_DIR)
                console.ok(Keys.maint.config_dir_removed)

            # Logic Data Dir (History & Registry)
            if DATA_DIR.exists():
                if wipe_mode == "full":
                    shutil.rmtree(DATA_DIR)
                    console.ok(Keys.maint.data_dir_removed)
                else:
                    # Partial: Delete history.json but kept registry.json
                    history_file = DATA_DIR / "history.json"
                    if history_file.exists():
                        os.remove(history_file)
                        console.ok(Keys.maint.history_file_removed)
                    
                    console.warn(Keys.maint.registry_kept_safe)

        except Exception as e:
            console.err(Keys.maint.failed_clean_data(error=e))

    # --- EXECUTE BASH UNINSTALLER ---
    console.warn(Keys.maint.launching_uninstaller)
    
    try:
        subprocess.run(["chmod", "+x", str(script_path)], check=False)
        sys.stdout.flush()
        subprocess.call(["bash", str(script_path)])
        sys.exit(0)
        
    except Exception as e:
        console.err(Keys.maint.error_executing_uninstaller(error=e))

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
            console.warn(Keys.maint.cache_nothing_to_clean)
        else:
            TempManager.cleanup()
            
            if os.path.exists(CACHE_PATH):
                try: os.remove(CACHE_PATH)
                except OSError: pass
            
            if os.path.exists(CACHE_DIR):
                try: shutil.rmtree(CACHE_DIR)
                except OSError: pass
                
            console.ok(Keys.maint.cache_cleared)

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
        console.warn(Keys.maint.nothing_to_clean(target=t.capitalize()))

    if not valid_targets:
        return

    if 'registry' in valid_targets:
        print()
        console.warn(f"{color('Warning:', 'y')} You are about to wipe the DOWNLOAD REGISTRY.")
        console.warn("TetoDL will lose track of ALL downloaded files.")
        
        other_valid = [t for t in valid_targets if t != 'registry']
        if other_valid:
            console.warn(Keys.maint.will_also_reset(items=', '.join([t.upper() for t in other_valid])))
        
        print()
        
        try:
            confirm = input(f"{color('Are you sure? This cannot be undone. (y/N) > ', 'y')}").strip().lower()
        except KeyboardInterrupt:
            print("\nOperation cancelled.")
            return

        if confirm not in ['y', 'yes']:
            console.warn(Keys.maint.reset_cancelled)
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
                console.ok(Keys.maint.download_history_cleared)

            if 'config' in valid_targets:
                reset_config()
                console.ok(Keys.maint.config_reset_to_defaults)

            if 'registry' in valid_targets:
                registry.reset()
                console.ok(Keys.maint.registry_nuked)
            
        except KeyboardInterrupt:
            sys.stdout.write("\r" + " " * 60 + "\r")
            print(color("\n[!] Reset ABORTED by user.", "g", True))
            return

    else:
        console.warn(Keys.maint.about_to_reset(items=', '.join([t.upper() for t in valid_targets])))
        
        try:
            confirm = input(f"{color('Are you sure? (y/N) > ', 'y')}").strip().lower()
        except KeyboardInterrupt:
            print("\nOperation cancelled.")
            return

        if confirm not in ['y', 'yes']:
            console.warn(Keys.maint.reset_cancelled)
            return

        if 'history' in valid_targets:
            reset_history()
            console.ok(Keys.maint.download_history_cleared)

        if 'config' in valid_targets:
            reset_config()
            console.ok(Keys.maint.config_reset_to_defaults)