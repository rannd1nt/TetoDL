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

from __future__ import annotations

from tetodl.core.pipeline.cleaners.title import clean_youtube_title
from tetodl.core.domain.models import CoverResult, MediaInfo, PipelineContext


def resolve_artist_title(
    info: MediaInfo,
    ctx: PipelineContext | None = None,
    cover_result: CoverResult | None = None,
) -> tuple[str, str]:
    if cover_result and cover_result.metadata:
        return cover_result.metadata.artist, cover_result.metadata.title

    if ctx and ctx.spotify_title:
        return (ctx.spotify_artist or ""), ctx.spotify_title

    if info.artist and info.track:
        return info.artist, info.track

    raw = info.title or ""
    artist, title = clean_youtube_title(raw)
    if artist and title:
        if info.uploader:
            uploader_clean = info.uploader.replace(" - Topic", "").strip().lower()
            if title.lower() == uploader_clean and artist.lower() != uploader_clean:
                artist, title = title, artist
        return artist, title

    artist = info.artist or info.uploader.replace(" - Topic", "")
    title = info.track or info.title
    return artist or "", title or ""
