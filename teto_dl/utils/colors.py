"""
Color codes and colored print functions
"""
import os

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


def print_process(message):
    """Print untuk proses/progress (biru)"""
    print(f"{Colors.BLUE}[i]{Colors.WHITE} {message}")


def print_info(message):
    """Print untuk info/warning (kuning)"""
    print(f"{Colors.YELLOW}[!]{Colors.WHITE} {message}")


def print_success(message):
    """Print untuk success (hijau)"""
    print(f"{Colors.GREEN}[✓]{Colors.WHITE} {message}")


def print_debug(message):
    """Print untuk debug (light green)"""
    print(f"{Colors.LIGHT_GREEN}[DEBUG]{Colors.WHITE} {message}")


def print_error(message):
    """Print untuk error (merah)"""
    print(f"{Colors.RED}[✗]{Colors.WHITE} {message}")


def print_neutral(message, symbol="[-]"):
    """Print untuk pesan netral (putih)"""
    print(f"{Colors.WHITE}{symbol} {message}")


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')