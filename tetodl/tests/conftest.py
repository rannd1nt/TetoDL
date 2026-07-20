"""
Shared test fixtures for TetoDL.

All fixtures in this file are auto-discovered by pytest.  Sub-package
``conftest.py`` files may add more-specific fixtures.

The :mod:`tetodl.tests.plugin` module is registered here, integrating
TetoDL's own ``@trace`` / ``traced()`` / ``console.debug()`` framework
into pytest — see ``--tetodl-trace`` CLI flag.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, Iterator

import pytest

from tetodl.core.models import (
    AppConfig,
    DownloadSession,
    PipelineContext,
    SessionOverrides,
)

# Register the TetoDL pytest plugin
pytest_plugins = ["tetodl.tests.plugin"]

# ---------------------------------------------------------------------------
# Temporary directory / file fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_config_dir(tmp_path: Path) -> Path:
    """Return a temporary directory that simulates ``~/.config/tetodl``."""
    d = tmp_path / "config"
    d.mkdir(parents=True, exist_ok=True)
    return d


@pytest.fixture
def tmp_data_dir(tmp_path: Path) -> Path:
    """Return a temporary directory that simulates data storage."""
    d = tmp_path / "data"
    d.mkdir(parents=True, exist_ok=True)
    return d


@pytest.fixture
def temp_file(tmp_path: Path) -> Iterator[Path]:
    """Yield a temporary file path and clean up afterward."""
    f = tmp_path / "temp_file.tmp"
    f.write_text("test content")
    yield f
    if f.exists():
        f.unlink()


# ---------------------------------------------------------------------------
# Config / state fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def app_config() -> AppConfig:
    """Return a default :class:`AppConfig` with no overrides."""
    return AppConfig()


@pytest.fixture
def session_overrides() -> SessionOverrides:
    """Return a default (all-None) :class:`SessionOverrides`."""
    return SessionOverrides()


@pytest.fixture
def audio_session() -> DownloadSession:
    """Return a :class:`DownloadSession` configured for audio download."""
    return DownloadSession(
        url="https://music.youtube.com/watch?v=dQw4w9WgXcQ",
        media_type="audio",
    )


@pytest.fixture
def video_session() -> DownloadSession:
    """Return a :class:`DownloadSession` configured for video download."""
    return DownloadSession(
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        media_type="video",
    )


@pytest.fixture
def thumbnail_session() -> DownloadSession:
    """Return a :class:`DownloadSession` configured for thumbnail-only."""
    return DownloadSession(
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        media_type="thumbnail",
    )


# ---------------------------------------------------------------------------
# Pipeline context fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def pipeline_ctx(app_config: AppConfig) -> PipelineContext:
    """Return a minimal :class:`PipelineContext` ready for a single run."""
    return PipelineContext(
        url="https://music.youtube.com/watch?v=dQw4w9WgXcQ",
        media_type="audio",
        config=app_config,
        target_dir=str(Path(tempfile.gettempdir()) / "tetodl_test"),
        is_youtube_music=True,
    )


# ---------------------------------------------------------------------------
# JSON config file helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_config_json() -> dict[str, Any]:
    """Return a dict matching the structure of a real ``config.json``."""
    return {
        "music_root": "/tmp/tetodl/music",
        "video_root": "/tmp/tetodl/video",
        "simple_mode": False,
        "smart_cover_mode": True,
        "skip_existing_files": True,
        "max_video_resolution": "720p",
        "audio_quality": "m4a",
        "video_container": "mp4",
        "language": "en",
        "media_scanner_enabled": False,
        "verified_dependencies": False,
    }


@pytest.fixture
def write_sample_config(
    tmp_config_dir: Path, sample_config_json: dict[str, Any]
) -> Path:
    """Write *sample_config_json* to a real temp file and return the path.

    The caller is responsible for patching ``tetodl.constants.CONFIG_PATH``
    if needed.
    """
    config_path = tmp_config_dir / "config.json"
    config_path.write_text(json.dumps(sample_config_json, indent=2))
    return config_path


# ---------------------------------------------------------------------------
# TetoDL tracing integration fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tetodl_trace(request: pytest.FixtureRequest):
    """Wrap the test body in a ``traced()`` block from TetoDL's tracer.

    The context label is derived from the test's ``nodeid`` so that trace
    entries are easily attributable to a specific test.

    This fixture is **auto-used** only when ``--tetodl-trace`` is active.
    A specific test can force it via ``@pytest.mark.tetodl_trace``.

    Usage
    -----
    .. code-block:: python

        def test_something(tetodl_trace):  # explicitly opt in
            ...

        @pytest.mark.tetodl_trace           # or via marker + implicit
        def test_something():
            ...

    When ``--tetodl-trace`` is passed on the CLI **every** test is wrapped
    automatically.
    """
    enabled = getattr(request.config, "_tetodl_trace_enabled", False)
    marked = request.node.get_closest_marker("tetodl_trace")
    if not (enabled or marked):
        yield
        return

    from tetodl.utils.tracer import traced

    label = request.node.nodeid
    with traced(f"pytest:{label}"):
        yield


@pytest.fixture
def tetodl_debug(request: pytest.FixtureRequest):
    """Enable ``console.debug()`` output for a specific test.

    Use this fixture on tests that exercise debug-path logic::

        def test_verbose_parsing(tetodl_debug):
            console.debug("checking URL variants...")
            ...

    The fixture respects ``--tetodl-trace`` — if the flag is *off* at the
    CLI level, this fixture is a no-op.
    """
    enabled = getattr(request.config, "_tetodl_trace_enabled", False)
    if not enabled:
        yield
        return

    from tetodl.utils.logger import set_debug, is_debug, get_debug_mode

    prev_enabled = is_debug()
    prev_mode = get_debug_mode()
    set_debug("all")
    try:
        yield
    finally:
        if prev_enabled:
            set_debug(prev_mode)
        else:
            set_debug(False)
