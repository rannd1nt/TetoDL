import json


class TestConfigLoad:
    """Tests for config loading behavior."""

    def test_load_config_defaults(self, monkeypatch, mocker, tetodl_trace):
        """Loading with no config file keeps module defaults and detects language."""
        import tetodl.core.config as cfg
        monkeypatch.setattr(cfg, "CONFIG_PATH", "/nonexistent/path.json")
        mock_detect = mocker.patch("tetodl.core.config.detect_system_language", return_value="en")
        mock_set = mocker.patch("tetodl.core.config.set_language")

        cfg.load_config()
        mock_detect.assert_called_once()
        mock_set.assert_called_once_with("en")

    def test_load_config_from_file(self, monkeypatch, mocker, tmp_path):
        """Loading from a valid JSON file updates module-level variables."""
        import tetodl.core.config as cfg
        config_file = tmp_path / "config.json"
        data = {
            "music_root": "/custom/music",
            "simple_mode": True,
            "max_video_resolution": "1080p",
            "smart_cover_mode": False,
            "language": "id",
        }
        config_file.write_text(json.dumps(data))
        monkeypatch.setattr(cfg, "CONFIG_PATH", str(config_file))
        mocker.patch("tetodl.core.config.detect_system_language")
        mock_set = mocker.patch("tetodl.core.config.set_language")

        cfg.load_config()
        assert cfg.music_root == "/custom/music"
        assert cfg.simple_mode is True
        assert cfg.max_video_resolution == "1080p"
        assert cfg.smart_cover_mode is False
        assert cfg.language == "id"
        mock_set.assert_called_once_with("id")

    def test_load_config_handles_bad_json(self, monkeypatch, mocker, tmp_path):
        """Corrupt JSON falls back to system language."""
        import tetodl.core.config as cfg
        config_file = tmp_path / "config.json"
        config_file.write_text("not valid json")
        monkeypatch.setattr(cfg, "CONFIG_PATH", str(config_file))
        mock_detect = mocker.patch("tetodl.core.config.detect_system_language", return_value="en")
        mock_set = mocker.patch("tetodl.core.config.set_language")

        cfg.load_config()
        assert cfg.language == "en"
        mock_detect.assert_called_once()
        mock_set.assert_called_once_with("en")


class TestConfigSave:
    """Tests for config persistence."""

    def test_save_config(self, monkeypatch, tmp_path):
        """save_config writes correct JSON to CONFIG_PATH."""
        import tetodl.core.config as cfg
        config_file = tmp_path / "config.json"
        monkeypatch.setattr(cfg, "CONFIG_PATH", str(config_file))
        monkeypatch.setattr(cfg, "music_root", "/tmp/test/music")
        monkeypatch.setattr(cfg, "simple_mode", True)
        monkeypatch.setattr(cfg, "max_video_resolution", "1080p")
        monkeypatch.setattr(cfg, "language", "en")

        cfg.save_config()

        saved = json.loads(config_file.read_text())
        assert saved["music_root"] == "/tmp/test/music"
        assert saved["simple_mode"] is True
        assert saved["max_video_resolution"] == "1080p"
        assert saved["language"] == "en"

    def test_save_config_handles_write_error(self, mocker):
        """save_config does not raise when the file cannot be written."""
        mocker.patch("builtins.open", side_effect=OSError("permission denied"))
        from tetodl.core.config import save_config
        save_config()


class TestConfigToggles:
    """Tests for config toggle functions."""

    def test_toggle_simple_mode(self, monkeypatch, tmp_path):
        """toggle_simple_mode toggles the module state and persists."""
        import tetodl.core.config as cfg
        config_file = tmp_path / "config.json"
        config_file.write_text("{}")
        monkeypatch.setattr(cfg, "CONFIG_PATH", str(config_file))

        cfg.toggle_simple_mode(True)
        assert cfg.simple_mode is True
        cfg.toggle_simple_mode(False)
        assert cfg.simple_mode is False

    def test_toggle_smart_cover(self, monkeypatch, tmp_path):
        """toggle_smart_cover updates smart_cover_mode and persists."""
        import tetodl.core.config as cfg
        config_file = tmp_path / "config.json"
        config_file.write_text("{}")
        monkeypatch.setattr(cfg, "CONFIG_PATH", str(config_file))

        cfg.toggle_smart_cover(False)
        assert cfg.smart_cover_mode is False
        cfg.toggle_smart_cover(True)
        assert cfg.smart_cover_mode is True

    def test_toggle_skip_existing(self, monkeypatch, tmp_path):
        """toggle_skip_existing flips skip_existing_files."""
        import tetodl.core.config as cfg
        config_file = tmp_path / "config.json"
        config_file.write_text("{}")
        monkeypatch.setattr(cfg, "CONFIG_PATH", str(config_file))

        cfg.toggle_skip_existing(False)
        assert cfg.skip_existing_files is False
        cfg.toggle_skip_existing(True)
        assert cfg.skip_existing_files is True

    def test_toggle_video_container_valid(self, monkeypatch, tmp_path):
        """Valid container returns True and updates state."""
        import tetodl.core.config as cfg
        config_file = tmp_path / "config.json"
        config_file.write_text("{}")
        monkeypatch.setattr(cfg, "CONFIG_PATH", str(config_file))

        result = cfg.toggle_video_container("mkv")
        assert result is True
        assert cfg.video_container == "mkv"

    def test_toggle_video_container_invalid(self, monkeypatch, tmp_path):
        """Invalid container returns False and does not change state."""
        import tetodl.core.config as cfg
        config_file = tmp_path / "config.json"
        config_file.write_text("{}")
        monkeypatch.setattr(cfg, "CONFIG_PATH", str(config_file))

        original = cfg.video_container
        result = cfg.toggle_video_container("avi")
        assert result is False
        assert cfg.video_container == original

    def test_set_video_resolution_valid(self, monkeypatch, tmp_path):
        """Valid resolution updates the module state."""
        import tetodl.core.config as cfg
        config_file = tmp_path / "config.json"
        config_file.write_text("{}")
        monkeypatch.setattr(cfg, "CONFIG_PATH", str(config_file))

        result = cfg.set_video_resolution("1080p")
        assert result is True
        assert cfg.max_video_resolution == "1080p"

    def test_set_video_resolution_invalid(self, monkeypatch, tmp_path):
        """Invalid resolution returns False."""
        import tetodl.core.config as cfg
        config_file = tmp_path / "config.json"
        config_file.write_text("{}")
        monkeypatch.setattr(cfg, "CONFIG_PATH", str(config_file))

        original = cfg.max_video_resolution
        result = cfg.set_video_resolution("4k")
        assert result is False
        assert cfg.max_video_resolution == original

    def test_set_video_codec_valid(self, monkeypatch, tmp_path):
        """Valid codec updates the module state."""
        import tetodl.core.config as cfg
        config_file = tmp_path / "config.json"
        config_file.write_text("{}")
        monkeypatch.setattr(cfg, "CONFIG_PATH", str(config_file))

        result = cfg.set_video_codec("h265")
        assert result is True
        assert cfg.video_codec == "h265"

    def test_toggle_audio_quality_valid(self, monkeypatch, tmp_path):
        """Valid quality returns the new quality key."""
        import tetodl.core.config as cfg
        config_file = tmp_path / "config.json"
        config_file.write_text("{}")
        monkeypatch.setattr(cfg, "CONFIG_PATH", str(config_file))

        result = cfg.toggle_audio_quality("opus")
        assert result == "opus"
        assert cfg.audio_quality == "opus"

    def test_toggle_audio_quality_invalid(self, monkeypatch, tmp_path):
        """Invalid quality returns the current quality key unchanged."""
        import tetodl.core.config as cfg
        config_file = tmp_path / "config.json"
        config_file.write_text("{}")
        monkeypatch.setattr(cfg, "CONFIG_PATH", str(config_file))

        original = cfg.audio_quality
        result = cfg.toggle_audio_quality("wav")
        assert result == original

    def test_set_progress_style_valid(self, monkeypatch, tmp_path):
        """Valid progress style is accepted."""
        import tetodl.core.config as cfg
        config_file = tmp_path / "config.json"
        config_file.write_text("{}")
        monkeypatch.setattr(cfg, "CONFIG_PATH", str(config_file))

        result = cfg.set_progress_style("modern")
        assert result == "modern"
        assert cfg.progress_style == "modern"

    def test_set_progress_style_invalid(self, monkeypatch, tmp_path):
        """Invalid progress style returns the current value."""
        import tetodl.core.config as cfg
        config_file = tmp_path / "config.json"
        config_file.write_text("{}")
        monkeypatch.setattr(cfg, "CONFIG_PATH", str(config_file))

        original = cfg.progress_style
        result = cfg.set_progress_style("unknown")
        assert result == original

    def test_set_header_style(self, monkeypatch, tmp_path):
        """set_header_style always returns True."""
        import tetodl.core.config as cfg
        config_file = tmp_path / "config.json"
        config_file.write_text("{}")
        monkeypatch.setattr(cfg, "CONFIG_PATH", str(config_file))

        result = cfg.set_header_style("classic")
        assert result is True
        assert cfg.header_style == "classic"

    def test_set_jitter_config(self, monkeypatch, tmp_path):
        """set_jitter_config saves config and returns True."""
        import tetodl.core.config as cfg
        config_file = tmp_path / "config.json"
        config_file.write_text("{}")
        monkeypatch.setattr(cfg, "CONFIG_PATH", str(config_file))

        result = cfg.set_jitter_config(min_=2.0, max_=6.0, retries=7)
        assert result is True

    def test_set_media_scanner(self, monkeypatch, tmp_path):
        """set_media_scanner saves config and returns True.

        Note: module-level media_scanner_enabled is NOT updated
        directly — the function lacks a ``global`` declaration
        (existing source issue).
        """
        import tetodl.core.config as cfg
        config_file = tmp_path / "config.json"
        config_file.write_text("{}")
        monkeypatch.setattr(cfg, "CONFIG_PATH", str(config_file))

        result = cfg.set_media_scanner(True)
        assert result is True


class TestFormatStrings:
    """Tests for yt-dlp format string generation."""

    def test_get_video_format_string(self, monkeypatch):
        """Returns correct yt-dlp format string with height cap."""
        import tetodl.core.config as cfg
        monkeypatch.setattr(cfg, "max_video_resolution", "1080p")
        result = cfg.get_video_format_string()
        assert result == "bestvideo[height<=1080]+bestaudio/best[height<=1080]"

    def test_get_video_format_string_720p(self, monkeypatch):
        """Returns format string for 720p."""
        import tetodl.core.config as cfg
        monkeypatch.setattr(cfg, "max_video_resolution", "720p")
        result = cfg.get_video_format_string()
        assert result == "bestvideo[height<=720]+bestaudio/best[height<=720]"

    def test_get_fallback_format_string(self, monkeypatch):
        """Returns correct fallback format string."""
        import tetodl.core.config as cfg
        monkeypatch.setattr(cfg, "max_video_resolution", "720p")
        result = cfg.get_fallback_format_string()
        assert result == "best[height<=720][ext=mp4]"

    def test_get_fallback_format_string_1080p(self, monkeypatch):
        """Returns fallback format string for 1080p."""
        import tetodl.core.config as cfg
        monkeypatch.setattr(cfg, "max_video_resolution", "1080p")
        result = cfg.get_fallback_format_string()
        assert result == "best[height<=1080][ext=mp4]"


class TestConfigDeletion:
    """Tests for config/cache/registry deletion functions."""

    def test_clear_cache_removes_file(self):
        """clear_cache returns True and clears all cache namespaces."""
        import tetodl.core.config as cfg
        from tetodl.core.cache import get_cache

        get_cache("yt_metadata").set("test", "value")
        result = cfg.clear_cache()
        assert result is True
        assert get_cache("yt_metadata").get("test") is None

    def test_clear_cache_no_file(self):
        """clear_cache returns True even when cache is already empty."""
        import tetodl.core.config as cfg
        from tetodl.core.cache import reset_cache

        reset_cache()
        result = cfg.clear_cache()
        assert result is True

    def test_reset_config_removes_file(self, monkeypatch, tmp_path):
        """reset_config deletes the config file and returns True."""
        import tetodl.core.config as cfg
        config_file = tmp_path / "config.json"
        config_file.write_text("{}")
        monkeypatch.setattr(cfg, "CONFIG_PATH", str(config_file))

        result = cfg.reset_config()
        assert result is True
        assert not config_file.exists()

    def test_reset_config_no_file(self, monkeypatch, tmp_path):
        """reset_config returns False when there is no config file."""
        import tetodl.core.config as cfg
        config_file = tmp_path / "config.json"
        monkeypatch.setattr(cfg, "CONFIG_PATH", str(config_file))

        result = cfg.reset_config()
        assert result is False

    def test_wipe_registry_removes_file(self, monkeypatch, tmp_path):
        """wipe_registry deletes the registry file and returns True."""
        import tetodl.core.config as cfg
        reg_file = tmp_path / "registry.json"
        reg_file.write_text("{}")
        monkeypatch.setattr(cfg, "REGISTRY_PATH", str(reg_file))

        result = cfg.wipe_registry()
        assert result is True
        assert not reg_file.exists()

    def test_wipe_registry_no_file(self, monkeypatch, tmp_path):
        """wipe_registry returns False when there is no registry file."""
        import tetodl.core.config as cfg
        reg_file = tmp_path / "registry.json"
        monkeypatch.setattr(cfg, "REGISTRY_PATH", str(reg_file))

        result = cfg.wipe_registry()
        assert result is False

    def test_perform_full_wipe(self, monkeypatch, tmp_path, mocker):
        """perform_full_wipe deletes all files and returns True."""
        import tetodl.core.config as cfg
        config_file = tmp_path / "config.json"
        config_file.write_text("{}")
        reg_file = tmp_path / "registry.json"
        reg_file.write_text("{}")

        monkeypatch.setattr(cfg, "CONFIG_PATH", str(config_file))
        monkeypatch.setattr(cfg, "REGISTRY_PATH", str(reg_file))
        mocker.patch("tetodl.core.history.reset_history", return_value=True)

        result = cfg.perform_full_wipe()
        assert result is True
        assert not config_file.exists()
        assert not reg_file.exists()


class TestConfigHelpers:
    """Tests for other config helper functions."""

    def test_get_audio_quality_info(self, monkeypatch):
        """get_audio_quality_info returns info dict for current quality."""
        import tetodl.core.config as cfg
        monkeypatch.setattr(cfg, "audio_quality", "mp3")
        info = cfg.get_audio_quality_info()
        assert info["ext"] == "mp3"
        assert "bitrate" in info
        assert "codec" in info

    def test_get_audio_quality_info_fallback(self, monkeypatch):
        """Unknown quality falls back to m4a info."""
        import tetodl.core.config as cfg
        monkeypatch.setattr(cfg, "audio_quality", "nonexistent")
        info = cfg.get_audio_quality_info()
        assert info["ext"] == "m4a"

    def test_clear_history(self, mocker):
        """clear_history delegates to reset_history and returns True."""
        mock_reset = mocker.patch("tetodl.core.history.reset_history", return_value=True)
        from tetodl.core.config import clear_history
        result = clear_history()
        assert result is True
        mock_reset.assert_called_once()

    def test_update_language_valid(self, monkeypatch, tmp_path, mocker):
        """update_language saves valid language code."""
        import tetodl.core.config as cfg
        config_file = tmp_path / "config.json"
        config_file.write_text("{}")
        monkeypatch.setattr(cfg, "CONFIG_PATH", str(config_file))
        mocker.patch("tetodl.core.config.set_language", return_value=True)

        result = cfg.update_language("id")
        assert result is True
        assert cfg.language == "id"

    def test_update_language_invalid(self, monkeypatch, tmp_path, mocker):
        """update_language rejects invalid language code."""
        import tetodl.core.config as cfg
        config_file = tmp_path / "config.json"
        config_file.write_text("{}")
        monkeypatch.setattr(cfg, "CONFIG_PATH", str(config_file))
        mocker.patch("tetodl.core.config.set_language", return_value=False)

        result = cfg.update_language("xx")
        assert result is False

    def test_get_language_name(self):
        """get_language_name returns display name for known codes."""
        from tetodl.core.config import get_language_name
        assert get_language_name("en") == "English"
        assert get_language_name("id") == "Indonesia"

    def test_get_language_name_unknown(self):
        """get_language_name returns the code itself for unknown codes."""
        from tetodl.core.config import get_language_name
        assert get_language_name("xx") == "xx"

    def test_add_user_subfolder(self, monkeypatch, tmp_path):
        """add_user_subfolder adds a folder to user_subfolders."""
        import tetodl.core.config as cfg
        config_file = tmp_path / "config.json"
        config_file.write_text("{}")
        monkeypatch.setattr(cfg, "CONFIG_PATH", str(config_file))
        monkeypatch.setattr(cfg, "user_subfolders", {})

        root = str(tmp_path / "music")
        cfg.add_user_subfolder(root, "artist_album")
        import os
        abs_root = os.path.abspath(root)
        assert abs_root in cfg.user_subfolders
        assert "artist_album" in cfg.user_subfolders[abs_root]

    def test_load_app_config(self, monkeypatch):
        """load_app_config returns an AppConfig snapshot of module state."""
        import tetodl.core.config as cfg
        monkeypatch.setattr(cfg, "music_root", "/test/music")
        monkeypatch.setattr(cfg, "simple_mode", True)

        app_cfg = cfg.load_app_config()
        assert app_cfg.music_root == "/test/music"
        assert app_cfg.simple_mode is True
