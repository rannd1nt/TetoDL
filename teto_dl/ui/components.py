import os
import sys
import shutil
from threading import Thread
import threading

from ..constants import RuntimeConfig
from ..utils.i18n import get_text as _
from ..utils.display import show_ascii
from ..utils.styles import Colors, console, clear

def run_in_thread(fn, *args):
    """Run function in a separate thread"""
    t = threading.Thread(target=fn, args=args, daemon=True)
    t.start()
    return t

def header():
    # reccomended size: stretch 35x16
    current_style = getattr(RuntimeConfig, 'HEADER_STYLE', 'default')
    show_ascii(current_style)
    
    title = _('menu.main.title')
    subtitle = _('menu.main.subtitle')
    
    console.print(
        f"[bold bright_cyan]{title}[/bold bright_cyan] [bright_red]{subtitle}[/bright_red]\n"
    )

def verification_header(title=None):
    """Display verification header"""
    clear()
    dep_title = title if title else _('dependency.title')
    print(f"{Colors.CYAN}╔════════════════════════════════════════╗{Colors.WHITE}")
    print(f"{Colors.CYAN}║{dep_title.center(40)}║{Colors.WHITE}")
    print(f"{Colors.CYAN}╚════════════════════════════════════════╝{Colors.WHITE}")
    print()

def thread_cancel_handle(t: Thread) -> SystemExit:
    try:
        t.join()
    except KeyboardInterrupt:
        sys.exit()

def get_free_space(path):
    """Helper buat dapetin free space dalam format GB yang manusiawi"""
    try:
        if not os.path.exists(path):
            check_path = os.path.dirname(path)
        else:
            check_path = path
            
        _, _, free = shutil.disk_usage(check_path)
        return f"{free / (2**30):.1f} GB free"
    except:
        return "N/A"