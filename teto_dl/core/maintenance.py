import sys
import subprocess
import os
from pathlib import Path
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

    print_info(f"Checking for updates in {root_dir}...")
    try:
        # Fetch remote changes
        subprocess.check_call(["git", "fetch"], cwd=root_dir)
        
        # Check status (behind/ahead)
        status = subprocess.check_output(
            ["git", "status", "-uno"], cwd=root_dir
        ).decode().lower()

        if "up to date" in status:
            print_success("TetoDL is already up to date.")
            return True
        else:
            print_info("New version found! Pulling changes...")
            subprocess.check_call(["git", "pull"], cwd=root_dir)
            print_success("Update successful! Please restart TetoDL.")
            return True

    except subprocess.CalledProcessError as e:
        print_error(f"Update failed: {e}")
        return False
    except FileNotFoundError:
        print_error("Command 'git' not found. Please install git.")
        return False

def perform_uninstall():
    """Trigger the bash uninstaller script."""
    root_dir = get_project_root()
    script_path = root_dir / "uninstall.sh"

    if not script_path.exists():
        print_error(f"Uninstaller script not found at: {script_path}")
        return

    # Warning text in English
    print_info("WARNING: This will remove global shortcuts, the launcher, and the virtual environment.")
    print_info("Your source code folder and downloaded media files will NOT be deleted.")
    
    try:
        confirm = input(f"{color('Are you sure you want to uninstall TetoDL? (y/N) > ', 'y')}").strip().lower()
    except KeyboardInterrupt:
        print()
        return

    if confirm != 'y':
        print_neutral("Uninstall cancelled.")
        return

    print_info("Launching uninstaller script...")
    
    try:
        # Ensure script is executable
        subprocess.run(["chmod", "+x", str(script_path)], check=False)
        
        # Run bash script and flush output
        sys.stdout.flush()
        subprocess.call(["bash", str(script_path)])
        
        # Force exit python because the environment (venv) it runs on is likely gone/corrupted now
        sys.exit(0)
        
    except Exception as e:
        print_error(f"Error executing uninstaller: {e}")