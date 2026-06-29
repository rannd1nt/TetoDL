"""
Defines themes, colors, and terminal capability detection.
"""
import sys
from dataclasses import dataclass
from colorama import Fore, Style

@dataclass
class LogTheme:
    ok: str; warn: str; proc: str; err: str; exit: str; panic: str; debug: str
    
    ok_color: str = Fore.GREEN
    warn_color: str = Fore.YELLOW
    proc_color: str = Fore.BLUE
    info_color: str = Fore.CYAN
    err_color: str = Fore.RED
    exit_color: str = Fore.WHITE
    panic_color: str = Fore.RED + Style.BRIGHT
    debug_color: str = Fore.LIGHTGREEN_EX

    text_color: str = Fore.WHITE
    accent_color: str = Fore.CYAN
    reset_color: str = Style.RESET_ALL

RichTheme = LogTheme(
    ok="[✓]", warn="[!]", proc="[i]", err="[✗]", exit="[-]", panic="[PANIC!]", debug="[DEBUG]"
)

PlainTheme = LogTheme(
    ok="[OK]", warn="[WARN]", proc="[PROC]", err="[ERR]", exit="[EXIT]", panic="[PANIC!]", debug="[DEBUG]"
)

def detect_terminal_theme() -> LogTheme:
    try:
        if sys.stdout.encoding.lower() == 'utf-8':
            return RichTheme
    except Exception:
        pass

    return PlainTheme