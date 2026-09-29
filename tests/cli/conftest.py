# Copyright 2026 rannd1nt
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
CLI sub-package fixtures — argv mock helpers, argument namespace builders.
"""

from __future__ import annotations

from typing import Any

import pytest


@pytest.fixture
def mock_argv(mocker: Any) -> Any:
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
