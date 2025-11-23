"""
Color codes and colored print functions
"""
import os

class Colors:
    """ANSI color codes"""
    BLUE = '\033[94m'
    LIGHT_GREEN = '\033[92m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    WHITE = '\033[0m'
    BOLD = '\033[1m'


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