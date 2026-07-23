"""
Advanced tracing system: ``@trace`` decorator, ``traced()`` context manager,
and ``TraceStore`` accumulator.

See ``refactor/ADV_LOGGING.md`` for the full architecture specification.

For related logging functionality see :mod:`tetodl.utils.logger`.
"""

import functools
import inspect
import threading
import time
import traceback as tbmod
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, ParamSpec, TypeVar, cast

from .logger import get_debug_mode, is_debug

__all__ = [
    "TraceEntry",
    "TraceStore",
    "get_trace_store",
    "set_dump_path",
    "trace",
    "traced",
]


P = ParamSpec("P")
R = TypeVar("R")

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

TraceKind = Literal["CALL", "RETURN", "EXCEPTION", "CONTEXT"]


@dataclass
class TraceEntry:
    """A single trace event recorded by ``@trace`` or ``traced()``.

    Each entry captures a snapshot of a traced function call (entry, return,
    or exception) or a user-defined context annotation at the moment it
    occurs.

    Parameters
    ----------
    kind : TraceKind
        Event category.
    timestamp : float
        Value of ``time.perf_counter()`` at the moment of recording.
    thread_id : int
        Result of ``threading.get_ident()``.
    module : str
        Dotted module path of the traced function (``tetodl.`` prefix stripped).
    name : str
        ``__qualname__`` of the traced function.
    depth : int
        Current call-stack depth at the time of recording.
    args : dict, optional
        Snapshot of argument reprs (``CALL`` entries only).
    result : str, optional
        Return-value repr (``RETURN`` entries only).
    exception : str, optional
        Exception repr (``EXCEPTION`` entries only).
    traceback : str, optional
        Compact traceback (``EXCEPTION`` entries only).
    duration : float, optional
        Wall-clock duration in seconds (``RETURN`` / ``EXCEPTION`` entries).
    context_msg : str, optional
        User-provided label (``CONTEXT`` entries only).

    See Also
    --------
    :func:`trace` : Decorator that produces CALL / RETURN / EXCEPTION entries.
    :func:`traced` : Context manager that produces CONTEXT entries.
    :class:`TraceStore` : Accumulator that stores and dumps entries.

    Examples
    --------
    >>> entry = TraceEntry(
    ...     kind="CALL",
    ...     timestamp=9.0,
    ...     thread_id=1,
    ...     module="utils.fetcher",
    ...     name="Fetcher.fetch",
    ...     depth=2,
    ...     args={"url": "'https://example.com'"},
    ... )
    >>> entry.kind
    'CALL'
    """

    kind: TraceKind
    timestamp: float
    thread_id: int
    module: str
    name: str
    depth: int

    args: dict | None = None
    result: str | None = None
    exception: str | None = None
    traceback: str | None = None
    duration: float | None = None
    context_msg: str | None = None


# ---------------------------------------------------------------------------
# TraceStore — bounded, thread-safe accumulator
# ---------------------------------------------------------------------------

_MAX_ENTRIES = 5000


class TraceStore:
    """Structured, bounded accumulator of :class:`TraceEntry` objects.

    Entries are pushed by ``@trace`` and ``traced()``.  The store can be
    dumped to a human-readable ``.log`` file or a ``.json`` array for
    post-mortem analysis.

    The store is thread-safe and auto-prunes the oldest entries when the
    internal buffer exceeds ``5000`` records.

    Parameters
    ----------
    renderer : callable, optional
        A ``callable(str)`` invoked for each entry that passes the current
        ``--debug`` mode filter.  Typically ``console.debug``.

    See Also
    --------
    :func:`trace` : Decorator that pushes CALL / RETURN / EXCEPTION entries.
    :func:`traced` : Context manager that pushes CONTEXT entries.
    :func:`get_trace_store` : Obtain the global singleton store.

    Examples
    --------
    >>> store = TraceStore()
    >>> store.record(TraceEntry(
    ...     kind="CALL", timestamp=0.0, thread_id=1,
    ...     module="mod", name="fn", depth=0))
    >>> len(store.entries)
    1
    >>> store.dump("/tmp/trace.log")  # doctest: +SKIP
    """

    def __init__(self, renderer: Callable[[str], None] | None = None) -> None:
        self._entries: list[TraceEntry] = []
        self._lock = threading.Lock()
        self._renderer = renderer
        self._depth: int = 0
        self._dump_path: Path | None = None
        self._atexit_done: bool = False

    # -- properties ---------------------------------------------------------

    @property
    def entries(self) -> list[TraceEntry]:
        """Return a snapshot of all recorded entries."""
        with self._lock:
            return list(self._entries)

    @property
    def depth(self) -> int:
        """Current call-stack depth."""
        return self._depth

    # -- mutation -----------------------------------------------------------

    def record(self, entry: TraceEntry) -> None:
        """Append *entry* and auto-prune the oldest when at capacity.

        Parameters
        ----------
        entry : TraceEntry
            The trace event to store.

        Returns
        -------
        None

        See Also
        --------
        :meth:`TraceStore.clear` : Remove all entries.
        :meth:`TraceStore.last` : Retrieve the most recent entries.
        :meth:`TraceStore.filter` : Query entries by criteria.

        Examples
        --------
        >>> store = TraceStore()
        >>> entry = TraceEntry(
        ...     kind="CALL", timestamp=0.0, thread_id=1,
        ...     module="mod", name="fn", depth=0)
        >>> store.record(entry)
        >>> len(store.entries)
        1
        """
        with self._lock:
            self._entries.append(entry)
            if len(self._entries) > _MAX_ENTRIES:
                self._entries.pop(0)

    def clear(self) -> None:
        """Remove all recorded entries from the store.

        Returns
        -------
        None

        See Also
        --------
        :meth:`TraceStore.record` : Add a new entry.

        Examples
        --------
        >>> store = TraceStore()
        >>> store.record(TraceEntry(
        ...     kind="CALL", timestamp=0.0, thread_id=1,
        ...     module="mod", name="fn", depth=0))
        >>> len(store.entries)
        1
        >>> store.clear()
        >>> len(store.entries)
        0
        """
        with self._lock:
            self._entries.clear()

    # -- queries ------------------------------------------------------------

    def last(self, n: int = 10) -> list[TraceEntry]:
        """Return the *n* most recent entries.

        Parameters
        ----------
        n : int
            Number of entries to return (default ``10``).

        Returns
        -------
        list[TraceEntry]
            A shallow copy of the trailing *n* entries, in recording order.

        See Also
        --------
        :meth:`TraceStore.filter` : Query entries by kind or module.
        :meth:`TraceStore.entries` : Snapshot of all entries.

        Examples
        --------
        >>> store = TraceStore()
        >>> for i in range(3):
        ...     store.record(TraceEntry(
        ...         kind="CALL", timestamp=float(i),
        ...         thread_id=1, module="mod", name="fn", depth=0))
        >>> len(store.last(2))
        2
        """
        with self._lock:
            return list(self._entries[-n:])

    def filter(
        self,
        *,
        kind: TraceKind | None = None,
        module: str | None = None,
    ) -> list[TraceEntry]:
        """Return entries matching the given criteria.

        Parameters
        ----------
        kind : TraceKind, optional
            If given, only entries of this kind are returned.
        module : str, optional
            If given, only entries whose ``module`` field equals or is a
            subpackage of *module* are returned.

        Returns
        -------
        list[TraceEntry]
            Filtered list of matching entries in recording order.

        See Also
        --------
        :meth:`TraceStore.last` : Retrieve the most recent entries.
        :meth:`TraceStore.entries` : Snapshot of all entries.

        Examples
        --------
        >>> store = TraceStore()
        >>> store.record(TraceEntry(
        ...     kind="CALL", timestamp=0.0, thread_id=1,
        ...     module="mod.sub", name="fn", depth=0))
        >>> store.record(TraceEntry(
        ...     kind="RETURN", timestamp=1.0, thread_id=1,
        ...     module="mod.sub", name="fn", depth=0))
        >>> len(store.filter(kind="CALL"))
        1
        >>> len(store.filter(module="mod"))
        2
        """
        result = list(self._entries)
        if kind:
            result = [e for e in result if e.kind == kind]
        if module:
            result = [
                e
                for e in result
                if e.module == module or e.module.startswith(module + ".")
            ]
        return result

    # -- depth tracking -----------------------------------------------------

    def push_depth(self) -> None:
        """Increment the internal call-stack depth counter.

        Called automatically by the ``@trace`` wrapper when entering a
        traced function.

        Returns
        -------
        None

        See Also
        --------
        :meth:`TraceStore.pop_depth` : Decrement the depth counter.

        Examples
        --------
        >>> store = TraceStore()
        >>> store.depth
        0
        >>> store.push_depth()
        >>> store.depth
        1
        """
        self._depth += 1

    def pop_depth(self) -> None:
        """Decrement the internal call-stack depth counter.

        Called automatically by the ``@trace`` wrapper when leaving a
        traced function.  The counter is clamped at zero.

        Returns
        -------
        None

        See Also
        --------
        :meth:`TraceStore.push_depth` : Increment the depth counter.

        Examples
        --------
        >>> store = TraceStore()
        >>> store.push_depth()
        >>> store.push_depth()
        >>> store.depth
        2
        >>> store.pop_depth()
        >>> store.depth
        1
        """
        self._depth = max(0, self._depth - 1)

    # -- dump ---------------------------------------------------------------

    def dump(self, path: str | Path) -> None:
        """Write a human-readable trace log.

        Parameters
        ----------
        path : str or Path
            Destination file path.  Parent directories are created if needed.

        Returns
        -------
        None

        Raises
        ------
        OSError
            If the file cannot be opened or written to.

        See Also
        --------
        :meth:`TraceStore.dump_json` : Write entries as a JSON array.
        :meth:`TraceStore.enable_auto_dump` : Register an atexit dump.

        Examples
        --------
        >>> store = TraceStore()
        >>> store.record(TraceEntry(
        ...     kind="CALL", timestamp=0.0, thread_id=1,
        ...     module="mod", name="fn", depth=0))
        >>> store.dump("/tmp/trace.log")  # doctest: +SKIP
        """
        import datetime as dt

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write(
                f"TetoDL Trace — {dt.datetime.now().isoformat()}\n"
                f"{'TYPE':<10} {'FUNCTION / CONTEXT':<50} "
                f"{'ARGS / RESULT':<50} {'DURATION':<10}\n"
                f"{'─' * 120}\n"
            )
            for e in self._entries:
                self._write_dump_line(f, e)

    def dump_json(self, path: str | Path) -> None:
        """Write a JSON array of trace entries.

        Parameters
        ----------
        path : str or Path
            Destination file path.  Parent directories are created if needed.

        Returns
        -------
        None

        Raises
        ------
        OSError
            If the file cannot be opened or written to.

        See Also
        --------
        :meth:`TraceStore.dump` : Write a human-readable trace log.
        :meth:`TraceStore.enable_auto_dump` : Register an atexit dump.

        Examples
        --------
        >>> store = TraceStore()
        >>> store.record(TraceEntry(
        ...     kind="CALL", timestamp=0.0, thread_id=1,
        ...     module="mod", name="fn", depth=0))
        >>> store.dump_json("/tmp/trace.json")  # doctest: +SKIP
        """
        import json

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        data: list[dict[str, Any]] = []
        for e in self._entries:
            d: dict[str, Any] = {
                "kind": e.kind,
                "timestamp": e.timestamp,
                "thread_id": e.thread_id,
                "module": e.module,
                "name": e.name,
                "depth": e.depth,
            }
            for attr in ("args", "result", "exception", "traceback", "context_msg"):
                val = getattr(e, attr, None)
                if val is not None:
                    d[attr] = val
            if e.duration is not None:
                d["duration"] = round(e.duration, 4)
            data.append(d)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

    # -- auto-dump ---------------------------------------------------------

    def enable_auto_dump(self, path: str | Path | None = None) -> None:
        """Register an ``atexit`` handler that dumps trace entries to *path*.

        Parameters
        ----------
        path : str or Path, optional
            Destination file path.  When ``None`` a default name
            ``tetodl_trace_<timestamp>.log`` is used in the current
            working directory.

        Returns
        -------
        None

        See Also
        --------
        :meth:`TraceStore.dump` : Manually write a trace log.
        :meth:`TraceStore.dump_json` : Manually write a JSON trace.

        Examples
        --------
        >>> store = TraceStore()
        >>> store.enable_auto_dump("/tmp/auto_trace.log")
        """
        if path:
            self._dump_path = Path(path)
        if not self._dump_path:
            import datetime as dt
            ts = dt.datetime.now().strftime('%Y%m%d_%H%M%S')
            self._dump_path = Path(f'tetodl_trace_{ts}.log')
        self._register_atexit()

    def _register_atexit(self) -> None:
        """Register the ``atexit`` dump handler if not already registered."""
        if self._atexit_done:
            return
        import atexit
        atexit.register(self._auto_dump)
        self._atexit_done = True

    def _auto_dump(self) -> None:
        """``atexit`` callback that flushes entries to the dump path."""
        if self._dump_path and self._entries:
            self.dump(self._dump_path)

    # -- internal helpers ---------------------------------------------------

    @staticmethod
    def _write_dump_line(f: Any, e: TraceEntry) -> None:
        """Write a single formatted line of the human-readable dump."""
        kind_pad = f"[{e.kind}]".ljust(8)
        if e.kind == "CALL":
            args_str = _safe_repr(e.args, 80) if e.args else ""
            f.write(f"{kind_pad} {e.name:<50} ({args_str}){'':>10}\n")
        elif e.kind == "RETURN":
            res = _safe_repr(e.result, 80) if e.result is not None else "None"
            dur = f"{e.duration:.2f}s" if e.duration is not None else ""
            f.write(f"{kind_pad} {e.name:<50} -> {res:<46} {dur:<10}\n")
        elif e.kind == "EXCEPTION":
            dur = f"{e.duration:.2f}s" if e.duration is not None else ""
            f.write(
                f"{kind_pad} {e.name:<50} X {e.exception or '':<46} {dur:<10}\n"
            )
        elif e.kind == "CONTEXT":
            f.write(f"{'  |':<8} {e.context_msg or '':<50}\n")


# ---------------------------------------------------------------------------
# Safe repr  (never raises)
# ---------------------------------------------------------------------------

def _safe_repr(obj: Any, max_len: int = 200) -> str:
    """Return ``repr(obj)`` truncated, or ``<repr error>`` on failure."""
    try:
        s = repr(obj)
    except Exception:
        return "<repr error>"
    if len(s) > max_len:
        s = s[:max_len] + "..."
    return s


# ---------------------------------------------------------------------------
# Global store (lazy-init) + auto-dump path
# ---------------------------------------------------------------------------

_store: TraceStore | None = None
_dump_path: Path | None = None


def _get_store() -> TraceStore:
    """Return the global ``TraceStore``, creating it on first access."""
    global _store
    if _store is None:
        from .console import console as _con

        _store = TraceStore(renderer=_con.debug)
        if _dump_path:
            _store._dump_path = _dump_path
            _store._register_atexit()
    return _store


def _short_module(module: str) -> str:
    """Strip leading ``tetodl.`` from a dotted module path."""
    return module.removeprefix("tetodl.")


# ---------------------------------------------------------------------------
# Console formatting
# ---------------------------------------------------------------------------

def _format_timestamp(ts: float) -> str:
    """Format a ``perf_counter`` float as ``HH:MM:SS.mmm``."""
    secs = int(ts)
    millis = int((ts - secs) * 1000)
    return f"{time.strftime('%H:%M:%S', time.localtime(secs))}.{millis:03d}"


def _format_call_args(args: dict) -> str:
    """Render a dict of arg-name → repr as a compact comma-separated string."""
    parts: list[str] = []
    for k, v in args.items():
        parts.append(f"{k}={v}")
    return ", ".join(parts)


def _format_entry(entry: TraceEntry) -> str:
    """Format a :class:`TraceEntry` as a single-line console string."""
    ts = _format_timestamp(entry.timestamp)

    if entry.kind == "CALL":
        args_str = _format_call_args(entry.args) if entry.args else ""
        return f"{ts} >>> {entry.name}({args_str})"

    if entry.kind == "RETURN":
        res = entry.result if entry.result is not None else "None"
        dur = f" ({entry.duration:.2f}s)" if entry.duration is not None else ""
        return f"{ts} <<< {entry.name} -> {res}{dur}"

    if entry.kind == "EXCEPTION":
        dur = f" ({entry.duration:.2f}s)" if entry.duration is not None else ""
        return f"{ts} !!! {entry.name} -> {entry.exception}{dur}"

    if entry.kind == "CONTEXT":
        return f"{ts}   | {entry.context_msg or ''}"

    return ""


def _should_display(entry: TraceEntry) -> bool:
    """Check whether *entry* passes the active ``--debug`` mode filter."""
    mode = get_debug_mode()
    if mode == "all":
        return True
    if mode == "errors":
        return entry.kind == "EXCEPTION"
    if mode == "concise":
        return entry.kind in ("CALL", "RETURN", "EXCEPTION")
    return False  # unknown mode, be safe


# ---------------------------------------------------------------------------
# @trace decorator
# ---------------------------------------------------------------------------

def trace(
    func: Callable[P, R] | None = None,
    *,
    show_args: bool = True,
    show_result: bool = True,
    max_len: int = 200,
) -> Callable[..., R]:
    """Decorator that auto-logs function entry, return, exception and duration.

    When ``--debug`` is **off** the wrapper collapses to a plain call
    with zero overhead.

    Parameters
    ----------
    func : Callable, optional
        Function to decorate.  When ``None`` (``@trace(...)`` with
        parentheses), returns a decorator.
    show_args : bool
        Include argument values in traces (default ``True``).
    show_result : bool
        Include return value in traces (default ``True``).
    max_len : int
        Truncate repr strings longer than this (default ``200``).

    Returns
    -------
    Callable[..., R]
        The wrapped function (or a decorator factory when *func* is
        ``None``).

    Raises
    ------
    No explicit exceptions are raised; all tracing failures are silently
    caught so that the decorated function always executes normally.

    See Also
    --------
    :func:`traced` : Context manager for inline CONTEXT entries.
    :class:`TraceStore` : Accumulator that stores and dumps entries.
    :func:`get_trace_store` : Access the global trace store.
    :func:`set_dump_path` : Configure auto-dump before first trace.

    Examples
    --------
    Basic usage --- decorate a function:

    >>> @trace
    ... def fetch_metadata(artist, title):
    ...     return {"artist": artist, "title": title}

    With configuration:

    >>> @trace(show_args=False, max_len=100)
    ... def download(url):
    ...     ...

    Notes
    -----
    The decorator is **safe** --- if its own tracing logic raises (broken
    ``repr``, etc.), the error is silently caught and the original
    function is called normally.
    """
    if func is not None:
        return cast(Callable[..., R], _make_trace_wrapper(func, show_args, show_result, max_len))

    def decorator(f: Callable[P, R]) -> Callable[P, R]:
        return _make_trace_wrapper(f, show_args, show_result, max_len)

    return cast(Callable[..., R], decorator)


def _make_trace_wrapper(
    func: Callable[P, R],
    show_args: bool,
    show_result: bool,
    max_len: int,
) -> Callable[P, R]:
    """Build the actual wrapper closure around *func*."""
    module = _short_module(func.__module__)
    qualname = func.__qualname__

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> R:
        if not is_debug():
            return func(*args, **kwargs)

        store = _get_store()
        ts_start = time.perf_counter()
        thread_id = threading.get_ident()
        depth = store.depth

        # CALL entry
        call_args: dict | None = None
        if show_args:
            try:
                call_args = _capture_args(func, args, kwargs)
            except Exception:
                call_args = {"<error>": "args capture failed"}

        call_entry = TraceEntry(
            kind="CALL",
            timestamp=ts_start,
            thread_id=thread_id,
            module=module,
            name=qualname,
            depth=depth,
            args=call_args,
        )
        store.record(call_entry)
        if _should_display(call_entry) and store._renderer is not None:
            store._renderer(_format_entry(call_entry))

        store.push_depth()

        try:
            result = func(*args, **kwargs)
        except BaseException as exc:
            ts_end = time.perf_counter()
            store.pop_depth()

            exc_entry = TraceEntry(
                kind="EXCEPTION",
                timestamp=ts_end,
                thread_id=thread_id,
                module=module,
                name=qualname,
                depth=depth,
                exception=_safe_repr(exc, max_len),
                traceback=_capture_traceback(),
                duration=ts_end - ts_start,
            )
            store.record(exc_entry)
            if _should_display(exc_entry) and store._renderer is not None:
                store._renderer(_format_entry(exc_entry))
            raise

        ts_end = time.perf_counter()
        store.pop_depth()

        # RETURN entry
        ret_str: str | None = _safe_repr(result, max_len) if show_result else None

        ret_entry = TraceEntry(
            kind="RETURN",
            timestamp=ts_end,
            thread_id=thread_id,
            module=module,
            name=qualname,
            depth=depth,
            result=ret_str,
            duration=ts_end - ts_start,
        )
        store.record(ret_entry)
        if _should_display(ret_entry) and store._renderer is not None:
            store._renderer(_format_entry(ret_entry))

        return result

    return wrapper


def _capture_args(
    func: Callable, args: tuple[Any, ...], kwargs: dict[str, Any]
) -> dict[str, str]:
    """Build a repr-snapshot dict of call arguments, skipping ``self``/``cls``."""
    try:
        sig = inspect.signature(func)
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()
    except (ValueError, TypeError):
        return {"<unbound>": _safe_repr((args, kwargs), 200)}

    result: dict[str, str] = {}
    for name, value in bound.arguments.items():
        if name in ("self", "cls"):
            continue
        result[name] = _safe_repr(value, 200)
    return result


def _capture_traceback() -> str:
    """Return a compact traceback string for the current exception context."""
    import sys as _sys

    try:
        exc_info = _sys.exc_info()
        if exc_info[2] is None:
            return ""
        frames = tbmod.extract_tb(exc_info[2], limit=4)
        if not frames:
            return ""
        return "".join(tbmod.format_list(frames))
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# traced() context manager
# ---------------------------------------------------------------------------

@contextmanager
def traced(message: str) -> Iterator[None]:
    """Context manager that records a ``CONTEXT`` trace entry.

    Use inside a ``@trace``-d function to document branch decisions
    without adding inline ``console.debug()`` calls.

    Parameters
    ----------
    message : str
        Descriptive label shown in the trace output.

    Yields
    ------
    None
        The context manager yields, allowing the wrapped block to execute.

    Raises
    ------
    No explicit exceptions are raised; all tracing failures are silently
    caught so that the wrapped code always executes normally.

    See Also
    --------
    :func:`trace` : Decorator that produces CALL / RETURN / EXCEPTION entries.
    :class:`TraceStore` : Accumulator that stores and dumps entries.
    :func:`get_trace_store` : Access the global trace store.

    Examples
    --------
    >>> @trace
    ... def process_cover(artist, title):
    ...     with traced("smart download"):
    ...         path = "/tmp/cover.jpg"
    ...     if not path:
    ...         with traced("fallback to thumbnail"):
    ...             path = "/tmp/thumb.jpg"
    ...     return path

    Notes
    -----
    When ``--debug`` is off the context manager is a no-op with zero overhead.
    """
    if not is_debug():
        yield
        return

    store = _get_store()
    ts = time.perf_counter()
    thread_id = threading.get_ident()
    depth = store.depth

    entry = TraceEntry(
        kind="CONTEXT",
        timestamp=ts,
        thread_id=thread_id,
        module="",
        name="",
        depth=depth,
        context_msg=message,
    )
    store.record(entry)
    if _should_display(entry) and store._renderer is not None:
        store._renderer(_format_entry(entry))

    yield


# ---------------------------------------------------------------------------
# Convenience accessor
# ---------------------------------------------------------------------------

def get_trace_store() -> TraceStore | None:
    """Return the global :class:`TraceStore` instance, or ``None`` if empty.

    The store is lazily created on first call to ``@trace`` or ``traced()``,
    so this function returns ``None`` if no traced code has executed yet
    in the current process.

    Returns
    -------
    TraceStore or None
        The global singleton store, or ``None`` if not yet initialised.

    See Also
    --------
    :class:`TraceStore` : The accumulator class.
    :func:`trace` : Decorator that populates the store.
    :func:`set_dump_path` : Configure auto-dump path.

    Examples
    --------
    >>> store = get_trace_store()
    >>> if store is not None:
    ...     print(len(store.entries))
    """
    return _store


def set_dump_path(path: str | Path | None = None) -> None:
    """Set default dump path and enable auto-dump at exit.

    Parameters
    ----------
    path : str or Path, optional
        Destination file path.  When ``None`` a default name
        ``tetodl_trace_<timestamp>.log`` is generated in CWD.

    Returns
    -------
    None

    See Also
    --------
    :meth:`TraceStore.enable_auto_dump` : Instance-level equivalent.
    :meth:`TraceStore.dump` : Manually write a trace log.
    :meth:`TraceStore.dump_json` : Manually write a JSON trace.

    Examples
    --------
    >>> set_dump_path("/tmp/trace.log")  # doctest: +SKIP

    Notes
    -----
    This must be called **before** any ``@trace``\\ d function runs so
    the path is picked up when the global ``TraceStore`` is created.
    Safe to call multiple times — ``atexit`` handler is registered only
    once.
    """
    global _dump_path
    if path:
        _dump_path = Path(path)
    else:
        import datetime as dt
        ts = dt.datetime.now().strftime('%Y%m%d_%H%M%S')
        _dump_path = Path(f'tetodl_trace_{ts}.log')
    store = _get_store()
    store._dump_path = _dump_path
    store._register_atexit()
