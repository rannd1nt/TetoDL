"""
Daemon sub-package fixtures — test client, mock API routes, worker helpers.
"""

from __future__ import annotations

from typing import Any

import pytest


@pytest.fixture
def sample_download_request() -> dict[str, Any]:
    """Return a dict that matches the ``DownloadRequest`` schema.

    Useful for serialization/deserialization tests without coupling to
    the actual daemon model.
    """
    return {
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "media_type": "audio",
        "quality": "m4a",
        "output_dir": "/tmp/tetodl",
        "overrides": {},
    }


@pytest.fixture
def sample_preview_request() -> dict[str, Any]:
    """Return a dict that matches the ``PreviewRequest`` schema."""
    return {
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "action": "info",
    }
