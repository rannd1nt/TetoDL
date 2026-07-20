"""
Global debug flag, debug mode, and ``@debug`` decorator for pytest.

See ``refactor/ADV_LOGGING.md`` for the full architecture specification.
"""

import functools
from typing import Callable, ParamSpec, TypeVar, cast

P = ParamSpec("P")
R = TypeVar("R")

_DEBUG_ENABLED: bool = False
_DEBUG_MODE: str = "all"


def set_debug(enabled: bool | str) -> None:
    """Enable or disable debug logging globally.

    When *enabled* is a string, debug mode is turned on with that mode.
    When *enabled* is ``True``, ``'all'`` mode is used.
    When *enabled* is ``False``, debug mode is turned off.

    Parameters
    ----------
    enabled : bool or str
        - ``True`` — enable debug output in ``'all'`` mode.
        - ``'all'`` — enable all traces.
        - ``'errors'`` — enable, only exceptions shown on console.
        - ``'concise'`` — enable, only entry/exit shown on console.
        - ``False`` — disable debug output.
    """
    global _DEBUG_ENABLED, _DEBUG_MODE

    if isinstance(enabled, str):
        _DEBUG_ENABLED = True
        _DEBUG_MODE = enabled
    elif enabled:
        _DEBUG_ENABLED = True
        _DEBUG_MODE = "all"
    else:
        _DEBUG_ENABLED = False
        _DEBUG_MODE = "all"

    from .console import console as _con

    _con.state.is_debug = _DEBUG_ENABLED
    _con.state.debug_mode = _DEBUG_MODE


def is_debug() -> bool:
    """Check whether debug mode is currently active.

    Returns
    -------
    bool
        ``True`` if debug mode was activated (via subcommand, ``--debug`` flag,
        or the ``@debug`` decorator).
    """
    return _DEBUG_ENABLED


def get_debug_mode() -> str:
    """Return the current debug mode string.

    Returns
    -------
    str
        One of ``'all'``, ``'errors'``, or ``'concise'``.
        Always ``'all'`` when debug is disabled.
    """
    return _DEBUG_MODE


def debug(
    func: Callable[P, R] | None = None,
    *,
    dump_path: str | None = None,
) -> Callable[..., R]:
    """Decorator for pytest test functions to enable debug logging.

    When applied, all ``@trace`` decorators and ``traced()`` context managers
    inside the decorated test will produce visible output.  The previous
    debug state is restored after the test finishes.

    This decorator has **no effect in production code** — use the
    ``debug`` CLI subcommand (``tetodl debug all ...``) instead.

    Parameters
    ----------
    func : Callable[P, R], optional
        Test function to wrap.  When ``None`` the decorator is called
        with keyword arguments (``@debug(dump_path=...)``).
    dump_path : str, optional
        If given, trace entries are dumped to this file path on test
        completion via ``atexit``.  A default name
        ``tetodl_trace_<timestamp>.log`` is used when omitted.

    Returns
    -------
    Callable[..., R]
        Wrapped test function.

    Examples
    --------
    >>> from tetodl.utils.logger import debug
    >>>
    >>> @debug
    ... def test_something():
    ...     ...
    >>>
    >>> @debug(dump_path="tests/_results/test_something.log")
    ... def test_with_dump():
    ...     ...
    """

    def decorator(f: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(f)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            previous = is_debug()
            previous_mode = get_debug_mode()
            set_debug("all")
            if dump_path:
                from tetodl.utils.tracer import set_dump_path
                set_dump_path(dump_path)
            try:
                return f(*args, **kwargs)
            finally:
                if previous:
                    set_debug(previous_mode)
                else:
                    set_debug(False)
        return wrapper

    if func is not None:
        return cast(Callable[..., R], decorator(func))
    return cast(Callable[..., R], decorator)
