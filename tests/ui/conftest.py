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
UI sub-package fixtures — mock questionary, simulated user input, app helpers.
"""

from __future__ import annotations

from typing import Any

import pytest


@pytest.fixture
def mock_questionary_select(mocker: Any) -> Any:
    """Mock ``questionary.select`` to return a canned choice.

    Usage::

        mock_questionary_select.return_value.ask.return_value = "audio"
    """
    return mocker.patch("questionary.select")


@pytest.fixture
def mock_questionary_path(mocker: Any) -> Any:
    """Mock ``questionary.path`` for folder-selection prompts.

    Usage::

        mock_questionary_path.return_value.ask.return_value = "/downloads"
    """
    return mocker.patch("questionary.path")
