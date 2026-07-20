"""
CLI sub-package fixtures — argv mock helpers, argument namespace builders.
"""

from __future__ import annotations

from typing import Any

import pytest


@pytest.fixture
def mock_argv(mocker: pytest.FixtureRequest) -> Any:
    """Mock ``sys.argv`` for CLI parser tests.

    Usage::

        def test_audio_url(mock_argv):
            mock_argv(["tetodl", "https://youtu.be/dQw4w9WgXcQ"])
            args = parse_args()
            assert args.url == "https://youtu.be/dQw4w9WgXcQ"

    The fixture cleans up ``sys.argv`` after the test automatically.
    """
    return mocker.patch("sys.argv")


@pytest.fixture
def sample_args() -> dict[str, Any]:
    """Return a dict that mimics the ``argparse.Namespace`` for ``tetodl``.

    Individual tests can convert to a ``Namespace`` with
    ``argparse.Namespace(**sample_args())`` or patch the dispatch layer.
    """
    return {
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "output": None,
        "config": None,
        "debug": False,
        "quiet": False,
        "version": False,
        "music": False,
        "command": None,
    }
