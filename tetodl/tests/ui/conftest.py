"""
UI sub-package fixtures — mock questionary, simulated user input, app helpers.
"""

from __future__ import annotations

from typing import Any

import pytest


@pytest.fixture
def mock_questionary_select(mocker: pytest.FixtureRequest) -> Any:
    """Mock ``questionary.select`` to return a canned choice.

    Usage::

        mock_questionary_select.return_value.ask.return_value = "audio"
    """
    return mocker.patch("questionary.select")


@pytest.fixture
def mock_questionary_path(mocker: pytest.FixtureRequest) -> Any:
    """Mock ``questionary.path`` for folder-selection prompts.

    Usage::

        mock_questionary_path.return_value.ask.return_value = "/downloads"
    """
    return mocker.patch("questionary.path")
