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

"""UI provider protocol — domain-level abstraction for UI rendering."""

from typing import Protocol


class UIProvider(Protocol):
    """Interface for all UI rendering strategies."""

    def header(self) -> None: ...

    def clear(self) -> None: ...

    def wait_and_clear_prompt(self, msg: str | None = None) -> None: ...


class NullUI:
    """Silent provider — no output, no interaction."""

    @staticmethod
    def header() -> None: pass

    @staticmethod
    def clear() -> None: pass

    @staticmethod
    def wait_and_clear_prompt(msg: str | None = None) -> None: pass
