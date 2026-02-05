"""
Handles the Command Line Interface (CLI/TUI) presentation layer, user interactions, 
and the main application entry point.
"""

from .navigation import (
    navigate_folders,
    select_download_folder
)

from .entry import app

from .analytics import (
    show_analytics,
    menu_style,
    calculate_stats
)

from .components import (
    console,
    get_free_space,
    run_in_thread,
    header,
    thread_cancel_handle
)

from .about import (
    menu_about
)

__all__ = [
    'app',
    'navigate_folders',
    'select_download_folder',
    'show_ascii',
    'visit_instagram',
    'visit_github',
    'wait_and_clear_prompt',
    'run_in_thread',
    'menu_audio_quality',
    'menu_folder',
    'menu_settings',
    'menu_about',
    'main_menu',
    'show_analytics',
    'menu_style',
    'calculate_stats',
    'console',
    'get_free_space',
    'header',
    'thread_cancel_handle'

]