"""
Pre-configured console singleton and public re-exports.

The module-level :data:`console` object is an instance of
:class:`~tetodl.utils.console.logger.Console` configured with an
auto-detected :class:`~tetodl.utils.console.themes.LogTheme` and ready
for immediate use throughout the application.

Examples
--------
>>> from tetodl.utils.console import console
>>> console.ok("Operation completed.")
"""
from .logger import Console

console = Console()
"""
    Central output interface for TetoDL.

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
    >>>
    >>> console.ok(Keys.system.ok)
    >>> with console.spin("Processing..."):
    ...     pass
"""

__all__ = ['console']