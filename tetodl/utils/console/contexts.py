"""
Context managers for temporary console state and loading animations.

The module provides two context managers that integrate closely with
:class:`~tetodl.utils.console.logger.Console`:

* :class:`ConsoleStateContext` -- temporarily overrides attributes on
  :class:`~tetodl.utils.console.logger.ConsoleState` (e.g. ``quiet_mode``).
* :class:`ConsoleSpinnerContext` -- runs an animated spinner in the
  terminal while a long-running operation executes.

See Also
--------
:meth:`Console.context`
:meth:`Console.spin`
"""
import sys
import time
import threading
from contextlib import AbstractContextManager

class ConsoleStateContext(AbstractContextManager):
    """Temporarily override console state attributes within a ``with`` block.

    On entry every non-empty key in *overrides* is applied to
    :attr:`Console.state <tetodl.utils.console.logger.Console.state>`;
    the original values are restored on exit.  Keys whose value is
    falsy are skipped.

    Parameters
    ----------
    console : Console
        The :class:`~tetodl.utils.console.logger.Console` instance whose
        ``state`` will be modified.
    overrides : dict
        Mapping of attribute names to temporary values.  Each key
        should match an attribute on
        :class:`~tetodl.utils.console.logger.ConsoleState`.

    Yields
    ------
    Console
        The same *console* instance, so callers can chain operations::

            with console.context(is_quiet=True) as c:
                c.proc("Silent step...")

    Examples
    --------
    >>> from tetodl.utils.console import console
    >>> with console.context(is_quiet=True):
    ...     console.warn("This will not be printed.")
    >>> console.warn("This will be printed.")

    See Also
    --------
    :meth:`Console.context`
    """
    
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
    """Animated terminal spinner synchronised with the console theme.

    Spawns a daemon thread that redraws a spinning character on
    ``stdout`` until the context exits.  The spinner is silently
    disabled when :attr:`ConsoleState.is_quiet` is ``True``.

    Parameters
    ----------
    console : Console
        The :class:`~tetodl.utils.console.logger.Console` whose theme
        is used for styling the spinner output.
    text : str
        Message displayed alongside the spinner animation.
    delay : float, optional
        Seconds between animation frames (default ``0.1``).

    Examples
    --------
    >>> console.spin("Downloading...").__enter__()

    Or more idiomatically::

        with console.spin("Processing file..."):
            time.sleep(3)

    See Also
    --------
    :meth:`Console.spin`
    """
    
    def __init__(self, console, text: str, delay: float = 0.1):
        self.console = console
        self.text = text
        self.delay = delay
        self.chars = ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"]
        self.running = False
        self.thread = None

    def _spin_loop(self):
        """Daemon thread target; writes animation frames to stdout."""
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
            
        sys.stdout.write("\r\033[K") 
        sys.stdout.flush()