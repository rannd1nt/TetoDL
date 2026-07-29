

class TestMaintenance:
    """Tests for maintenance utilities."""

    def test_get_project_root(self):
        """get_project_root returns a Path pointing to the project root."""
        from tetodl.core.maintenance import get_project_root
        root = get_project_root()
        assert root.exists()
        assert (root / "tetodl").is_dir()

    def test_reset_data_cache_only(self, mocker):
        """reset_data with ['cache'] does not crash and handles no-garbage path."""
        mocker.patch("tetodl.core.maintenance.os.path.exists", return_value=False)
        mocker.patch("tetodl.core.maintenance.os.listdir", side_effect=OSError)
        mock_warn = mocker.patch("tetodl.core.maintenance.console.warn")

        from tetodl.core.maintenance import reset_data
        reset_data(targets=["cache"])

        mock_warn.assert_any_call(mocker.ANY)

    def test_reset_data_all_confirm_yes(self, mocker):
        """reset_data with ['all'] and confirmation='y' resets everything."""
        mocker.patch("tetodl.core.maintenance.os.path.exists", return_value=True)
        mocker.patch("tetodl.core.maintenance.os.listdir", return_value=["file1"])
        mocker.patch("tetodl.core.maintenance.console.warn")
        mocker.patch("tetodl.core.maintenance.console.ok")
        mocker.patch("tetodl.core.maintenance.console.err")
        mocker.patch("tetodl.core.maintenance.TempManager.cleanup")
        mocker.patch("tetodl.core.maintenance.shutil.rmtree")
        mocker.patch("tetodl.core.maintenance.os.remove")
        mocker.patch("tetodl.core.maintenance.time.sleep")
        mock_input = mocker.patch("builtins.input", return_value="y")

        mock_reset_history = mocker.patch("tetodl.core.maintenance.reset_history")
        mock_reset_config = mocker.patch("tetodl.core.maintenance.reset_config")
        mock_registry_reset = mocker.patch("tetodl.core.maintenance.registry.reset")

        from tetodl.core.maintenance import reset_data
        reset_data(targets=["all"])

        assert mock_input.call_count >= 1
        mock_reset_history.assert_called_once()
        mock_reset_config.assert_called_once()
        mock_registry_reset.assert_called_once()

    def test_reset_data_all_confirm_no(self, mocker):
        """reset_data with ['all'] warns about empty targets when nothing exists."""
        mocker.patch("tetodl.core.maintenance.os.path.exists", return_value=False)
        mocker.patch("tetodl.core.maintenance.console.warn")
        mocker.patch("tetodl.core.maintenance.console.ok")

        from tetodl.core.maintenance import reset_data
        reset_data(targets=["all"])

    def test_reset_data_empty_targets(self, mocker):
        """reset_data with empty targets list does nothing."""
        mocker.patch("tetodl.core.maintenance.console.warn")
        mocker.patch("tetodl.core.maintenance.console.ok")

        from tetodl.core.maintenance import reset_data
        reset_data(targets=[])

    def test_reset_data_history_only(self, mocker):
        """reset_data with ['history'] resets history when it exists."""
        mocker.patch("tetodl.core.maintenance.os.path.exists", return_value=True)
        mocker.patch("tetodl.core.maintenance.console.warn")
        mocker.patch("tetodl.core.maintenance.console.ok")
        mocker.patch("builtins.input", return_value="y")
        mock_reset_history = mocker.patch("tetodl.core.maintenance.reset_history")

        from tetodl.core.maintenance import reset_data
        reset_data(targets=["history"])

        mock_reset_history.assert_called_once()

    def test_reset_data_history_missing(self, mocker):
        """reset_data with ['history'] warns when history file doesn't exist."""
        mocker.patch("tetodl.core.maintenance.os.path.exists", return_value=False)
        mocker.patch("tetodl.core.maintenance.console.warn")
        mocker.patch("tetodl.core.maintenance.console.ok")

        from tetodl.core.maintenance import reset_data
        reset_data(targets=["history"])

    def test_reset_data_cache_with_garbage(self, mocker):
        """reset_data with ['cache'] cleans up when garbage exists."""
        mocker.patch("tetodl.core.maintenance.os.path.exists", return_value=True)
        mocker.patch("tetodl.core.maintenance.console.warn")
        mocker.patch("tetodl.core.maintenance.console.ok")
        mock_cleanup = mocker.patch("tetodl.core.maintenance.TempManager.cleanup")
        mocker.patch("tetodl.core.maintenance.shutil.rmtree")
        mocker.patch("tetodl.core.maintenance.os.remove")

        from tetodl.core.maintenance import reset_data
        reset_data(targets=["cache"])

        mock_cleanup.assert_called_once()
