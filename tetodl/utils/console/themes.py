"""
Theme definitions, colour palettes, and terminal-capability detection.

Two pre-built theme instances are provided:

* :data:`RichTheme` -- uses Unicode glyphs (UTF-8).
* :data:`PlainTheme` -- uses ASCII-only labels.

The :func:`detect_terminal_theme` helper chooses one of the two based on
the current ``sys.stdout.encoding``.

See Also
--------
:class:`Console` : Uses a :class:`LogTheme` for all output rendering.
"""
import sys
from dataclasses import dataclass
from colorama import Fore, Style

@dataclass
class LogTheme:
    """Colour palette and label symbols for a single visual theme.

    Each log level is associated with a pair ``(symbol, colour)``.
    The instance also carries generic foreground and accent colours
    used by context managers such as
    :class:`~tetodl.utils.console.contexts.ConsoleSpinnerContext`.

    Parameters
    ----------
    ok : str
        Symbol printed for successful / OK messages.
    warn : str
        Symbol printed for warnings.
    proc : str
        Symbol printed for in-progress / processing messages.
    err : str
        Symbol printed for errors.
    exit : str
        Symbol printed for normal exits.
    panic : str
        Symbol printed for fatal errors.
    debug : str
        Symbol printed for debug messages.
    ok_color : str, optional
        ANSI colour code for OK messages (default ``Fore.GREEN``).
    warn_color : str, optional
        ANSI colour code for warnings (default ``Fore.YELLOW``).
    proc_color : str, optional
        ANSI colour code for progress messages (default ``Fore.BLUE``).
    info_color : str, optional
        ANSI colour code for informational highlights (default ``Fore.CYAN``).
    err_color : str, optional
        ANSI colour code for errors (default ``Fore.RED``).
    exit_color : str, optional
        ANSI colour code for exit messages (default ``Fore.WHITE``).
    panic_color : str, optional
        ANSI colour code for panic messages (default ``Fore.RED + Style.BRIGHT``).
    debug_color : str, optional
        ANSI colour code for debug messages (default ``Fore.LIGHTGREEN_EX``).
    text_color : str, optional
        Default text foreground colour (default ``Fore.WHITE``).
    accent_color : str, optional
        Accent colour for highlights (default ``Fore.CYAN``).
    reset_color : str, optional
        ANSI reset sequence (default ``Style.RESET_ALL``).

    Examples
    --------
    >>> theme = LogTheme(ok="[Y]", err="[N]")
    >>> print(f"{theme.ok_color}{theme.ok}{theme.reset_color}")

    See Also
    --------
    :data:`RichTheme`
    :data:`PlainTheme`
    :func:`detect_terminal_theme`
    """
    ok: str
    warn: str
    proc: str
    err: str
    exit: str
    panic: str
    debug: str
    
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
"""Unicode-rich theme for UTF-8 terminals."""

PlainTheme = LogTheme(
    ok="[OK]", warn="[WARN]", proc="[PROC]", err="[ERR]", exit="[EXIT]", panic="[PANIC!]", debug="[DEBUG]"
)
"""ASCII-only theme for terminals without full Unicode support."""

def detect_terminal_theme() -> LogTheme:
    """Detect the best theme for the current terminal.

    Checks ``sys.stdout.encoding``; returns :data:`RichTheme` when the
    encoding is UTF-8 and :data:`PlainTheme` otherwise.

    Returns
    -------
    LogTheme
        Either :data:`RichTheme` or :data:`PlainTheme`.

    Examples
    --------
    >>> theme = detect_terminal_theme()
    >>> print(theme.ok)
    '[✓]'

    See Also
    --------
    :data:`RichTheme`
    :data:`PlainTheme`
    """
    try:
        if sys.stdout.encoding.lower() == 'utf-8':
            return RichTheme
    except Exception:
        pass

    return PlainTheme