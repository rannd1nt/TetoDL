import pytest
from pydantic import ValidationError


class TestAppConfig:
    """Tests for the root AppConfig model."""

    def test_defaults(self):
        """All AppConfig fields have expected default values."""
        from tetodl.core.models import AppConfig
        cfg = AppConfig()
        assert cfg.music_root == ""
        assert cfg.video_root == ""
        assert cfg.thumbnail_root == ""
        assert cfg.simple_mode is False
        assert cfg.async_mode is False
        assert cfg.quiet is False
        assert cfg.smart_cover_mode is True
        assert cfg.no_cover_mode is False
        assert cfg.force_crop is False
        assert cfg.thumbnail_format == "jpg"
        assert cfg.group_mode is False
        assert cfg.force_grouping_on_share is False
        assert cfg.lyrics_mode is False
        assert cfg.romaji_mode is False
        assert cfg.zip_mode is False
        assert cfg.create_m3u is False
        assert cfg.skip_existing_files is True
        assert cfg.max_video_resolution == "720p"
        assert cfg.audio_quality == "m4a"
        assert cfg.video_container == "mp4"
        assert cfg.video_codec == "default"
        assert cfg.header_style == "default"
        assert cfg.progress_style == "minimal"
        assert cfg.language == "en"
        assert cfg.media_scanner_enabled is False
        assert cfg.jitter_min == 3.0
        assert cfg.jitter_max == 5.0
        assert cfg.max_retries == 3
        assert cfg.async_workers == 3
        assert cfg.daemon_default_temp is True
        assert cfg.daemon_cleanup_interval == 3600
        assert cfg.verified_dependencies is False

    def test_forbids_extra(self):
        """AppConfig raises ValidationError for unknown fields."""
        from tetodl.core.models import AppConfig
        with pytest.raises(ValidationError):
            AppConfig(nonexistent_field=True)  # type: ignore[call-arg]

    def test_sub_config_audio(self):
        """AppConfig.audio returns AudioConfig with quality from audio_quality."""
        from tetodl.core.models import AppConfig
        cfg = AppConfig(audio_quality="mp3")
        audio = cfg.audio
        assert audio.quality == "mp3"

    def test_sub_config_video(self):
        """AppConfig.video returns VideoConfig populated from flat fields."""
        from tetodl.core.models import AppConfig
        cfg = AppConfig(video_container="mkv", video_codec="h265", max_video_resolution="1080p")
        video = cfg.video
        assert video.container == "mkv"
        assert video.codec == "h265"
        assert video.max_resolution == "1080p"

    def test_sub_config_cover(self):
        """AppConfig.cover returns CoverConfig populated from flat fields."""
        from tetodl.core.models import AppConfig
        cfg = AppConfig(smart_cover_mode=False, no_cover_mode=True, force_crop=True)
        cover = cfg.cover
        assert cover.smart_mode is False
        assert cover.disabled is True
        assert cover.force_crop is True

    def test_sub_config_lyrics(self):
        """AppConfig.lyrics returns LyricsConfig from flat fields."""
        from tetodl.core.models import AppConfig
        cfg = AppConfig(lyrics_mode=True, romaji_mode=True)
        lyrics = cfg.lyrics
        assert lyrics.enabled is True
        assert lyrics.romaji is True

    def test_sub_config_download(self):
        """AppConfig.download returns DownloadConfig from flat fields."""
        from tetodl.core.models import AppConfig
        cfg = AppConfig(simple_mode=False, quiet=True, skip_existing_files=False, progress_style="detailed")
        dl = cfg.download
        assert dl.simple_mode is False
        assert dl.quiet is True
        assert dl.skip_existing is False
        assert dl.progress_style == "detailed"

    def test_sub_config_library(self):
        """AppConfig.library returns LibraryConfig from flat fields."""
        from tetodl.core.models import AppConfig
        cfg = AppConfig(music_root="/music", group_mode=True, zip_mode=True, create_m3u=True)
        lib = cfg.library
        assert lib.music_root == "/music"
        assert lib.group_mode is True
        assert lib.zip_mode is True
        assert lib.create_m3u is True

    def test_sub_config_system(self):
        """AppConfig.system returns SystemConfig from flat fields."""
        from tetodl.core.models import AppConfig
        cfg = AppConfig(max_retries=5, async_workers=8, jitter_min=2.0, jitter_max=6.0)
        sys_cfg = cfg.system
        assert sys_cfg.max_retries == 5
        assert sys_cfg.async_workers == 8
        assert sys_cfg.jitter_min == 2.0
        assert sys_cfg.jitter_max == 6.0

    def test_sub_config_daemon(self):
        """AppConfig.daemon returns DaemonConfig from flat fields."""
        from tetodl.core.models import AppConfig
        cfg = AppConfig(daemon_default_temp=False, daemon_cleanup_interval=7200)
        daemon = cfg.daemon
        assert daemon.default_temp is False
        assert daemon.cleanup_interval == 7200


class TestSessionOverrides:
    """Tests for SessionOverrides model."""

    def test_defaults(self):
        """SessionOverrides fields have expected defaults."""
        from tetodl.core.models import SessionOverrides
        o = SessionOverrides()
        assert o.output_path is None
        assert o.format is None
        assert o.codec is None
        assert o.resolution is None
        assert o.cut_range is None
        assert o.playlist_items is None
        assert o.group_folder is False
        assert o.lyrics is False
        assert o.romaji is False
        assert o.zip is False
        assert o.m3u is False
        assert o.smart_cover is False
        assert o.no_cover is False
        assert o.force_crop is False
        assert o.quiet is False
        assert o.async_mode is False


class TestDownloadSession:
    """Tests for DownloadSession model."""

    def test_url_not_empty_strips_whitespace(self):
        """url_not_empty validator strips leading/trailing whitespace."""
        from tetodl.core.models import DownloadSession
        session = DownloadSession(url="  https://example.com  ")
        assert session.url == "https://example.com"

    def test_url_empty_preserved(self):
        """Empty URL is preserved as empty string."""
        from tetodl.core.models import DownloadSession
        session = DownloadSession(url="")
        assert session.url == ""

    def test_merged_overrides_flat_takes_precedence(self):
        """Flat fields in DownloadSession override structured overrides."""
        from tetodl.core.models import DownloadSession, SessionOverrides
        session = DownloadSession(
            url="https://example.com",
            format="mp3",
            lyrics=True,
            overrides=SessionOverrides(format="opus", lyrics=False),
        )
        merged = session.merged_overrides
        assert merged.format == "mp3"
        assert merged.lyrics is True

    def test_merged_overrides_structured_used_when_flat_is_default(self):
        """Structured overrides apply when flat fields are at defaults."""
        from tetodl.core.models import DownloadSession, SessionOverrides
        session = DownloadSession(
            url="https://example.com",
            overrides=SessionOverrides(quiet=True, async_mode=True),
        )
        merged = session.merged_overrides
        assert merged.quiet is True
        assert merged.async_mode is True

    def test_config_updates_output_path(self):
        """config_updates maps output_path to music/video/thumbnail_root."""
        from tetodl.core.models import DownloadSession
        session = DownloadSession(url="https://example.com", output_path="/out")
        updates = session.config_updates()
        assert updates["music_root"] == "/out"
        assert updates["video_root"] == "/out"
        assert updates["thumbnail_root"] == "/out"

    def test_config_updates_format_for_audio(self):
        """config_updates maps format to audio_quality for audio media_type."""
        from tetodl.core.models import DownloadSession
        session = DownloadSession(url="https://example.com", format="mp3", media_type="audio")
        updates = session.config_updates()
        assert updates["audio_quality"] == "mp3"

    def test_config_updates_format_for_video(self):
        """config_updates maps format to video_container for video media_type."""
        from tetodl.core.models import DownloadSession
        session = DownloadSession(url="https://example.com", format="mkv", media_type="video")
        updates = session.config_updates()
        assert updates["video_container"] == "mkv"

    def test_config_updates_toggles(self):
        """config_updates includes all toggle flags when set."""
        from tetodl.core.models import DownloadSession
        session = DownloadSession(
            url="https://example.com",
            lyrics=True,
            romaji=True,
            zip=True,
            quiet=True,
            async_mode=True,
        )
        updates = session.config_updates()
        assert updates["lyrics_mode"] is True
        assert updates["romaji_mode"] is True
        assert updates["zip_mode"] is True
        assert updates["quiet"] is True
        assert updates["async_mode"] is True

    def test_merged_overrides_preserves_all_fields(self):
        """merged_overrides preserves all SessionOverrides fields."""
        from tetodl.core.models import DownloadSession
        session = DownloadSession(
            url="https://example.com",
            output_path="/out",
            format="mp3",
            codec="h264",
            resolution="1080p",
            cut_range=(10.0, 20.0),
            playlist_items={1, 2, 3},
            group_folder="mygroup",
            lyrics=True,
            romaji=True,
            zip=True,
            m3u=True,
            smart_cover=True,
            no_cover=True,
            force_crop=True,
            quiet=True,
            async_mode=True,
        )
        merged = session.merged_overrides
        assert merged.output_path == "/out"
        assert merged.format == "mp3"
        assert merged.codec == "h264"
        assert merged.resolution == "1080p"
        assert merged.cut_range == (10.0, 20.0)
        assert merged.playlist_items == {1, 2, 3}
        assert merged.group_folder == "mygroup"
        assert merged.lyrics is True
        assert merged.romaji is True
        assert merged.zip is True
        assert merged.m3u is True
        assert merged.smart_cover is True
        assert merged.no_cover is True
        assert merged.force_crop is True
        assert merged.quiet is True
        assert merged.async_mode is True


class TestPipelineContext:
    """Tests for PipelineContext dataclass."""

    def test_defaults_no_downloaded_file(self):
        """PipelineContext defaults have no downloaded_file set."""
        from tetodl.core.models import AppConfig, PipelineContext
        ctx = PipelineContext(
            config=AppConfig(),
            url="https://example.com",
            target_dir="/tmp/out",
        )
        assert ctx.downloaded_file is None
        assert ctx.media_info is None
        assert ctx.cover_result is None
        assert ctx.classification is None
        assert ctx.error is None
        assert ctx.lyrics_embedded is False
        assert ctx.media_type == "audio"
        assert ctx.is_youtube_music is False


class TestDownloadResult:
    """Tests for DownloadResult model."""

    def test_getitem(self):
        """DownloadResult supports dict-style __getitem__ access."""
        from tetodl.core.models import DownloadResult
        result = DownloadResult(success=True, file_path="/tmp/file.mp3", title="My Song")
        assert result["success"] is True
        assert result["file_path"] == "/tmp/file.mp3"
        assert result["title"] == "My Song"

    def test_get_method(self):
        """DownloadResult.get returns default for missing keys."""
        from tetodl.core.models import DownloadResult
        result = DownloadResult(success=True)
        assert result.get("success") is True
        assert result.get("nonexistent", "fallback") == "fallback"

    def test_contains(self):
        """DownloadResult supports 'in' operator."""
        from tetodl.core.models import DownloadResult
        result = DownloadResult(success=True)
        assert "success" in result
        assert "missing" not in result

    def test_defaults(self):
        """DownloadResult fields have expected defaults for optional fields."""
        from tetodl.core.models import DownloadResult
        result = DownloadResult(success=True)
        assert result.file_path is None
        assert result.skipped is False
        assert result.cancelled is False
        assert result.is_playlist is False
        assert result.is_staging is False
        assert result.title is None
        assert result.reason is None


class TestSubModels:
    """Tests for smaller domain models."""

    def test_audio_config_defaults(self):
        """AudioConfig defaults quality to m4a."""
        from tetodl.core.models import AudioConfig
        cfg = AudioConfig()
        assert cfg.quality == "m4a"

    def test_video_config_defaults(self):
        """VideoConfig defaults match expected values."""
        from tetodl.core.models import VideoConfig
        cfg = VideoConfig()
        assert cfg.container == "mp4"
        assert cfg.codec == "h264"
        assert cfg.max_resolution == "720p"

    def test_cover_config_defaults(self):
        """CoverConfig defaults."""
        from tetodl.core.models import CoverConfig
        cfg = CoverConfig()
        assert cfg.smart_mode is True
        assert cfg.disabled is False
        assert cfg.force_crop is False

    def test_lyrics_config_defaults(self):
        """LyricsConfig defaults."""
        from tetodl.core.models import LyricsConfig
        cfg = LyricsConfig()
        assert cfg.enabled is False
        assert cfg.romaji is False

    def test_media_info_required_fields(self):
        """MediaInfo requires id, title, and url."""
        from tetodl.core.models import MediaInfo
        info = MediaInfo(id="abc123", title="Test", url="https://example.com")
        assert info.id == "abc123"
        assert info.title == "Test"
        assert info.url == "https://example.com"

    def test_media_info_defaults_optional(self):
        """MediaInfo optional fields have proper defaults."""
        from tetodl.core.models import MediaInfo
        info = MediaInfo(id="abc", title="T", url="https://e.com")
        assert info.duration == 0
        assert info.uploader == ""
        assert info.artist is None
        assert info.thumbnail is None
        assert info.thumbnails == []
        assert info.is_playlist is False

    def test_downloaded_file_minimal(self):
        """DownloadedFile requires path, container, and title."""
        from tetodl.core.models import DownloadedFile
        f = DownloadedFile(path="/tmp/f.mp3", container="mp3", title="Song")
        assert f.path == "/tmp/f.mp3"
        assert f.container == "mp3"
        assert f.title == "Song"

    def test_classification_defaults(self):
        """Classification defaults."""
        from tetodl.core.models import Classification
        c = Classification()
        assert c.is_playlist is False
        assert c.existing_result is None

    def test_cover_result_required_fields(self):
        """CoverResult requires thumbnail_path."""
        from tetodl.core.models import CoverResult
        r = CoverResult(thumbnail_path="/tmp/cover.jpg")
        assert r.thumbnail_path == "/tmp/cover.jpg"
        assert r.source == "youtube"
        assert r.cropped is False

    def test_download_target_defaults(self):
        """DownloadTarget defaults."""
        from tetodl.core.models import DownloadTarget
        t = DownloadTarget(output_dir="/out", filename_template="%(title)s", format_string="bestaudio")
        assert t.postprocessors == []
        assert t.cut_range is None
