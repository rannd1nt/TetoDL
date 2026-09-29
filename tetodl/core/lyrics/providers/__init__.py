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

from tetodl.core.lyrics.providers.base import LyricsProvider
from tetodl.core.lyrics.providers.genius import GeniusProvider
from tetodl.core.lyrics.providers.lrclib import LRCLIBProvider

_PROVIDERS: list[LyricsProvider] | None = None


def get_lyrics_providers() -> list[LyricsProvider]:
    global _PROVIDERS
    if _PROVIDERS is None:
        _PROVIDERS = [LRCLIBProvider(), GeniusProvider()]
    return _PROVIDERS


__all__ = ["LyricsProvider", "get_lyrics_providers"]
