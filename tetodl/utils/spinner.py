"""
Loading spinner for long operations
"""
import sys
import time
import threading
from ..utils.styles import Colors


class Spinner:
    """Animated loading spinner"""
    
    def __init__(self, message="Loading...", delay=0.1):
        self.message = message
        self.delay = delay
        self.spinner_chars = ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"]
        self.running = False
        self.spinner_thread = None

    def spin(self):
        """Internal spinner animation loop"""
        i = 0
        while self.running:
            sys.stdout.write(
                f"\r{Colors.BLUE}[i]{Colors.WHITE} {self.message} {self.spinner_chars[i]}"
            )
            sys.stdout.flush()
            time.sleep(self.delay)
            i = (i + 1) % len(self.spinner_chars)

    def start(self):
        """Start the spinner"""
        self.running = True
        self.spinner_thread = threading.Thread(target=self.spin)
        self.spinner_thread.daemon = True
        self.spinner_thread.start()

    def stop(self, message=None):
        """Stop the spinner and optionally print a message"""
        self.running = False
        if self.spinner_thread:
            self.spinner_thread.join()
        # Clear line
        sys.stdout.write("\r" + " " * (len(self.message) + 15) + "\r")
        if message:
            print(message)