"""
Context Managers for temporary console state and loading animations.
"""
import sys
import time
import threading
from contextlib import AbstractContextManager

class ConsoleStateContext(AbstractContextManager):
    """Mengatur override state secara sementara (e.g., quiet_mode)."""
    
    def __init__(self, console, overrides: dict):
        self.console = console
        self.overrides = overrides
        self._backup_state = {}

    def __enter__(self):
        for key, new_val in self.overrides.items():
            if not new_val:
                continue
            if hasattr(self.console.state, key):
                self._backup_state[key] = getattr(self.console.state, key)
                setattr(self.console.state, key, new_val)
        return self.console

    def __exit__(self, exc_type, exc_val, exc_tb):
        for key, old_val in self._backup_state.items():
            setattr(self.console.state, key, old_val)


class ConsoleSpinnerContext(AbstractContextManager):
    """Animasi Loading Spinner yang terintegrasi dengan Console Theme."""
    
    def __init__(self, console, text: str, delay: float = 0.1):
        self.console = console
        self.text = text
        self.delay = delay
        self.chars = ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"]
        self.running = False
        self.thread = None

    def _spin_loop(self):
        i = 0
        theme = self.console.theme
        prefix = f"{theme.proc_color}{theme.proc}{theme.reset_color}"
        
        while self.running:
            sys.stdout.write(
                f"\r{prefix} {theme.text_color}{self.text} {theme.accent_color}{self.chars[i]}{theme.reset_color}"
            )
            sys.stdout.flush()
            time.sleep(self.delay)
            i = (i + 1) % len(self.chars)

    def __enter__(self):
        # Jangan jalankan spinner jika sedang quiet
        if self.console.state.is_quiet:
            return self

        self.running = True
        self.thread = threading.Thread(target=self._spin_loop, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.running:
            return
            
        self.running = False
        if self.thread:
            self.thread.join()
            
        # Bersihkan baris terminal dari spinner
        sys.stdout.write("\r\033[K") 
        sys.stdout.flush()