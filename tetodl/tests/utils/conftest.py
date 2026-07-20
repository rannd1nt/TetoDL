"""
Utils sub-package fixtures — mock network, temp media files, i18n helpers.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def sample_video_urls() -> dict[str, str]:
    """Return a dict of well-known YouTube URL variants for extraction tests."""
    return {
        "standard": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "short": "https://youtu.be/dQw4w9WgXcQ",
        "music": "https://music.youtube.com/watch?v=dQw4w9WgXcQ",
        "embed": "https://www.youtube.com/embed/dQw4w9WgXcQ",
        "shorts": "https://www.youtube.com/shorts/dQw4w9WgXcQ",
        "playlist": "https://www.youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf",
        "live": "https://www.youtube.com/watch?v=dQw4w9WgXcQ&ab_channel=RickAstleyVEVO",
    }


@pytest.fixture
def mock_console_debug(mocker: pytest.FixtureRequest) -> Any:
    """Mock ``tetodl.utils.console.console.debug`` so tests can verify calls.

    Usage::

        def test_something(mock_console_debug):
            run_some_code()
            mock_console_debug.assert_called_once_with("expected message")
    """
    return mocker.patch("tetodl.utils.console.console.debug")


@pytest.fixture
def temp_media_file(tmp_path: Path) -> Path:
    """Create a minimal fake media file (MP4-like) for pipeline tests."""
    path = tmp_path / "test_media.mp4"
    path.write_bytes(b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42mp41")
    return path
