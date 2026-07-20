import pytest


class TestDependency:
    """Tests for dependency verification functions."""

    def test_check_python_version(self, mocker):
        """Returns True on modern Python (>= 3.8)."""
        mocker.patch("tetodl.core.dependency.console.ok")
        from tetodl.core.dependency import check_python_version
        assert check_python_version() is True

    def test_get_ytdlp_version_info_returns_tuple(self, mocker):
        """Returns expected tuple shape (bool, str, str) when mocked."""
        mocker.patch("tetodl.core.dependency.console.ok")
        mock_get = mocker.patch("tetodl.core.dependency.requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"info": {"version": "2024.12.06"}}
        mock_get.return_value = mock_response

        mock_ytdlp = mocker.Mock()
        mock_ytdlp.version.__version__ = "2024.12.06"
        mocker.patch.dict("sys.modules", {"yt_dlp": mock_ytdlp})

        from tetodl.core.dependency import get_ytdlp_version_info
        is_outdated, current, latest = get_ytdlp_version_info()
        assert isinstance(is_outdated, bool)
        assert isinstance(current, str)
        assert isinstance(latest, str)
        assert current == latest

    def test_get_ytdlp_version_info_outdated(self, mocker):
        """Returns outdated=True when installed version is behind latest."""
        mocker.patch("tetodl.core.dependency.console.ok")
        mock_get = mocker.patch("tetodl.core.dependency.requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"info": {"version": "2025.01.01"}}
        mock_get.return_value = mock_response

        mock_ytdlp = mocker.Mock()
        mock_ytdlp.version.__version__ = "2024.01.01"
        mocker.patch.dict("sys.modules", {"yt_dlp": mock_ytdlp})

        from tetodl.core.dependency import get_ytdlp_version_info
        is_outdated, current, latest = get_ytdlp_version_info()
        assert is_outdated is True
        assert current < latest

    def test_get_ytdlp_version_info_network_error(self, mocker):
        """Returns safe defaults when the network request fails."""
        mocker.patch("tetodl.core.dependency.requests.get", side_effect=Exception("timeout"))
        mock_ytdlp = mocker.Mock()
        mock_ytdlp.version.__version__ = "2024.01.01"
        mocker.patch.dict("sys.modules", {"yt_dlp": mock_ytdlp})

        from tetodl.core.dependency import get_ytdlp_version_info
        is_outdated, current, latest = get_ytdlp_version_info()
        assert is_outdated is False
        assert current == "unknown"
        assert latest == "unknown"

    def test_check_command_exists_false(self):
        """Returns False for a nonexistent command."""
        from tetodl.core.dependency import check_command_exists
        assert check_command_exists("thiscommanddoesnotexist12345") is False

    def test_check_command_exists_true(self):
        """Returns True for an existing command (e.g. 'echo')."""
        from tetodl.core.dependency import check_command_exists
        assert check_command_exists("echo") is True

    def test_check_python_package_stdlib(self, mocker):
        """Returns True for a known stdlib module."""
        mocker.patch("tetodl.core.dependency.console.ok")
        from tetodl.core.dependency import check_python_package

        assert check_python_package("os") is True

    def test_check_python_package_fake(self, mocker):
        """Returns False for a nonexistent package."""
        mocker.patch("tetodl.core.dependency.console.err")
        from tetodl.core.dependency import check_python_package

        assert check_python_package("_nonexistent_package_xyz_") is False
