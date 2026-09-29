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

from unittest.mock import patch

import pytest

from tetodl.core.domain.models import CliDownload, CliExit, CliMenu, CliSearch


class TestCLIParser:
    """Tests for CLI argument parser."""

    @patch("tetodl.ui.cli.parser.sys.argv", ["tetodl", "https://youtube.com/watch?v=test", "--audio"])
    def test_parse_audio_url(self):
        """CLI arg --audio produces a DownloadSession with media_type 'audio'."""
        from tetodl.ui.cli.parser import CLIHandler

        handler = CLIHandler()
        handled, result = handler.parse()

        assert handled is False
        assert isinstance(result, CliDownload)
        assert result.session.media_type == "audio"
        assert "youtube.com/watch?v=test" in result.session.url

    @patch("tetodl.ui.cli.parser.sys.argv", ["tetodl", "https://youtube.com/watch?v=test", "--video"])
    def test_parse_video_url(self):
        """CLI arg --video produces a DownloadSession with media_type 'video'."""
        from tetodl.ui.cli.parser import CLIHandler

        handler = CLIHandler()
        handled, result = handler.parse()

        assert handled is False
        assert isinstance(result, CliDownload)
        assert result.session.media_type == "video"
        assert "youtube.com/watch?v=test" in result.session.url

    @patch("tetodl.ui.cli.parser.sys.argv", ["tetodl", "https://youtube.com/watch?v=test", "-T"])
    def test_parse_thumbnail_url(self):
        """CLI arg -T/--thumbnail produces a DownloadSession with media_type 'thumbnail'."""
        from tetodl.ui.cli.parser import CLIHandler

        handler = CLIHandler()
        handled, result = handler.parse()

        assert handled is False
        assert isinstance(result, CliDownload)
        assert result.session.media_type == "thumbnail"

    @patch("tetodl.ui.cli.parser.sys.argv", ["tetodl", "https://youtube.com/watch?v=test"])
    def test_parse_default_media_type_url(self):
        """Default detection for a plain youtube.com URL should be 'video'."""
        from tetodl.ui.cli.parser import CLIHandler

        handler = CLIHandler()
        handled, result = handler.parse()

        assert handled is False
        assert isinstance(result, CliDownload)
        assert result.session.media_type == "video"

    @patch("tetodl.ui.cli.parser.sys.argv", ["tetodl", "https://music.youtube.com/watch?v=test"])
    def test_parse_youtube_music_default_audio(self):
        """Default detection for music.youtube.com URL should be 'audio'."""
        from tetodl.ui.cli.parser import CLIHandler

        handler = CLIHandler()
        handled, result = handler.parse()

        assert handled is False
        assert isinstance(result, CliDownload)
        assert result.session.media_type == "audio"

    @patch("tetodl.ui.cli.parser.sys.argv", ["tetodl", "--version"])
    def test_parse_version(self):
        """--version flag produces CliExit."""
        from tetodl.ui.cli.parser import CLIHandler

        handler = CLIHandler()
        handled, result = handler.parse()

        assert handled is True
        assert isinstance(result, CliExit)

    @patch("tetodl.ui.cli.parser.sys.argv", ["tetodl"])
    def test_parse_no_args(self):
        """No args produces CliMenu."""
        from tetodl.ui.cli.parser import CLIHandler

        handler = CLIHandler()
        handled, result = handler.parse()

        assert handled is False
        assert isinstance(result, CliMenu)

    @patch(
        "tetodl.ui.cli.parser.sys.argv",
        ["tetodl", "--search", "never gonna give you up"],
    )
    def test_parse_search(self):
        """--search produces CliSearch."""
        from tetodl.ui.cli.parser import CLIHandler

        handler = CLIHandler()
        handled, result = handler.parse()

        assert handled is False
        assert isinstance(result, CliSearch)
        assert result.query == "never gonna give you up"
        assert result.limit == 5

    # --- Spotify flag tests ---

    @patch("tetodl.ui.cli.parser.sys.argv", ["tetodl", "https://open.spotify.com/track/abc"])
    def test_spotify_auto_detect(self):
        """Spotify URL without --spotify flag auto-detects is_spotify=True."""
        from tetodl.ui.cli.parser import CLIHandler

        handler = CLIHandler()
        handled, result = handler.parse()

        assert handled is False
        assert isinstance(result, CliDownload)
        assert result.session.is_spotify is True
        assert result.session.media_type == "audio"

    @patch("tetodl.ui.cli.parser.sys.argv", ["tetodl", "https://open.spotify.com/track/abc", "--video"])
    def test_spotify_video_conflict(self):
        """--spotify + --video should error."""
        from tetodl.ui.cli.parser import CLIHandler

        handler = CLIHandler()
        with pytest.raises(SystemExit):
            handler.parse()

    @patch("tetodl.ui.cli.parser.sys.argv", ["tetodl", "https://open.spotify.com/playlist/pl", "--lyrics", "--group"])
    def test_spotify_with_other_flags(self):
        """--spotify works with --lyrics and --group."""
        from tetodl.ui.cli.parser import CLIHandler

        handler = CLIHandler()
        handled, result = handler.parse()

        assert handled is False
        assert isinstance(result, CliDownload)
        assert result.session.is_spotify is True
        assert result.session.lyrics is True
        assert result.session.group_folder is not False

    @patch("tetodl.ui.cli.parser.sys.argv", ["tetodl", "https://open.spotify.com/album/al", "--format", "mp3"])
    def test_spotify_with_format(self):
        """Spotify + --format."""
        from tetodl.ui.cli.parser import CLIHandler

        handler = CLIHandler()
        handled, result = handler.parse()

        assert handled is False
        assert isinstance(result, CliDownload)
        assert result.session.is_spotify is True

    @patch("tetodl.ui.cli.parser.sys.argv", ["tetodl", "https://open.spotify.com/track/abc", "-T"])
    def test_spotify_thumbnail_mode(self):
        """--spotify + -T should produce thumbnail session."""
        from tetodl.ui.cli.parser import CLIHandler

        handler = CLIHandler()
        handled, result = handler.parse()
        assert handled is False
        assert isinstance(result, CliDownload)
        assert result.session.is_spotify is True
        assert result.session.media_type == "thumbnail"

    def test_share_subcommand_invoked(self, tmp_path):
        """tetodl share [PATH] invokes standalone share handler with flat and no_parent flags."""
        from tetodl.ui.cli.parser import CLIHandler

        share_target = tmp_path / "share_folder"
        share_target.mkdir()

        with patch("tetodl.ui.cli.parser.sys.argv", ["tetodl", "share", str(share_target), "--flat"]):
            with patch("tetodl.ui.cli.network.start_share_server") as mock_start:
                handler = CLIHandler()
                handled, result = handler.parse()
                assert handled is True
                assert isinstance(result, CliExit)
                mock_start.assert_called_once()
                args, kwargs = mock_start.call_args
                assert args[0] == str(share_target.resolve())
                assert kwargs.get("flat") is True
                assert kwargs.get("no_parent") is True

    def test_config_subcommand_path(self, capsys, tmp_path):
        """tetodl config path prints config file path."""
        from tetodl.ui.cli.parser import CLIHandler

        cfg_file = tmp_path / "tetodl.conf"
        with patch("tetodl.ui.cli.parser.sys.argv", ["tetodl", "config", "path"]):
            with patch("tetodl.core.domain.server_config.ensure_default_server_config", return_value=cfg_file):
                handler = CLIHandler()
                handled, result = handler.parse()
                assert handled is True
                assert isinstance(result, CliExit)
                captured = capsys.readouterr()
                assert str(cfg_file) in captured.out

    def test_config_subcommand_show(self, capsys, tmp_path):
        """tetodl config show prints config content."""
        from tetodl.ui.cli.parser import CLIHandler

        cfg_file = tmp_path / "tetodl.conf"
        cfg_file.write_text("[server]\nhost = '127.0.0.1'\n", encoding="utf-8")
        with patch("tetodl.ui.cli.parser.sys.argv", ["tetodl", "config", "show"]):
            with patch("tetodl.core.domain.server_config.ensure_default_server_config", return_value=cfg_file):
                handler = CLIHandler()
                handled, result = handler.parse()
                assert handled is True
                assert isinstance(result, CliExit)
                captured = capsys.readouterr()
                assert "127.0.0.1" in captured.out

    def test_config_subcommand_edit(self, tmp_path):
        """tetodl config edit spawns editor with config path."""
        from tetodl.ui.cli.parser import CLIHandler

        cfg_file = tmp_path / "tetodl.conf"
        cfg_file.write_text("", encoding="utf-8")
        with patch("tetodl.ui.cli.parser.sys.argv", ["tetodl", "config", "edit"]):
            with patch("tetodl.core.domain.server_config.ensure_default_server_config", return_value=cfg_file):
                with patch("tetodl.ui.cli.parser.subprocess.run") as mock_run:
                    with patch.dict("os.environ", {"EDITOR": "myeditor"}):
                        handler = CLIHandler()
                        handled, result = handler.parse()
                        assert handled is True
                        assert isinstance(result, CliExit)
                        mock_run.assert_called_once_with(["myeditor", str(cfg_file)], check=True)

    def test_system_subcommand_update_ytdlp(self):
        """tetodl system update-ytdlp calls maintenance.update_ytdlp."""
        from tetodl.ui.cli.parser import CLIHandler

        with patch("tetodl.ui.cli.parser.sys.argv", ["tetodl", "system", "update-ytdlp"]):
            with patch("tetodl.core.maintenance.update_ytdlp") as mock_update:
                handler = CLIHandler()
                handled, result = handler.parse()
                assert handled is True
                assert isinstance(result, CliExit)
                mock_update.assert_called_once()

    def test_history_subcommand_routes(self):
        """tetodl history calls render_history_view."""
        from tetodl.ui.cli.parser import CLIHandler

        with patch("tetodl.ui.cli.parser.sys.argv", ["tetodl", "history", "15"]):
            with patch("tetodl.core.domain.history.load_history"):
                with patch("tetodl.core.domain.config.load_config"):
                    with patch("tetodl.ui.tui.analytics.render_history_view") as mock_hist:
                        handler = CLIHandler()
                        handled, result = handler.parse()
                        assert handled is True
                        assert isinstance(result, CliExit)
                        mock_hist.assert_called_once_with(15, False, None)

    def test_analytics_subcommand_routes(self):
        """tetodl analytics calls render_analytics_view."""
        from tetodl.ui.cli.parser import CLIHandler

        with patch("tetodl.ui.cli.parser.sys.argv", ["tetodl", "analytics"]):
            with patch("tetodl.core.domain.config.load_config"):
                with patch("tetodl.ui.tui.analytics.render_analytics_view") as mock_ana:
                    handler = CLIHandler()
                    handled, result = handler.parse()
                    assert handled is True
                    assert isinstance(result, CliExit)
                    mock_ana.assert_called_once()

    def test_search_subcommand_rewrites_to_clisearch(self):
        """tetodl search <QUERY> produces CliSearch."""
        from tetodl.ui.cli.parser import CLIHandler

        with patch("tetodl.ui.cli.parser.sys.argv", ["tetodl", "search", "test song"]):
            handler = CLIHandler()
            handled, result = handler.parse()
            assert handled is False
            assert isinstance(result, CliSearch)
            assert result.query == "test song"

    def test_interactive_flag_produces_climenu(self):
        """tetodl -i produces CliMenu."""
        from tetodl.ui.cli.parser import CLIHandler

        with patch("tetodl.ui.cli.parser.sys.argv", ["tetodl", "-i"]):
            handler = CLIHandler()
            handled, result = handler.parse()
            assert handled is False
            assert isinstance(result, CliMenu)


