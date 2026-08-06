"""
Bootstrap: Handles initialization, system integrity checks, and update checks.
"""
import sys
import threading

from tetodl.core.domain import config as cfg
from tetodl.core.domain.config import initialize_config
from tetodl.core.domain.history import load_history
from tetodl.core.dependency import get_ytdlp_version_info
from tetodl.core.domain.env import env


def setup_application(force_recheck=False):
    """Initialize configuration, verify system integrity and env."""
    if force_recheck:
        env.recheck()
    initialize_config()
    load_history()

    if force_recheck or not cfg.verified_dependencies:
        from tetodl.ui.tui.verifier import verify_dependencies

        header_title = "System Integrity Check" if force_recheck else None
        if not verify_dependencies(header_title):
            sys.exit(1)


def needs_dep_check():
    return not cfg.verified_dependencies


def start_update_checker(app_instance):
    threading.Thread(target=_update_checker_worker, args=(app_instance,), daemon=True).start()


def _update_checker_worker(app_instance):
    try:
        is_outdated, current, latest = get_ytdlp_version_info()
        if is_outdated:
            app_instance.update_status = (current, latest)
    except Exception:
        pass