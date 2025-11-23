"""
Display utilities and ASCII art
"""
import time
import os
from ..utils.colors import print_error


def show_ascii(filename):
    """Display ASCII art from txt file"""
    try:
        with open(f"asset/{filename}.txt", "r", encoding="utf-8") as f:
            print(f.read())
    except Exception:
        print_error("Gagal menampilkan ASCII art.")
        time.sleep(1)


def visit_instagram():
    """Open Instagram profile"""
    os.system("am start -a android.intent.action.VIEW -d https://www.instagram.com/rannd1nt/")


def visit_github():
    """Open GitHub profile"""
    os.system("am start -a android.intent.action.VIEW -d https://github.com/rannd1nt")


def wait_and_clear_prompt():
    """Wait for user input and clear screen"""
    try:
        input("\nTekan Enter untuk kembali ke menu...")
    except (KeyboardInterrupt, EOFError):
        pass
    os.system("clear")