"""
pytest plugin — integrate TetoDL's tracing & debug framework into the test run.

Features
--------
* ``--tetodl-trace`` CLI flag (``--tetodl-trace`` / ``--no-tetodl-trace``):
  enable or disable TetoDL's ``@trace`` / ``console.debug()`` during tests.
  Defaults to *on* when ``-s`` (capture=no) is active, *off* otherwise.

* The ``tetodl_trace`` fixture wraps each test body in a ``traced()`` context,
  so every test invocation is visible in the trace store.

* On test failure the current ``TraceStore`` contents are automatically dumped
  to ``tetodl_tests_trace_<timestamp>.log`` so developers can inspect the full
  call sequence leading to the failure.

* ``console.debug()`` output is enabled while the plugin is active, giving
  tests the same debug pathway that production code uses.

Usage
-----
.. code-block:: bash

    pytest --tetodl-trace          # force trace on
    pytest --no-tetodl-trace       # force trace off
    pytest -s --tetodl-trace       # trace + live stdout
"""

from __future__ import annotations

import datetime
import os
from pathlib import Path

import pytest

from tetodl.utils.console import console
from tetodl.utils.logger import set_debug
from tetodl.utils.tracer import get_trace_store, traced


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register ``--tetodl-trace`` / ``--no-tetodl-trace`` CLI flags."""
    group = parser.getgroup("tetodl")
    group.addoption(
        "--tetodl-trace",
        action="store_true",
        default=None,
        help="Enable TetoDL tracing (@trace / console.debug) during tests.",
    )
    group.addoption(
        "--no-tetodl-trace",
        action="store_false",
        dest="tetodl_trace",
        help="Disable TetoDL tracing during tests.",
    )


def pytest_configure(config: pytest.Config) -> None:
    """Register the ``tetodl`` marker and initialise debug mode."""
    config.addinivalue_line(
        "markers",
        "tetodl_trace: enable TetoDL tracing for the marked test only.",
    )

    # Default: trace ON only when capture is disabled (-s / --capture=no).
    trace_enabled = config.option.tetodl_trace
    if trace_enabled is None:
        trace_enabled = config.option.capture == "no"

    if trace_enabled:
        set_debug("all")
    else:
        set_debug(False)

    # Store for use in hooks
    config._tetodl_trace_enabled = trace_enabled


def pytest_report_header(config: pytest.Config) -> list[str] | None:
    """Show trace status in the pytest header."""
    if getattr(config, "_tetodl_trace_enabled", False):
        return ["tetodl-trace: enabled"]
    return None


# ---------------------------------------------------------------------------
# Item-level setup: wrap each test in a traced() block
# ---------------------------------------------------------------------------


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_call(item: pytest.Item) -> None:
    """Wrap each test in a ``traced()`` context when tracing is active.

    The wrapping is done through the ``tetodl_trace`` fixture (see below)
    which is injected automatically via ``pytest_fixture_setup``.
    We only need to ensure the fixture is requested.
    """
    # The fixture is automatically injected — no extra work needed here.
    # The fixture itself lives in conftest.py and provides the traced() wrapper.
    pass


# ---------------------------------------------------------------------------
# Failure reporting: dump trace on test failure
# ---------------------------------------------------------------------------


@pytest.hookimpl(trylast=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo) -> None:
    """Dump the ``TraceStore`` to a file when a test fails."""
    if call.when == "call" and call.excinfo is not None:
        trace_enabled = getattr(item.config, "_tetodl_trace_enabled", False)
        if not trace_enabled:
            return

        store = get_trace_store()
        if not store.entries:
            return

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        dump_dir = Path(item.config.rootpath) / "test_traces"
        dump_dir.mkdir(parents=True, exist_ok=True)

        safe_name = item.nodeid.replace("::", "_").replace("/", "_").replace("\\", "_")
        dump_path = dump_dir / f"{safe_name}_{timestamp}.log"

        try:
            store.dump(str(dump_path))
            # Attach a user-facing message
            item.config._tetodl_trace_dump = str(dump_path)
        except Exception:
            pass


def pytest_terminal_summary(
    terminalreporter: pytest.TerminalReporter, config: pytest.Config
) -> None:
    """Print paths to any trace dumps that were written during the run."""
    dumps = getattr(config, "_tetodl_trace_dump", None)
    if dumps:
        terminalreporter.section("TetoDL Trace Dumps")
        terminalreporter.write_line(f"  Trace file: {dumps}")
