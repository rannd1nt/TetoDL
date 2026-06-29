"""
The Core Logger and Rendering Engine.
"""
import sys
from dataclasses import dataclass
from colorama import init

from .themes import detect_terminal_theme, LogTheme
from .contexts import ConsoleStateContext, ConsoleSpinnerContext
from ..i18n import get_text
from ..i18n_keys import I18nKey

init(autoreset=True)

@dataclass
class ConsoleState:
    is_quiet: bool = False
    is_debug: bool = False

class Console:
    def __init__(self):
        self.state = ConsoleState()
        self.theme: LogTheme = detect_terminal_theme()

    # Internal Method
    def _resolve_text(self, message: str | I18nKey, **kwargs) -> str:
        hl_kwargs = {}
        target_key = message
        
        if isinstance(message, tuple):
            target_key, dynamic_kwargs = message
            kwargs = {**dynamic_kwargs, **kwargs}

        for k, v in kwargs.items():
            hl_kwargs[k] = f"{self.theme.accent_color}{v}{self.theme.reset_color}{self.theme.text_color}"
            
        return get_text(target_key, **hl_kwargs)

    def _print(self, symbol: str, color: str, message: str | I18nKey, **kwargs):
        if self.state.is_quiet:
            return
            
        text = self._resolve_text(message, **kwargs)
        
        final_output = (
            f"{color}{symbol}{self.theme.reset_color} "
            f"{self.theme.text_color}{text}{self.theme.reset_color}"
        )
        print(final_output)


    # Context Factory
    def context(self, **overrides: ConsoleState) -> ConsoleStateContext:
        return ConsoleStateContext(self, overrides)

    def spin(self, message: str | I18nKey, **kwargs) -> ConsoleSpinnerContext:
        text = self._resolve_text(message, **kwargs)
        return ConsoleSpinnerContext(self, text)
    
    # Logging Method
    def ok(self, message: str | I18nKey, **kwargs):
        "ok/success"
        self._print(self.theme.ok, self.theme.ok_color, message, **kwargs)
    
    def warn(self, message: str | I18nKey, **kwargs):
        "warning/info"
        self._print(self.theme.warn, self.theme.warn_color, message, **kwargs)
 
    def err(self, message: str | I18nKey, **kwargs):
        "error"
        self._print(self.theme.err, self.theme.err_color, message, **kwargs)
       
    def proc(self, message: str | I18nKey, **kwargs):
        "process"
        self._print(self.theme.proc, self.theme.proc_color, message, **kwargs)

    def debug(self, message: str | I18nKey, **kwargs):
        "debug"
        self._print(self.theme.debug, self.theme.debug_color, message, **kwargs)

    def neutral(self, message: str | I18nKey, **kwargs):
        "neutral/custom message"
        self._print(self.theme.exit, self.theme.text_color, message, **kwargs)

    def exit(self, message: str | I18nKey = "Exiting...", **kwargs):
        self._print(self.theme.exit, self.theme.exit_color, message, **kwargs)
        sys.exit(0)

    def panic(self, message: str | I18nKey, **kwargs):
        text = self._resolve_text(message, **kwargs)
        print(f"{self.theme.panic_color}{self.theme.panic} {text}{self.theme.reset_color}")
        sys.exit(1)