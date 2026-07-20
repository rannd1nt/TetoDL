"""
Pipeline sub-package fixtures — step instances, mock handlers, ctx builders.
"""

from __future__ import annotations

from typing import Any

import pytest


@pytest.fixture
def mock_download_handler(mocker: Any) -> Any:
    """Mock ``pipeline.handlers.download_audio_youtube``.

    Returns a coroutine-like mock so the pipeline can call it without
    actually invoking yt-dlp.
    """
    return mocker.patch("tetodl.pipeline.handlers.download_audio_youtube")


@pytest.fixture
def mock_yt_dlp_extract(mocker: Any) -> Any:
    """Mock ``yt_dlp.YoutubeDL.extract_info`` to return a canned result.

    The caller can override ``mock_yt_dlp_extract.return_value`` to
    simulate different extractor outcomes.
    """
    return mocker.patch(
        "yt_dlp.YoutubeDL.extract_info",
        return_value={
            "id": "dQw4w9WgXcQ",
            "title": "Rick Astley - Never Gonna Give You Up",
            "webpage_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "extractor": "youtube",
        },
    )


@pytest.fixture
def step_ctx_factory() -> Any:
    """Return a factory function that builds a minimal PipelineContext.

    Usage::

        ctx = step_ctx_factory(url="https://example.com", media_type="audio")
    """
    from tetodl.core.models import AppConfig, PipelineContext

    def _build(
        url: str = "https://music.youtube.com/watch?v=dQw4w9WgXcQ",
        media_type: str = "audio",
        **overrides: Any,
    ) -> PipelineContext:
        config = overrides.pop("config", AppConfig())
        return PipelineContext(
            url=url,
            media_type=media_type,
            config=config,
            target_dir="/tmp/tetodl_test",
            **overrides,
        )

    return _build
