"""
Handles the Command Line Interface (CLI/TUI) presentation layer, user interactions, 
and the main application entry point.
"""

from .about import menu_about
from .analytics import calculate_stats, menu_style, show_analytics
from .components import console, header, run_in_thread, thread_cancel_handle
from .entry import app
from .navigation import navigate_folders, select_download_folder

__all__ = [
    'app',
    'calculate_stats',
    'console',
    'get_free_space',
    'header',
    'main_menu',
    'menu_about',
    'menu_audio_quality',
    'menu_folder',
    'menu_settings',
    'menu_style',
    'navigate_folders',
    'run_in_thread',
    'select_download_folder',
    'show_analytics',
    'show_ascii',
    'thread_cancel_handle',
    'visit_github',
    'visit_instagram',
    'wait_and_clear_prompt'

]