"""
Bootstrap: Handles initialization, dependency verification, and update checks.
"""
import sys
import threading
from tetodl.constants import RuntimeConfig
from tetodl.core.config import initialize_config
from tetodl.core.history import load_history
from tetodl.core.dependency import get_ytdlp_version_info

def setup_application(force_recheck=False):
    """Initialize configuration and verify system integrity."""
    initialize_config()
    load_history()

    if force_recheck or not RuntimeConfig.VERIFIED_DEPENDENCIES:
        from ..verifier import verify_dependencies

        header_title = "System Integrity Check" if force_recheck else None
        if not verify_dependencies(header_title):
            sys.exit(1)

def start_update_checker(app_instance):
    """Start background thread to check for updates."""
    threading.Thread(target=_update_checker_worker, args=(app_instance,), daemon=True).start()

def _update_checker_worker(app_instance):
    """Background worker to check updates silently."""
    try:
        is_outdated, current, latest = get_ytdlp_version_info()
        if is_outdated:
            app_instance.update_status = (current, latest)
    except Exception:
        pass