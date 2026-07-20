"""
Core sub-package fixtures — config paths, sample JSON, dependency mocks.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def sample_config_dict() -> dict[str, Any]:
    """Return a dict matching a complete ``config.json`` with defaults."""
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
def config_file(tmp_path: Path, sample_config_dict: dict[str, Any]) -> Path:
    """Write *sample_config_dict* to a temporary JSON file."""
    path = tmp_path / "config.json"
    path.write_text(json.dumps(sample_config_dict, indent=2))
    return path


@pytest.fixture
def mock_shutil_which(mocker: Any) -> Any:
    """Mock ``shutil.which`` so it returns a fake path by default.

    Tests that verify missing dependencies can override the return value::

        mock_shutil_which.return_value = None   # simulate missing binary
    """
    return mocker.patch("shutil.which", return_value="/usr/bin/fake_bin")
