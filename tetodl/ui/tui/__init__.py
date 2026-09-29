# Copyright 2026 rannd1nt
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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