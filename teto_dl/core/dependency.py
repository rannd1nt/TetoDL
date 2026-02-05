"""
Dependency verification system
"""
import sys
import requests
import subprocess
import importlib.util
import time
from ..constants import RuntimeConfig, IS_WINDOWS
from ..utils.i18n import get_text as _
from ..utils.styles import (
    print_process, print_success, print_error, 
    print_info, print_neutral
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

def verify_platform_compatibility():
    """
    Check if the current platform is supported.
    Returns (True, None) if supported.
    Returns (False, ErrorMessage) if unsupported.
    """
    if IS_WINDOWS:
        return False, _("error.platform.windows_not_supported")
    return True, None

def get_ytdlp_version_info():
    """
    Check installed yt-dlp version against PyPI.
    Returns: (is_outdated, current_version, latest_version)
    """
    def normalize_version(v_str):
        try:
            return ".".join([str(int(x)) for x in v_str.split('.') if x.isdigit()])
        except ValueError:
            return v_str
        
    try:
        import yt_dlp
        raw_current = yt_dlp.version.__version__
        
        response = requests.get("https://pypi.org/pypi/yt-dlp/json", timeout=3)
        if response.status_code == 200:
            data = response.json()
            raw_latest = data['info']['version']
            
            clean_current = normalize_version(raw_current)
            clean_latest = normalize_version(raw_latest)

            curr_v = [int(x) for x in clean_current.split('.')]
            latest_v = [int(x) for x in clean_latest.split('.')]

            is_outdated = curr_v < latest_v
            
            return is_outdated, clean_current, clean_latest
            
    except Exception:
        pass
    
    return False, "unknown", "unknown"

def verify_core_dependencies(check_updates: bool = True):
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
        if check_updates and checks['yt-dlp']:
            try:
                is_outdated, current, latest = get_ytdlp_version_info()
                if is_outdated:
                    return "update_available", current, latest
            except Exception:
                pass
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

def verify_spotify_functional():
    """
    Verify Spotify dependency availability and FUNCTIONALITY (Rate Limit Check).
    """
    print_process(_("dependency.checking_spotify"))
    time.sleep(1)
    
    # 1. Cek Package Terinstall
    if not check_python_package('spotdl'):
        print_info(_("dependency.spotify_unavailable"))
        print_info(_("dependency.spotify_install"))
        return False

    # 2. Cek Fungsionalitas (Rate Limit Check)
    print_process(_("dependency.spotify_testing"))
    
    dummy_track = "https://open.spotify.com/track/2ksyzVfU0WJoBpu8otr4pz?si=9cb9bd5dbfa64f61" 
    
    try:
        result = subprocess.run(
            ['spotdl', dummy_track],
            capture_output=True,
            text=True,
            timeout=15 
        )
        
        output = result.stdout + result.stderr
        
        if "429" in output or "rate" in output or "request limit" in output:
            print_error(_("dependency.spotify_ratelimited"))
            print_info(_("dependency.spotify_ratelimit_desc"))
            return False
            
        if result.returncode != 0:
            print_error(_("dependency.spotify_error_test"))
            return False

        print_success(_("dependency.spotify_available"))
        return True

    except Exception:
        print_error(_("dependency.spotify_error_test"))
        return False
    
def reset_verification():
    """Reset verification status"""
    RuntimeConfig.VERIFIED_DEPENDENCIES = False
    RuntimeConfig.SPOTIFY_AVAILABLE = False
    save_config()
    print_success(_("dependency.verification_reset"))
    print_info(_("dependency.verify_next_run"))
