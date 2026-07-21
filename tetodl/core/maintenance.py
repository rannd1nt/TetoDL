import time
import sys
import os
import shutil
import subprocess
import json
import urllib.request
from pathlib import Path
from ..constants import DATA_DIR, CACHE_DIR, CONFIG_DIR, HISTORY_PATH, CONFIG_PATH, REGISTRY_PATH, CACHE_PATH, TEMP_DIR, IS_BINARY
from ..core.registry import registry
from ..core.history import reset_history
from ..core.config import reset_config
from ..utils.files import TempManager
from ..utils.console import console
from ..utils.i18n_keys import Keys
from ..utils.formatters import color

def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent

def perform_update() -> bool:
    """Update the application — pip mode or binary self-destructive update."""

    if IS_BINARY:
        return _perform_binary_update()

    # ── Pip mode ──
    try:
        import subprocess
        console.proc(Keys.cli.checking_for_updates)
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "tetodl"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            console.ok(Keys.maint.update_successful)
            return True
        else:
            console.err(Keys.maint.update_failed(error=result.stderr))
            return False
    except Exception as e:
        console.err(Keys.maint.update_failed(error=e))
        return False


def _perform_binary_update() -> bool:
    """Self-destructive binary update: download → rename → spawn updater."""
    import tempfile

    repo = "rannd1nt/tetodl"
    current_exe = sys.executable

    try:
        console.proc(Keys.cli.checking_for_updates)
        url = f"https://api.github.com/repos/{repo}/releases/latest"
        with urllib.request.urlopen(url, timeout=10) as resp:
            release = json.loads(resp.read())

        tag = release["tag_name"]
        asset_name = _binary_asset_name()
        asset_url = None
        for a in release["assets"]:
            if a["name"] == asset_name:
                asset_url = a["browser_download_url"]
                break

        if not asset_url:
            console.err(f"No binary found for {asset_name}")
            return False

        console.proc(f"Downloading {tag} ...")
        tmp_dir = Path(tempfile.mkdtemp())
        tmp_bin = tmp_dir / asset_name

        urllib.request.urlretrieve(asset_url, tmp_bin)
        os.chmod(tmp_bin, 0o755)

        console.ok(Keys.maint.update_successful)
        _spawn_updater(current_exe, str(tmp_bin))
        return True

    except Exception as e:
        console.err(Keys.maint.update_failed(error=e))
        return False


def _binary_asset_name() -> str:
    import platform
    system = platform.system().lower()
    if system == "windows":
        return "tetodl.exe"
    return "tetodl-linux"


def _spawn_updater(old_exe: str, new_exe: str) -> None:
    """Replace old binary with new binary using platform-appropriate script."""
    import platform

    if platform.system() == "Windows":
        bat_path = Path(old_exe).with_suffix(".update.bat")
        bat_content = f"""@echo off
timeout /t 1 /nobreak >nul
move /y "{new_exe}" "{old_exe}" >nul
start "" "{old_exe}" --version
del "%~f0"
"""
        bat_path.write_text(bat_content)
        subprocess.Popen(["cmd.exe", "/c", str(bat_path)],
                         shell=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    else:
        updater_script = f"""#!/bin/sh
sleep 1
mv -f "{new_exe}" "{old_exe}"
chmod +x "{old_exe}"
exec "{old_exe}" --version
"""
        import tempfile
        script = Path(tempfile.mktemp(suffix=".sh"))
        script.write_text(updater_script)
        os.chmod(script, 0o755)
        subprocess.Popen([str(script)], shell=False)

    sys.exit(0)

def perform_uninstall():
    """Uninstall TetoDL — source (pip/venv) or binary (Windows/Linux)."""
    if IS_BINARY:
        _perform_binary_uninstall()
    else:
        _perform_source_uninstall()


def _confirm_uninstall() -> str:
    """Shared prompt: ask user for wipe mode. Returns 'none', 'partial', or 'full'."""
    console.warn(Keys.maint.uninstall_warning)
    console.warn(Keys.maint.uninstall_details)
    print()

    print(f"{color('Do you want to delete configuration & data files?', 'y')}")
    print(f"  {color('[1]', 'y')} No, keep everything (Safe for reinstall)")
    print(f"  {color('[2]', 'y')} Delete Config & Cache ONLY (Keep Registry/Stats)")
    print(f"  {color('[3]', 'r')} Delete EVERYTHING (Full Wipe inc. Registry)")
    print()

    try:
        choice = input(f"{color('Choice (1/2/3) > ', 'y')}").strip()
    except KeyboardInterrupt:
        print()
        return ''

    wipe_mode = "none"
    if choice == '2':
        wipe_mode = "partial"
    elif choice == '3':
        wipe_mode = "full"
    elif choice != '1':
        console.neutral(Keys.maint.invalid_choice_aborting)
        return ''

    print()
    if wipe_mode == "full":
        console.warn(Keys.maint.alert_permanent_delete)

    try:
        confirm = input(f"{color('Are you sure you want to proceed? (y/N) > ', 'y')}").strip().lower()
    except KeyboardInterrupt:
        print()
        return ''

    if confirm != 'y':
        console.neutral(Keys.maint.uninstall_cancelled)
        return ''

    return wipe_mode


def _execute_data_cleanup(wipe_mode: str) -> None:
    """Delete user data according to wipe_mode (shared by source & binary)."""
    if wipe_mode == "none":
        return

    console.warn(Keys.maint.cleaning_user_data)
    try:
        if CACHE_DIR.exists():
            shutil.rmtree(CACHE_DIR)
            console.ok(Keys.maint.cache_dir_removed)

        if CONFIG_DIR.exists():
            shutil.rmtree(CONFIG_DIR)
            console.ok(Keys.maint.config_dir_removed)

        if DATA_DIR.exists():
            if wipe_mode == "full":
                shutil.rmtree(DATA_DIR)
                console.ok(Keys.maint.data_dir_removed)
            else:
                history_file = DATA_DIR / "history.json"
                if history_file.exists():
                    os.remove(history_file)
                    console.ok(Keys.maint.history_file_removed)
                console.warn(Keys.maint.registry_kept_safe)

    except Exception as e:
        console.err(Keys.maint.failed_clean_data(error=e))


def _perform_source_uninstall():
    """Source/pip install: run uninstall.sh to remove symlink, venv, etc."""
    root_dir = get_project_root()
    script_path = root_dir / "uninstall.sh"

    if not script_path.exists():
        console.err(Keys.maint.uninstaller_script_not_found(path=script_path))
        return

    wipe_mode = _confirm_uninstall()
    if wipe_mode == '':
        return

    _execute_data_cleanup(wipe_mode)

    # --- EXECUTE BASH UNINSTALLER ---
    console.warn(Keys.maint.launching_uninstaller)
    try:
        subprocess.run(["chmod", "+x", str(script_path)], check=False)
        sys.stdout.flush()
        subprocess.call(["bash", str(script_path)])
        sys.exit(0)
    except Exception as e:
        console.err(Keys.maint.error_executing_uninstaller(error=e))


def _perform_binary_uninstall():
    """Binary mode (Windows & Linux): prompt → cleanup → self-delete executable."""
    import platform

    wipe_mode = _confirm_uninstall()
    if wipe_mode == '':
        return

    _execute_data_cleanup(wipe_mode)

    binary_path = Path(sys.executable).resolve()
    if not binary_path.exists():
        console.err(f"Binary not found at: {binary_path}")
        return

    console.warn(Keys.maint.launching_uninstaller)

    if platform.system() == "Windows":
        _spawn_binary_self_delete_windows(binary_path)
    else:
        _spawn_binary_self_delete_linux(binary_path)

    sys.exit(0)


def _spawn_binary_self_delete_windows(binary_path: Path) -> None:
    """Create a .bat helper that deletes the running .exe and itself."""
    bat_path = binary_path.with_suffix(".uninstall.bat")
    bat_content = f"""@echo off
echo Removing TetoDL...
timeout /t 1 /nobreak >nul
del /f /q "{binary_path}" >nul 2>&1
if exist "{binary_path.parent}" (
    rmdir "{binary_path.parent}" 2>nul
)
echo TetoDL has been removed.
del "%~f0"
"""
    bat_path.write_text(bat_content)
    subprocess.Popen(
        ["cmd.exe", "/c", str(bat_path)],
        shell=True,
        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
    )


def _spawn_binary_self_delete_linux(binary_path: Path) -> None:
    """Create a shell script that deletes the running binary and itself."""
    import tempfile
    script_content = f"""#!/bin/sh
sleep 1
rm -f "{binary_path}"
rmdir "{binary_path.parent}" 2>/dev/null
echo "TetoDL has been removed."
rm -f "$0"
"""
    script = Path(tempfile.mktemp(suffix=".uninstall.sh"))
    script.write_text(script_content)
    os.chmod(script, 0o755)
    subprocess.Popen([str(script)], shell=False)

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
            except OSError:
                pass

        if not has_garbage and os.path.exists(CACHE_DIR):
            try:
                for item in os.listdir(CACHE_DIR):
                    os.path.join(CACHE_DIR, item)

                    if item == "temp":
                        continue
                    if item == "cache.json":
                        continue

                    has_garbage = True
                    break
            except OSError:
                pass

        if not has_garbage:
            console.warn(Keys.maint.cache_nothing_to_clean)
        else:
            TempManager.cleanup()
            
            if os.path.exists(CACHE_PATH):
                try:
                    os.remove(CACHE_PATH)
                except OSError:
                    pass

            if os.path.exists(CACHE_DIR):
                try:
                    shutil.rmtree(CACHE_DIR)
                except OSError:
                    pass
                
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