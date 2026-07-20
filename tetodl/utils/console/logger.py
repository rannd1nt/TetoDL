"""
The core logger, rendering engine, and :class:`Console` singleton factory.

Every TetoDL component that needs to print a status line, warning, error,
or animated spinner imports :class:`Console` from this module.  Console
output is theme-aware (Unicode symbols when the terminal supports UTF-8,
plain ASCII otherwise), colourised via :mod:`colorama`, and localised
through the :mod:`~tetodl.utils.i18n` layer.

The :class:`Console` instance is **not** created here — the pre-configured
singleton lives in :mod:`tetodl.utils.console` and is accessed as::

    from tetodl.utils.console import console
"""
import sys
from typing_extensions import deprecated
from dataclasses import dataclass
from colorama import init

from .themes import detect_terminal_theme, LogTheme
from .contexts import ConsoleStateContext, ConsoleSpinnerContext
from ..i18n import get_text
from ..i18n_keys import I18nKey

init(autoreset=True)

@dataclass
class ConsoleState:
    """Runtime state flags for a :class:`Console` instance.

    Attributes
    ----------
    is_quiet : bool
        Suppress all non-debug output when ``True``.
    is_debug : bool
        Enable debug output when ``True``.
    debug_mode : str
        Active debug filtering mode — ``'all'``, ``'errors'``,
        or ``'concise'``.
    """
    is_quiet: bool = False
    is_debug: bool = False
    debug_mode: str = 'all'

class Console:
    """Central output interface for TetoDL.

    Wraps every printed line with theme-aware symbols, colours, and
    i18n resolution.  Methods are grouped into several categories:

    **Status output** — :meth:`ok`, :meth:`err`, :meth:`warn`,
    :meth:`proc`, :meth:`neutral`, :meth:`debug`, :meth:`exit`,
    :meth:`panic`.
        Each prints a themed symbol followed by the resolved message.

    **Loading animation** — :meth:`spin`.
        Context manager that displays a terminal spinner while a
        long-running operation executes.

    **Display control** — :meth:`context`.
        Context manager that temporarily overrides state flags
        (e.g. ``is_quiet``, ``is_debug``).

    See Also
    --------
    ConsoleState : Runtime flags queried by this class.
    LogTheme : Symbol and colour set used for rendering.
    set_debug : Global debug enabler that updates the console state.

    Examples
    --------
    >>> from tetodl.utils.console import console
    >>> from tetodl.utils.i18n_keys import Keys
    >>> console.ok(Keys.system.ok)
    >>>
    >>> with console.spin("Processing..."):
    ...     pass
    """

    def __init__(self):
        """Initialise a :class:`Console` with default state and an
        auto-detected :class:`LogTheme`."""
        self.state = ConsoleState()
        self.theme: LogTheme = detect_terminal_theme()

    def _resolve_text(self, message: str | I18nKey, **kwargs) -> str:
        """Resolve an i18n key into a display string, substituting
        highlighted keyword arguments into the template."""
        hl_kwargs = {}
        
        if isinstance(message, tuple):
            target_key, dynamic_kwargs = message
            kwargs = {**dynamic_kwargs, **kwargs}
        else:
            target_key = message

        for k, v in kwargs.items():
            hl_kwargs[k] = f"{self.theme.accent_color}{v}{self.theme.reset_color}{self.theme.text_color}"
            
        return get_text(target_key, **hl_kwargs)

    def _print(self, symbol: str, color: str, message: str | I18nKey, **kwargs):
        """Print a status line with the given *symbol* and *color*,
        respecting the ``is_quiet`` flag."""
        if self.state.is_quiet:
            return
            
        text = self._resolve_text(message, **kwargs)
        
        final_output = (
            f"{color}{symbol}{self.theme.reset_color} "
            f"{self.theme.text_color}{text}{self.theme.reset_color}"
        )
        print(final_output)


    def context(self, **overrides: bool | str) -> ConsoleStateContext:
        """Return a context manager that temporarily overrides
        :class:`ConsoleState` attributes.

        Parameters
        ----------
        **overrides : ConsoleState
            Keyword arguments matching :class:`ConsoleState` fields
            (e.g. ``is_quiet=True``, ``is_debug=True``).  Only
            truthy values take effect.

        Returns
        -------
        ConsoleStateContext
            Context manager; on ``__enter__`` it yields the
            :class:`Console` instance itself.

        Examples
        --------
        >>> from tetodl.utils.console import console
        >>> with console.context(is_quiet=True):
        ...     console.ok("This line is suppressed.")
        >>> console.ok("This line is visible.")

        See Also
        --------
        spin : Context manager for loading animations.
        """
        return ConsoleStateContext(self, overrides)

    def spin(self, message: str | I18nKey, **kwargs) -> ConsoleSpinnerContext:
        """Return a context manager that displays a terminal spinner.

        The spinner cycles through Unicode braille characters and is
        suppressed when ``is_quiet`` is ``True``.

        Parameters
        ----------
        message : str or I18nKey
            Text displayed alongside the spinner.
        **kwargs
            Format arguments for the message text.

        Returns
        -------
        ConsoleSpinnerContext
            Context manager that starts the animation on ``__enter__``
            and clears it on ``__exit__``.

        Examples
        --------
        >>> from tetodl.utils.console import console
        >>> with console.spin("Downloading..."):
        ...     import time; time.sleep(2)

        See Also
        --------
        context : Context manager for temporary state overrides.
        proc : Non-animated status line with the same symbol.
        """
        text = self._resolve_text(message, **kwargs)
        return ConsoleSpinnerContext(self, text)
    
    # Logging Methods
    def ok(self, message: str | I18nKey, **kwargs):
        """Print a themed success / confirmation message.

        Parameters
        ----------
        message : str or I18nKey
            Success text or i18n key.
        **kwargs
            Format arguments for the message.

        Returns
        -------
        None

        Examples
        --------
        >>> from tetodl.utils.console import console
        >>> console.ok("Download complete.")

        See Also
        --------
        warn : Warning-level output.
        err : Error-level output.
        proc : In-progress / info output.
        neutral : Un-themed custom message.
        """
        self._print(self.theme.ok, self.theme.ok_color, message, **kwargs)
    
    def warn(self, message: str | I18nKey, **kwargs):
        """Print a themed warning / informational message.

        Parameters
        ----------
        message : str or I18nKey
            Warning text or i18n key.
        **kwargs
            Format arguments for the message.

        Returns
        -------
        None

        Examples
        --------
        >>> from tetodl.utils.console import console
        >>> console.warn("Disk space is low.")

        See Also
        --------
        ok : Success-level output.
        err : Error-level output.
        """
        self._print(self.theme.warn, self.theme.warn_color, message, **kwargs)
 
    def err(self, message: str | I18nKey, **kwargs):
        """Print a themed error message.

        Parameters
        ----------
        message : str or I18nKey
            Error text or i18n key.
        **kwargs
            Format arguments for the message.

        Returns
        -------
        None

        Examples
        --------
        >>> from tetodl.utils.console import console
        >>> console.err("Connection failed.")

        See Also
        --------
        warn : Warning-level output.
        panic : Fatal error that terminates the process.
        """
        self._print(self.theme.err, self.theme.err_color, message, **kwargs)
       
    def proc(self, message: str | I18nKey, **kwargs):
        """Print a themed in-progress / info message.

        Parameters
        ----------
        message : str or I18nKey
            Process text or i18n key.
        **kwargs
            Format arguments for the message.

        Returns
        -------
        None

        Examples
        --------
        >>> from tetodl.utils.console import console
        >>> console.proc("Processing track 4 of 12...")

        See Also
        --------
        ok : Success-level output.
        spin : Animated spinner for long-running operations.
        """
        self._print(self.theme.proc, self.theme.proc_color, message, **kwargs)

    @deprecated("Use trace() and traced() instead.")
    def debug(self, message: str | I18nKey, **kwargs):
        """Print a debug-level message.

        Only visible when debug mode is active (see
        :func:`~tetodl.utils.logger.set_debug`).  **Not** suppressed
        by ``is_quiet`` — combine ``--quiet --debug`` to see debug
        output alone.

        Parameters
        ----------
        message : str or I18nKey
            Debug text or i18n key.
        **kwargs
            Format arguments for the message.

        Returns
        -------
        None

        Examples
        --------
        >>> from tetodl.utils.console import console
        >>> from tetodl.utils.logger import set_debug
        >>> set_debug("all")
        >>> console.debug("Entered download loop.")

        See Also
        --------
        set_debug : Global function that enables / disables debug mode.
        """
        if not self.state.is_debug:
            return
        text = self._resolve_text(message, **kwargs)
        final_output = (
            f"{self.theme.debug_color}{self.theme.debug}{self.theme.reset_color} "
            f"{self.theme.text_color}{text}{self.theme.reset_color}"
        )
        print(final_output)

    def neutral(self, message: str | I18nKey, **kwargs):
        """Print a neutral, un-themed message.

        Uses the ``exit`` symbol rendered in the default text colour,
        making it suitable for informational lines that should not carry
        a semantic colour.

        Parameters
        ----------
        message : str or I18nKey
            Neutral text or i18n key.
        **kwargs
            Format arguments for the message.

        Returns
        -------
        None

        Examples
        --------
        >>> from tetodl.utils.console import console
        >>> console.neutral("No changes detected.")

        See Also
        --------
        ok : Themed success output.
        """
        self._print(self.theme.exit, self.theme.text_color, message, **kwargs)

    def exit(self, message: str | I18nKey = "Exiting...", **kwargs):
        """Print an exit message and terminate the process with code 0.

        Parameters
        ----------
        message : str or I18nKey, optional
            Exit text or i18n key.  Defaults to ``"Exiting..."``.
        **kwargs
            Format arguments for the message.

        Returns
        -------
        NoReturn
            This method does not return — it calls :func:`sys.exit`.

        Raises
        ------
        SystemExit
            Always raised with status code 0.

        Examples
        --------
        >>> from tetodl.utils.console import console
        >>> console.exit("Goodbye.")

        See Also
        --------
        panic : Fatal exit with code 1.
        """
        self._print(self.theme.exit, self.theme.exit_color, message, **kwargs)
        sys.exit(0)

    def panic(self, message: str | I18nKey, **kwargs):
        """Print a fatal error message and terminate with code 1.

        The message is rendered in bright panic colours and is **not**
        suppressed by the ``is_quiet`` flag.

        Parameters
        ----------
        message : str or I18nKey
            Fatal error text or i18n key.
        **kwargs
            Format arguments for the message.

        Returns
        -------
        NoReturn
            This method does not return — it calls :func:`sys.exit`.

        Raises
        ------
        SystemExit
            Always raised with status code 1.

        Examples
        --------
        >>> from tetodl.utils.console import console
        >>> console.panic("Unexpected error during startup.")

        See Also
        --------
        exit : Graceful exit with code 0.
        err : Non-fatal error output.
        """
        text = self._resolve_text(message, **kwargs)
        print(f"{self.theme.panic_color}{self.theme.panic} {text}{self.theme.reset_color}")
        sys.exit(1)