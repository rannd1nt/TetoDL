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
