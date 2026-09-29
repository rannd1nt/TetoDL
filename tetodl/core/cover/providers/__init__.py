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

from tetodl.core.cover.providers.base import CoverProvider
from tetodl.core.cover.providers.deezer import DeezerProvider
from tetodl.core.cover.providers.itunes import ITunesProvider
from tetodl.core.cover.providers.genius import GeniusCoverProvider

_PROVIDERS: list[CoverProvider] | None = None


def get_cover_providers() -> list[CoverProvider]:
    global _PROVIDERS
    if _PROVIDERS is None:
        _PROVIDERS = [
            DeezerProvider(),
            GeniusCoverProvider(),
            ITunesProvider(),
        ]
    return _PROVIDERS


__all__ = ["CoverProvider", "get_cover_providers"]
