"""
TUI layer — Textual-based interactive interface.
"""

from .about import menu_about
from .analytics import calculate_stats, menu_style, show_analytics
from .components import console, header, run_in_thread, thread_cancel_handle
from .navigation import navigate_folders, select_download_folder

__all__ = [
    'calculate_stats',
    'console',
    'header',
    'menu_about',
    'menu_style',
    'navigate_folders',
    'run_in_thread',
    'select_download_folder',
    'show_analytics',
    'thread_cancel_handle',
]