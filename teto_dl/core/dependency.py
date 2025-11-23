"""
Dependency verification system
"""
import os
import sys
import subprocess
import importlib.util
from ..constants import RuntimeConfig
from ..utils.colors import (
    print_process, print_success, print_error, 
    print_info, Colors
)
from .config import save_config


def check_python_version():
    """Check if Python version is 3.8 or higher"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print_success(f"Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print_error(f"Python {version.major}.{version.minor} - Required: 3.8+")
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
                print_success(f"FFmpeg {version}")
                return True
        except Exception:
            pass
    
    print_error("FFmpeg not found")
    return False


def check_python_package(package_name, import_name=None):
    """Check if a Python package is installed"""
    if import_name is None:
        import_name = package_name
    
    try:
        spec = importlib.util.find_spec(import_name)
        if spec is not None:
            # Try to get version
            try:
                module = importlib.import_module(import_name)
                version = getattr(module, '__version__', 'unknown')
                print_success(f"{package_name} {version}")
            except Exception:
                print_success(f"{package_name} (installed)")
            return True
        else:
            print_error(f"{package_name} not found")
            return False
    except Exception:
        print_error(f"{package_name} not found")
        return False


def verify_core_dependencies():
    """Verify all core dependencies (required)"""
    print_process("Verifying core dependencies...")
    
    checks = {
        'python': check_python_version(),
        'ffmpeg': check_ffmpeg(),
        'yt-dlp': check_python_package('yt-dlp', 'yt_dlp'),
        'requests': check_python_package('requests')
    }
    
    all_passed = all(checks.values())
    
    if all_passed:
        print_success("All core dependencies verified!")
    else:
        print_error("Some core dependencies are missing")
        print_info("\nTo install missing dependencies:")
        
        if not checks['ffmpeg']:
            print_info("  pkg install ffmpeg -y")
        
        if not checks['yt-dlp']:
            print_info("  pip install yt-dlp")
        
        if not checks['requests']:
            print_info("  pip install requests")
    
    return all_passed


def verify_spotify_dependency():
    """Verify Spotify dependency (optional)"""
    print_process("Checking Spotify support...")
    
    if check_python_package('spotdl'):
        print_success("Spotify support available")
        return True
    else:
        print_info("Spotify support not available (optional)")
        print_info("Install with: pip install spotdl")
        print_info("WARNING: Installation may take 30-60 minutes on Termux")
        return False


def display_verification_header():
    """Display verification header"""
    os.system("clear")
    print(f"{Colors.BLUE}╔════════════════════════════════════════╗{Colors.WHITE}")
    print(f"{Colors.BLUE}║        TetoDL - First Run Setup        ║{Colors.WHITE}")
    print(f"{Colors.BLUE}╚════════════════════════════════════════╝{Colors.WHITE}")
    print()


def verify_dependencies():
    """
    Main dependency verification function
    Returns: (core_ok, spotify_ok)
    """
    display_verification_header()
    
    print_info("Verifying dependencies for the first time...")
    print_info("This only happens once.\n")
    
    # Verify core dependencies
    core_ok = verify_core_dependencies()
    
    print()
    
    # Verify Spotify (optional)
    spotify_ok = verify_spotify_dependency()
    
    print()
    
    # Update RuntimeConfig
    RuntimeConfig.SPOTIFY_AVAILABLE = spotify_ok
    
    # Consider verified if either:
    # 1. All dependencies OK (including Spotify)
    # 2. Core OK but Spotify not available (acceptable)
    if core_ok:
        RuntimeConfig.VERIFIED_DEPENDENCIES = True
        save_config()
        
        print_success("Verification complete!")
        
        if not spotify_ok:
            print_info("\nNote: Spotify menu akan hidden karena spotdl tidak terinstall")
        
        print()
        input("Tekan Enter untuk melanjutkan...")
        return True
    else:
        RuntimeConfig.VERIFIED_DEPENDENCIES = False
        save_config()
        
        print_error("\nVerification gagal - core dependencies tidak lengkap")
        print_info("Silakan install dependencies yang missing, lalu jalankan lagi")
        print()
        input("Tekan Enter untuk keluar...")
        return False


def reset_verification():
    """Reset verification status - for re-checking dependencies"""
    RuntimeConfig.VERIFIED_DEPENDENCIES = False
    RuntimeConfig.SPOTIFY_AVAILABLE = False
    save_config()
    print_success("Verification status direset")
    print_info("Program akan verify ulang saat dijalankan berikutnya")