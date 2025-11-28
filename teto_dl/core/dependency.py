"""
Dependency verification system
"""
import os
import sys
import subprocess
import importlib.util
import time
from ..constants import RuntimeConfig
from ..utils.i18n import get_text as _
from ..utils.colors import (
    print_process, print_success, print_error, 
    print_info, print_neutral, Colors
)
from .config import save_config


def check_python_version():
    """Check if Python version is 3.8 or higher"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print_success(_("dependency.python_version",
                        version=f"{version.major}.{version.minor}.{version.micro}"))
        return True
    else:
        print_error(_("dependency.python_old",
                      version=f"{version.major}.{version.minor}"))
        return False


def check_command_exists(command):
    """Check if a command exists in PATH"""
    try:
        result = subprocess.run(
            ['which', command],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


def check_ffmpeg():
    """Check if FFmpeg is installed"""
    if check_command_exists('ffmpeg'):
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                version = version_line.split()[2] if len(version_line.split()) > 2 else "unknown"
                print_success(_("dependency.ffmpeg_version", version=version))
                return True
        except Exception:
            pass
    
    print_error(_("dependency.ffmpeg_not_found"))
    return False


def check_python_package(package_name, import_name=None):
    """Check if a Python package is installed"""
    if import_name is None:
        import_name = package_name
    
    try:
        spec = importlib.util.find_spec(import_name)
        if spec is not None:
            try:
                module = importlib.import_module(import_name)
                version = getattr(module, '__version__', 'unknown')
                print_success(_("dependency.package_installed",
                                package=package_name, version=version))
            except Exception:
                print_success(_("dependency.package_simple", package=package_name))
            return True
        else:
            print_error(_("dependency.package_not_found", package=package_name))
            return False
    except Exception:
        print_error(_("dependency.package_not_found", package=package_name))
        return False


def verify_core_dependencies():
    """Verify all core dependencies (required)"""
    print_process(_("dependency.core_verifying"))
    time.sleep(2)

    checks = {
        'python': check_python_version(),
        'ffmpeg': check_ffmpeg(),
        'yt-dlp': check_python_package('yt-dlp', 'yt_dlp'),
        'requests': check_python_package('requests')
    }
    
    all_passed = all(checks.values())
    
    if all_passed:
        print_success(_("dependency.core_success"))
    else:
        print_error(_("dependency.core_failed"))
        print_info(_("dependency.install_missing"))

        if not checks['ffmpeg']:
            print_neutral(_("dependency.install_ffmpeg"))
        
        if not checks['yt-dlp']:
            print_neutral(_("dependency.install_ytdlp"))
        
        if not checks['requests']:
            print_neutral(_("dependency.install_requests"))
    
    return all_passed


def verify_spotify_dependency():
    """Verify Spotify dependency (optional)"""
    print_process(_("dependency.checking_spotify"))
    time.sleep(1.25)
    
    if check_python_package('spotdl'):
        print_success(_("dependency.spotify_available"))
        return True
    else:
        print_info(_("dependency.spotify_unavailable"))
        print_info(_("dependency.spotify_install"))
        print_info(_("dependency.spotify_warning"))
        return False


def display_verification_header():
    """Display verification header"""
    os.system("clear")
    print(f"{Colors.CYAN}╔════════════════════════════════════════╗{Colors.WHITE}")
    print(f"{Colors.CYAN}║        { _('dependency.title') }        ║{Colors.WHITE}")
    print(f"{Colors.CYAN}╚════════════════════════════════════════╝{Colors.WHITE}")
    print()


def verify_dependencies():
    """Main dependency verification function"""
    display_verification_header()
    
    print_info(_("dependency.verifying"))
    print_info(_("dependency.once_only") + "\n")
    time.sleep(1.5)
    
    core_ok = verify_core_dependencies()
    print()
    spotify_ok = verify_spotify_dependency()
    print()
    
    RuntimeConfig.SPOTIFY_AVAILABLE = spotify_ok # type: ignore
    
    if core_ok:
        RuntimeConfig.VERIFIED_DEPENDENCIES = True # type: ignore
        save_config()
        
        print_success(_("dependency.verification_complete"))
        
        if not spotify_ok:
            print_info(_("dependency.spotify_hidden"))
        
        print()
        input("Press enter to continue...")
        return True
    else:
        RuntimeConfig.VERIFIED_DEPENDENCIES = False
        save_config()
        
        print_error(_("dependency.verification_failed"))
        print_info(_("dependency.install_and_retry") + "\n")
        input("Press enter to exit...")
        return False


def reset_verification():
    """Reset verification status"""
    RuntimeConfig.VERIFIED_DEPENDENCIES = False
    RuntimeConfig.SPOTIFY_AVAILABLE = False
    save_config()
    print_success(_("dependency.verification_reset"))
    print_info(_("dependency.verify_next_run"))
