"""
Color codes and colored print functions
"""
import os
from rich.console import Console
from questionary import Style

console = Console()

def menu_style():
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
    if not title: return ""
    title = str(title).strip()
    
    if len(title) <= max_chars:
        return title
    return title[:max_chars-3] + "..."

def format_duration(seconds):
    """Format duration"""
    if not seconds: return "0s"
    try:
        seconds = int(seconds)
    except:
        return "0s"
        
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    parts = []
    if hours > 0: parts.append(f"{hours}h")
    if minutes > 0: parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    
    if not parts: return f"{secs}s"
    return " ".join(parts)

def format_duration_digital(seconds):
    """Format duration digital (misal: 04:20 atau 1:02:12) - Untuk Tabel"""
    if not seconds: return "--:--"
    try:
        seconds = int(seconds)
    except:
        return "--:--"

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"

# PRINT UTILITY STYLES
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

def print_process(message, str_only=False):
    """Print untuk proses/progress (biru)"""
    msg = f"{Colors.BLUE}[i]{Colors.WHITE} {message}"
    if str_only:
        return msg
    print(msg)


def print_info(message, str_only=False):
    """Print untuk info/warning (kuning)"""
    msg = f"{Colors.YELLOW}[!]{Colors.WHITE} {message}"
    if str_only:
        return msg
    print(msg)


def print_success(message, str_only=False):
    """Print untuk success (hijau)"""
    msg = f"{Colors.GREEN}[✓]{Colors.WHITE} {message}"
    if str_only:
        return msg
    print(msg)


def print_debug(message, str_only=False):
    """Print untuk debug (light green)"""
    msg = f"{Colors.LIGHT_GREEN}[DEBUG]{Colors.WHITE} {message}"
    if str_only:
        return msg
    print(msg)


def print_error(message, str_only=False):
    """Print untuk error (merah)"""
    msg = f"{Colors.RED}[✗]{Colors.WHITE} {message}"
    if str_only:
        return msg
    print(msg)


def print_neutral(message, symbol="[+]", str_only=False):
    """Print untuk pesan netral (putih)"""
    msg = f"{Colors.WHITE}{symbol} {message}"
    if str_only:
        return msg
    print(msg)


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


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

def color(text: str, ansi: str, bold: bool = False) -> str:
    """
    Apply ANSI coloring easily.
    """

    code = colors.get(ansi)
    if code is None:
        raise ValueError(f"Invalid color code '{ansi}'")

    if bold:
        return f"{Colors.BOLD}{code}{text}{Colors.RESET}"

    return f"{code}{text}{Colors.RESET}"


