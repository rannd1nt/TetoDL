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

from unittest.mock import MagicMock, patch


class TestNavigationImports:
    """Basic import tests for the navigation module."""

    def test_navigation_module_imports(self):
        """The navigation module can be imported without errors."""
        import tetodl.ui.tui.navigation as nav
        assert hasattr(nav, "navigate_folders")
        assert hasattr(nav, "select_download_folder")

    @patch("tetodl.ui.tui.navigation.questionary")
    @patch("tetodl.ui.tui.navigation.cfg")
    def test_select_download_folder_simple_mode(self, mock_cfg, mock_questionary):
        """select_download_folder returns root_dir when simple_mode is True."""
        mock_cfg.simple_mode = True
        from tetodl.ui.tui.navigation import select_download_folder

        result = select_download_folder("/music", "audio")
        assert result == "/music"
        mock_questionary.select.assert_not_called()

    @patch("tetodl.ui.tui.navigation.questionary")
    @patch("tetodl.ui.tui.navigation.cfg")
    def test_select_download_folder_cancel(self, mock_cfg, mock_questionary):
        """select_download_folder returns None when user cancels."""
        mock_cfg.simple_mode = False
        mock_cfg.user_subfolders = {}
        mock_select = MagicMock()
        mock_select.ask.return_value = "__CANCEL__"
        mock_questionary.select.return_value = mock_select

        from tetodl.ui.tui.navigation import select_download_folder

        result = select_download_folder("/music", "audio")
        assert result is None

    @patch("tetodl.ui.tui.navigation.questionary")
    @patch("tetodl.ui.tui.navigation.cfg")
    def test_select_download_folder_root(self, mock_cfg, mock_questionary):
        """select_download_folder returns root_dir when user selects root."""
        mock_cfg.simple_mode = False
        mock_cfg.user_subfolders = {}
        mock_select = MagicMock()
        mock_select.ask.return_value = "__ROOT__"
        mock_questionary.select.return_value = mock_select

        from tetodl.ui.tui.navigation import select_download_folder

        result = select_download_folder("/music", "audio")
        assert result == "/music"
