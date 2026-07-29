"""
Color codes and colored print functions
"""
import os
from typing import Literal

from .console import console as _tetodl_console

console = _tetodl_console.rich
"""
Alias for ``console.rich`` -- the underlying ``rich.console.Console`` instance.

Kept here for backward compatibility so existing importers
(``from tetodl.utils.formatters import console``) continue to work.
New code should use ``from tetodl.utils.console import console`` and access
``console.rich`` directly.
"""

def search_style():
    from questionary import Style
    return Style([
        ('qmark', 'fg:cyan'),
        ('question', 'fg:white nobold'),
        ('answer', 'fg:white'),
        ('pointer', 'fg:cyan'),
        ('highlighted', 'fg:cyan'),
        ('selected', 'fg:cyan'),
        ('separator', 'fg:grey'),
        ('instruction', 'fg:grey'),
        ('disabled', 'fg:#666666'),
    ])

def menu_style():
    from questionary import Style
    return Style([
        ('qmark', 'fg:cyan'),
        ('question', 'fg:cyan'),
        ('answer', 'fg:white'),
        ('pointer', 'fg:cyan bold'),
        ('highlighted', 'fg:cyan bold'),
        ('selected', 'fg:cyan'),
        ('separator', 'fg:grey'),
        ('instruction', 'fg:grey'),
        ('disabled', 'fg:#666666'),
    ])

def truncate_title(title, max_words=None, max_chars=50):
    if not title:
        return "Unknown Title"

    title = str(title).strip()
    title = title.replace('\n', ' ').replace('\r', '')

    if len(title) <= max_chars:
        return title

    if max_chars <= 3:
        return title[:max_chars]

    return title[:max_chars-3] + "..."

def format_duration(seconds):
    """Format duration"""
    if not seconds:
        return "0s"
    try:
        seconds = int(seconds)
    except Exception:
        return "0s"

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")

    if not parts:
        return f"{secs}s"
    return " ".join(parts)

def format_duration_digital(seconds):
    """Format duration digital (misal: 04:20 atau 1:02:12) - Untuk Tabel"""
    if not seconds:
        return "--:--"
    try:
        seconds = int(seconds)
    except Exception:
        return "--:--"

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"

class Colors:
    """ANSI color codes"""
    RESET = '\033[0m'
    BLUE = '\033[94m'
    LIGHT_GREEN = '\033[92m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    WHITE = '\033[0m'
    CYAN = '\033[96m'
    LIGHT_GRAY = '\033[37m'
    BOLD = '\033[1m'


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

CCode = Literal['r', 'g', 'y', 'b', 'c', 'w', 'lgrn', 'lgry']

colors = {
        'r': Colors.RED,
        'g': Colors.GREEN,
        'y': Colors.YELLOW,
        'b': Colors.BLUE,
        'c': Colors.CYAN,
        'w': Colors.WHITE,
        'lgrn': Colors.LIGHT_GREEN,
        'lgry': Colors.LIGHT_GRAY,
    }

def key_color(txt: str, ansi=Colors.YELLOW, bold=False):
    if not bold:
        return f'{ansi}{txt}{Colors.RESET}'
    else:
        return f'{Colors.BOLD}{ansi}{txt}{Colors.RESET}'


def colored_switch(flag: bool, true_txt: str, false_txt: str,
    true_c=Colors.GREEN, false_c=Colors.RED
    ) -> str:
    return f'{true_c}{true_txt}{Colors.RESET}' if flag else f'{false_c}{false_txt}{Colors.RESET}'

def colored_info(key: str, data, ansi_key=Colors.WHITE, ansi_data=Colors.GREEN, bold_key=False):
    """ Custom coloring = key : data """
    if not bold_key:
        return f'{ansi_key}{key}{Colors.RESET}{ansi_data}{data}{Colors.RESET}'
    else:
        return f'{Colors.BOLD}{ansi_key}{key}{Colors.RESET}{ansi_data}{data}{Colors.RESET}'

def color(text: str, ansi: CCode | str, bold: bool = False) -> str:
    """
    Apply ANSI coloring easily.
    """

    code = colors.get(ansi)
    if code is None:
        raise ValueError(f"Invalid color code '{ansi}'")

    if bold:
        return f"{Colors.BOLD}{code}{text}{Colors.RESET}"

    return f"{code}{text}{Colors.RESET}"


def human_size(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    if size < 1024**2:
        return f"{size/1024:.1f} KB"
    return f"{size/(1024**2):.1f} MB"


AUDIO_EXTS = {'.mp3', '.m4a', '.wav', '.flac', '.opus'}
VIDEO_EXTS = {'.mp4', '.mkv', '.webm', '.avi', '.mov'}
MEDIA_EXTS = AUDIO_EXTS | VIDEO_EXTS
IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.svg'}
ARCHIVE_EXTS = {'.zip', '.rar', '.7z', '.tar', '.gz'}
CODE_EXTS = {'.py', '.js', '.html', '.css', '.json', '.c', '.rs'}
DOC_EXTS = {'.pdf', '.txt', '.md', '.doc', '.docx'}
APP_EXTS = {'.apk', '.exe', '.msi'}


def icon_for_ext(ext: str) -> str:
    ext = ext.lower()
    if ext in AUDIO_EXTS:
        return 'audio'
    if ext in VIDEO_EXTS:
        return 'video'
    if ext in IMAGE_EXTS:
        return 'image'
    if ext in ARCHIVE_EXTS:
        return 'archive'
    if ext in CODE_EXTS:
        return 'code'
    if ext in DOC_EXTS:
        return 'doc'
    if ext in APP_EXTS:
        return 'app'
    return 'file'
