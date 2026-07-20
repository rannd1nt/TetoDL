from unittest.mock import MagicMock, patch

import pytest

from tetodl.core.models import CliDownload, CliExit, CliMenu, CliSearch


class TestCLIParser:
    """Tests for CLI argument parser."""

    @patch("tetodl.cli.parser.sys.argv", ["tetodl", "https://youtube.com/watch?v=test", "--audio"])
    def test_parse_audio_url(self):
        """CLI arg --audio produces a DownloadSession with media_type 'audio'."""
        from tetodl.cli.parser import CLIHandler

        handler = CLIHandler()
        handled, result = handler.parse()

        assert handled is False
        assert isinstance(result, CliDownload)
        assert result.session.media_type == "audio"
        assert "youtube.com/watch?v=test" in result.session.url

    @patch("tetodl.cli.parser.sys.argv", ["tetodl", "https://youtube.com/watch?v=test", "--video"])
    def test_parse_video_url(self):
        """CLI arg --video produces a DownloadSession with media_type 'video'."""
        from tetodl.cli.parser import CLIHandler

        handler = CLIHandler()
        handled, result = handler.parse()

        assert handled is False
        assert isinstance(result, CliDownload)
        assert result.session.media_type == "video"
        assert "youtube.com/watch?v=test" in result.session.url

    @patch("tetodl.cli.parser.sys.argv", ["tetodl", "https://youtube.com/watch?v=test", "--thumbnail-only"])
    def test_parse_thumbnail_url(self):
        """CLI arg --thumbnail-only produces a DownloadSession with media_type 'thumbnail'."""
        from tetodl.cli.parser import CLIHandler

        handler = CLIHandler()
        handled, result = handler.parse()

        assert handled is False
        assert isinstance(result, CliDownload)
        assert result.session.media_type == "thumbnail"

    @patch("tetodl.cli.parser.sys.argv", ["tetodl", "https://youtube.com/watch?v=test"])
    def test_parse_default_media_type_url(self):
        """Default detection for a plain youtube.com URL should be 'video'."""
        from tetodl.cli.parser import CLIHandler

        handler = CLIHandler()
        handled, result = handler.parse()

        assert handled is False
        assert isinstance(result, CliDownload)
        assert result.session.media_type == "video"

    @patch("tetodl.cli.parser.sys.argv", ["tetodl", "https://music.youtube.com/watch?v=test"])
    def test_parse_youtube_music_default_audio(self):
        """Default detection for music.youtube.com URL should be 'audio'."""
        from tetodl.cli.parser import CLIHandler

        handler = CLIHandler()
        handled, result = handler.parse()

        assert handled is False
        assert isinstance(result, CliDownload)
        assert result.session.media_type == "audio"

    @patch("tetodl.cli.parser.sys.argv", ["tetodl", "--version"])
    def test_parse_version(self):
        """--version flag produces CliExit."""
        from tetodl.cli.parser import CLIHandler

        handler = CLIHandler()
        handled, result = handler.parse()

        assert handled is True
        assert isinstance(result, CliExit)

    @patch("tetodl.cli.parser.sys.argv", ["tetodl"])
    def test_parse_no_args(self):
        """No args produces CliMenu."""
        from tetodl.cli.parser import CLIHandler

        handler = CLIHandler()
        handled, result = handler.parse()

        assert handled is False
        assert isinstance(result, CliMenu)

    @patch(
        "tetodl.cli.parser.sys.argv",
        ["tetodl", "--search", "never gonna give you up"],
    )
    def test_parse_search(self):
        """--search produces CliSearch."""
        from tetodl.cli.parser import CLIHandler

        handler = CLIHandler()
        handled, result = handler.parse()

        assert handled is False
        assert isinstance(result, CliSearch)
        assert result.query == "never gonna give you up"
        assert result.limit == 5
