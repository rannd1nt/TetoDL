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
Source handler protocol — each source (YouTube, Spotify, etc.) implements
:class:`SourceHandler` to declare which URLs it handles and how to extract
track metadata from them.

Usage::

    from tetodl.core.sources.base import SourceHandler, VideoInfo
"""

from dataclasses import dataclass
from typing import Protocol


@dataclass
class VideoInfo:
    url: str
    title: str
    artist: str | None = None
    album: str | None = None
    cover_url: str | None = None
    source: str = ""
    raw_title: str | None = None


class SourceHandler(Protocol):
    """Handle one type of input URL -> list of VideoInfo."""

    def handles(self, url: str) -> bool:
        """Return True if this handler can process the given URL."""
        ...

    def extract(self, url: str) -> list[VideoInfo]:
        """Extract track metadata from the URL.

        Returns a list of VideoInfo (one per track, even for playlists).
        """
        ...
