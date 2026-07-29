import sys
import threading
from threading import Thread

from ...core.domain import config as cfg
from ...utils.display import show_ascii
from ...utils.console import console
from ...utils.formatters import Colors, clear
from ...utils.i18n import get_text as _
from ...utils.i18n_keys import Keys


def run_in_thread(fn, *args, **kwargs):
    """Run function in a separate thread"""
    t = threading.Thread(target=fn, args=args, kwargs=kwargs, daemon=True)
    t.start()
    return t

def header():
    # reccomended size: stretch 35x16
    current_style = getattr(cfg, 'header_style', 'default')
    show_ascii(current_style)
    
    title = _(Keys.menu.main.title)
    subtitle = _(Keys.menu.main.subtitle)
    
    console.rich.print(
        f"[bold bright_cyan]{title}[/bold bright_cyan] [bright_red]{subtitle}[/bright_red]\n"
    )

def verification_header(title=None):
    """Display verification header"""
    clear()
    dep_title = title if title else _(Keys.dependency.title)
    print(f"{Colors.CYAN}╔════════════════════════════════════════╗{Colors.WHITE}")
    print(f"{Colors.CYAN}║{dep_title.center(40)}║{Colors.WHITE}")
    print(f"{Colors.CYAN}╚════════════════════════════════════════╝{Colors.WHITE}")
    print()

def thread_cancel_handle(t: Thread):
    try:
        t.join()
    except KeyboardInterrupt:
        sys.exit()