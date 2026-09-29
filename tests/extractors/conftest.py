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
Extractors sub-package fixtures — mock yt-dlp extractor, plugin registry helpers.
"""

from __future__ import annotations

from typing import Any

import pytest


@pytest.fixture
def mock_extractor_result() -> dict[str, Any]:
    """Return a canned ``yt-dlp``-style extractor result dict."""
    return {
        "id": "dQw4w9WgXcQ",
        "title": "Rick Astley - Never Gonna Give You Up",
        "webpage_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "extractor": "youtube",
        "extractor_key": "Youtube",
        "duration": 212,
        "thumbnail": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
        "formats": [
            {"format_id": "140", "ext": "m4a", "vcodec": "none", "acodec": "aac"},
            {"format_id": "137", "ext": "mp4", "vcodec": "avc1", "acodec": "none"},
        ],
        "subtitles": {},
        "requested_subtitles": None,
        "automatic_captions": {},
    }


@pytest.fixture
def mock_ytdlp_extract_info(mocker: Any) -> Any:
    """Mock ``yt_dlp.YoutubeDL`` to return a controlled extractor result.

    The returned mock can be configured per-test::

        mock_ytdlp_extract_info.return_value = mock_extractor_result()
        mock_ytdlp_extract_info.side_effect = Exception("Network error")
    """
    return mocker.patch("yt_dlp.YoutubeDL.extract_info")
