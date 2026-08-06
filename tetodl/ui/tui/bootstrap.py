"""
TUI bootstrap — wraps general startup with interactive dependency verification.
"""

from tetodl.ui import bootstrap


def setup_and_verify(force_recheck=False):
    bootstrap.setup_application(force_recheck=force_recheck)
