"""
Display utilities and ASCII art
"""
import time
import os
from ..utils.colors import print_error, clear, Colors as C
from ..utils.i18n import get_text as _


def show_ascii(filename=None):
    """Display ASCII art from txt file"""
    header = r'''
  ______     __        ____  __ 
 /_  __/__  / /_____  / __ \/ / 
  / / / _ \/ __/ __ \/ / / / /  
 / / /  __/ /_/ /_/ / /_/ / /___
/_/  \___/\__/\____/_____/_____/
                                
'''
    try:
        with open(f"asset/{filename}.txt", "r", encoding="utf-8") as f:
            print(f.read())
    except Exception:
        print_error("Gagal menampilkan ASCII art.")
        time.sleep(0.45)
        clear()
        print(f'{(C.CYAN)}{header}{C.RESET}')
        


def visit_instagram():
    """Open Instagram profile"""
    os.system("am start -a android.intent.action.VIEW -d https://www.instagram.com/rannd1nt/")


def visit_github():
    """Open GitHub profile"""
    os.system("am start -a android.intent.action.VIEW -d https://github.com/rannd1nt")


def wait_and_clear_prompt():
    """Wait for user input and clear screen"""
    try:
        input(f"\n{_('common.press_enter')}")
    except (KeyboardInterrupt, EOFError):
        pass
    clear()