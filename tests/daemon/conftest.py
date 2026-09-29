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
