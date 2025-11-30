"""
User interface package
"""

from .navigation import (
    navigate_folders,
    select_download_folder
)

from .display import (
    show_ascii,
    visit_instagram,
    visit_github,
    wait_and_clear_prompt
)

from .menus import (
    run_in_thread,
    menu_audio_quality,
    menu_folder,
    menu_settings,
    menu_about,
    main_menu
)

__all__ = [
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
    'main_menu'
]