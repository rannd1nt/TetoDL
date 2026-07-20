"""
Dependency verification system.

Provides functions to verify that the runtime environment meets all
requirements: Python version, FFmpeg availability, importable Python
packages, and platform compatibility.

See Also
--------
:func:`verify_core_dependencies` : Orchestrate all dependency checks.
:class:`tetodl.core.resolver.ConfigResolver` : Configuration resolution.
"""
import sys
import os
import shutil
import requests
import importlib.util
import time
from ..constants import IS_WINDOWS, IS_BINARY
from ..utils.i18n_keys import Keys
from ..utils.console import console
from . import config as cfg


def check_python_version():
    """
    Verify that the Python interpreter is version 3.8 or higher.

    Compares ``sys.version_info`` against (3, 8) and prints a success
    or error message through the console.

    Returns
    -------
    bool
        ``True`` if Python >= 3.8, ``False`` otherwise.

    Examples
    --------
    >>> check_python_version()
    True

    See Also
    --------
    :data:`sys.version_info` : Standard library version tuple.
    :func:`check_command_exists` : Lookup external executables.
    """
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        console.ok(Keys.dependency.python_version(
            version=f"{version.major}.{version.minor}.{version.micro}"))
        return True
    else:
        console.err(Keys.dependency.python_old(
            version=f"{version.major}.{version.minor}"))
        return False


def check_command_exists(command):
    """
    Determine whether an executable is present on ``PATH``.

    Uses :func:`shutil.which` (pure Python, cross-platform).

    Parameters
    ----------
    command : str
        Name of the executable to look up (e.g. ``'ffmpeg'``).

    Returns
    -------
    bool
        ``True`` if the command is found, ``False`` otherwise.

    See Also
    --------
    :func:`check_ffmpeg` : Check FFmpeg specifically.
    :func:`python:shutil.which` : Cross-platform executable lookup.
    """
    return shutil.which(command) is not None


def check_ffmpeg():
    """
    Verify that FFmpeg is available and print its version.

    On Windows the check is optional — if missing, PyAV is used as fallback.
    Uses :func:`shutil.which` to locate the binary.

    Returns
    -------
    bool
        ``True`` if FFmpeg is found, ``False`` otherwise.
    """
    ffmpeg_path = shutil.which('ffmpeg')
    if not ffmpeg_path:
        # Check bundled binary path (Windows)
        bundled = os.path.join(os.path.dirname(sys.executable), 'ffmpeg.exe')
        if os.path.exists(bundled):
            ffmpeg_path = bundled

    if ffmpeg_path:
        try:
            import subprocess
            result = subprocess.run(
                [ffmpeg_path, '-version'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                version = version_line.split()[2] if len(version_line.split()) > 2 else "unknown"
                console.ok(Keys.dependency.ffmpeg_version(version=version))
                return True
        except Exception:
            pass

    if IS_WINDOWS and IS_BINARY:
        console.warn(Keys.dependency.ffmpeg_not_found)
        return True  # non-fatal on Windows binary — PyAV handles thumbnails

    console.err(Keys.dependency.ffmpeg_not_found)
    return False


def check_python_package(package_name, import_name=None):
    """
    Verify that a Python package is importable and report its version.

    Uses :func:`importlib.util.find_spec` to locate the package and
    :func:`importlib.import_module` to load its ``__version__``.
    Prints status through the console.

    Parameters
    ----------
    package_name : str
        Display name of the package (e.g. ``'yt-dlp'``).
    import_name : str, optional
        Actual import name if it differs from ``package_name``
        (e.g. ``'yt_dlp'`` when the package is ``'yt-dlp'``).
        Defaults to ``package_name``.

    Returns
    -------
    bool
        ``True`` if the package can be imported, ``False`` otherwise.

    Examples
    --------
    >>> check_python_package("requests")
    True
    >>> check_python_package("yt-dlp", "yt_dlp")
    True

    See Also
    --------
    :func:`importlib.util.find_spec` : Standard import spec finder.
    :func:`check_command_exists` : Check external executables.
    """
    if import_name is None:
        import_name = package_name
    
    try:
        spec = importlib.util.find_spec(import_name)
        if spec is not None:
            try:
                module = importlib.import_module(import_name)
                version = getattr(module, '__version__', 'unknown')
                console.ok(Keys.dependency.package_installed(
                                package=package_name, version=version))
            except Exception:
                console.ok(Keys.dependency.package_simple(package=package_name))
            return True
        else:
            console.err(Keys.dependency.package_not_found(package=package_name))
            return False
    except Exception:
        console.err(Keys.dependency.package_not_found(package=package_name))
        return False



def get_ytdlp_version_info():
    """
    Compare the installed yt-dlp version with the latest PyPI release.

    Fetches ``https://pypi.org/pypi/yt-dlp/json`` and compares version
    strings numerically.  If the network request fails or any exception
    occurs the function safely returns ``(False, "unknown", "unknown")``.

    Returns
    -------
    tuple[bool, str, str]
        ``(is_outdated, current_version, latest_version)``.
        ``is_outdated`` is ``True`` when ``current < latest``.

    Examples
    --------
    >>> outdated, cur, latest = get_ytdlp_version_info()
    >>> outdated
    False

    See Also
    --------
    :func:`verify_core_dependencies` : Orchestrates version checks.
    :pypi:`yt-dlp` : PyPI project page.
    """
    def normalize_version(v_str):
        """Normalise a PEP 440 version string to a comparable dotted form."""
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
    """
    Run all core dependency checks and optionally query for updates.

    Sequentially verifies Python version, FFmpeg, yt-dlp and
    ``requests``.  If all pass and ``check_updates`` is ``True``,
    calls :func:`get_ytdlp_version_info` to detect newer yt-dlp
    releases.  Prints status messages through the console at each
    stage.

    Parameters
    ----------
    check_updates : bool
        Whether to check PyPI for a newer yt-dlp version after core
        dependencies pass.  Defaults to ``True``.

    Returns
    -------
    bool or tuple
        ``True`` if all dependencies pass and no update is available.
        ``("update_available", current, latest)`` if all pass but a
        newer yt-dlp exists.
        ``False`` if any dependency fails.

    Examples
    --------
    >>> result = verify_core_dependencies(check_updates=False)
    >>> result
    True

    See Also
    --------
    :func:`check_python_version` : Python version check.
    :func:`check_ffmpeg` : FFmpeg presence check.
    :func:`check_python_package` : Package import check.
    :func:`get_ytdlp_version_info` : yt-dlp update check.
    :func:`reset_verification` : Reset verified flag.
    """
    console.proc(Keys.dependency.core_verifying)
    time.sleep(2)

    checks = {
        'python': check_python_version(),
        'ffmpeg': check_ffmpeg(),
        'yt-dlp': check_python_package('yt-dlp', 'yt_dlp'),
        'requests': check_python_package('requests')
    }
    
    all_passed = all(checks.values())
    
    if all_passed:
        console.ok(Keys.dependency.core_success)
        if check_updates and checks['yt-dlp']:
            try:
                is_outdated, current, latest = get_ytdlp_version_info()
                if is_outdated:
                    return "update_available", current, latest
            except Exception:
                pass
    else:
        console.err(Keys.dependency.core_failed)
        console.warn(Keys.dependency.install_missing)

        if not checks['ffmpeg']:
            console.neutral(Keys.dependency.install_ffmpeg)
        
        if not checks['yt-dlp']:
            console.neutral(Keys.dependency.install_ytdlp)
        
        if not checks['requests']:
            console.neutral(Keys.dependency.install_requests)
    
    return all_passed


def reset_verification():
    """
    Reset the dependency verification flag and persist the change.

    Sets ``cfg.verified_dependencies`` to ``False``, calls
    :meth:`config.save_config`, and prints confirmation and warning
    messages through the console.

    Examples
    --------
    >>> reset_verification()

    See Also
    --------
    :attr:`config.verified_dependencies` : The flag being reset.
    :func:`verify_core_dependencies` : Re-run verification.
    """
    cfg.verified_dependencies = False
    cfg.save_config()
    console.ok(Keys.dependency.verification_reset)
    console.warn(Keys.dependency.verify_next_run)
