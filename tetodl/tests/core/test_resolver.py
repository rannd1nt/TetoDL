import pytest


class TestConfigResolver:
    """Tests for the ConfigResolver merge logic."""

    def test_merge_overrides_overrides_fields(self):
        """Session overrides take effect on the resolved config."""
        from tetodl.core.models import AppConfig, DownloadSession, SessionOverrides
        from tetodl.core.resolver import ConfigResolver

        base = AppConfig(music_root="/base/music", video_root="/base/video")
        resolver = ConfigResolver(base)
        session = DownloadSession(
            url="https://example.com",
            media_type="audio",
            format="opus",
            quiet=True,
            lyrics=True,
        )
        resolved = resolver.resolve(session)
        assert resolved.audio_quality == "opus"
        assert resolved.quiet is True
        assert resolved.lyrics_mode is True

    def test_merge_overrides_preserves_defaults(self):
        """Non-overridden fields retain their base config values."""
        from tetodl.core.models import AppConfig, DownloadSession
        from tetodl.core.resolver import ConfigResolver

        base = AppConfig(music_root="/base/music", max_video_resolution="1080p", audio_quality="m4a")
        resolver = ConfigResolver(base)
        session = DownloadSession(url="https://example.com", media_type="audio", format="mp3")
        resolved = resolver.resolve(session)
        assert resolved.music_root == "/base/music"
        assert resolved.max_video_resolution == "1080p"
        assert resolved.audio_quality == "mp3"

    def test_resolve_no_base(self):
        """Resolver with no base uses default AppConfig."""
        from tetodl.core.models import DownloadSession
        from tetodl.core.resolver import ConfigResolver

        resolver = ConfigResolver()
        session = DownloadSession(url="https://example.com", media_type="audio")
        resolved = resolver.resolve(session)
        assert resolved.music_root == ""
        assert resolved.audio_quality == "m4a"

    def test_resolve_covers_all_fields(self):
        """Resolver maps all SessionOverrides fields to AppConfig."""
        from tetodl.core.models import AppConfig, DownloadSession, SessionOverrides
        from tetodl.core.resolver import ConfigResolver

        base = AppConfig()
        resolver = ConfigResolver(base)
        session = DownloadSession(
            url="https://example.com",
            media_type="video",
            overrides=SessionOverrides(
                output_path="/out",
                format="mkv",
                codec="h265",
                resolution="1080p",
                group_folder="mygroup",
                lyrics=True,
                romaji=True,
                zip=True,
                m3u=True,
                no_cover=True,
                force_crop=True,
                quiet=True,
                async_mode=True,
            ),
        )
        resolved = resolver.resolve(session)
        assert resolved.music_root == "/out"
        assert resolved.video_root == "/out"
        assert resolved.thumbnail_root == "/out"
        assert resolved.video_container == "mkv"
        assert resolved.video_codec == "h265"
        assert resolved.max_video_resolution == "1080p"
        assert resolved.group_mode == "mygroup"
        assert resolved.lyrics_mode is True
        assert resolved.romaji_mode is True
        assert resolved.zip_mode is True
        assert resolved.create_m3u is True
        assert resolved.no_cover_mode is True
        assert resolved.smart_cover_mode is False
        assert resolved.force_crop is True
        assert resolved.quiet is True
        assert resolved.async_mode is True

    def test_sets_simple_mode_true(self):
        """Resolver always sets simple_mode=True on the resolved config."""
        from tetodl.core.models import AppConfig, DownloadSession
        from tetodl.core.resolver import ConfigResolver

        base = AppConfig(simple_mode=False)
        resolver = ConfigResolver(base)
        session = DownloadSession(url="https://example.com")
        resolved = resolver.resolve(session)
        assert resolved.simple_mode is True

    def test_resolve_cover_smart_cover(self):
        """Setting smart_cover in overrides enables smart and disables no_cover."""
        from tetodl.core.models import AppConfig, DownloadSession, SessionOverrides
        from tetodl.core.resolver import ConfigResolver

        base = AppConfig()
        resolver = ConfigResolver(base)
        session = DownloadSession(
            url="https://example.com",
            overrides=SessionOverrides(smart_cover=True),
        )
        resolved = resolver.resolve(session)
        assert resolved.smart_cover_mode is True
        assert resolved.no_cover_mode is False

    def test_resolve_cover_no_cover(self):
        """Setting no_cover disables smart cover."""
        from tetodl.core.models import AppConfig, DownloadSession, SessionOverrides
        from tetodl.core.resolver import ConfigResolver

        base = AppConfig()
        resolver = ConfigResolver(base)
        session = DownloadSession(
            url="https://example.com",
            overrides=SessionOverrides(no_cover=True),
        )
        resolved = resolver.resolve(session)
        assert resolved.no_cover_mode is True
        assert resolved.smart_cover_mode is False

    def test_m3u_enables_group_mode_if_no_group(self):
        """m3u override enables group_mode when base has no group."""
        from tetodl.core.models import AppConfig, DownloadSession, SessionOverrides
        from tetodl.core.resolver import ConfigResolver

        base = AppConfig(group_mode=False)
        resolver = ConfigResolver(base)
        session = DownloadSession(
            url="https://example.com",
            overrides=SessionOverrides(m3u=True),
        )
        resolved = resolver.resolve(session)
        assert resolved.create_m3u is True
        assert resolved.group_mode is True

    def test_m3u_does_not_override_explicit_group(self):
        """m3u does not override an explicitly set group_folder."""
        from tetodl.core.models import AppConfig, DownloadSession, SessionOverrides
        from tetodl.core.resolver import ConfigResolver

        base = AppConfig(group_mode=False)
        resolver = ConfigResolver(base)
        session = DownloadSession(
            url="https://example.com",
            overrides=SessionOverrides(m3u=True, group_folder="custom"),
        )
        resolved = resolver.resolve(session)
        assert resolved.create_m3u is True
        assert resolved.group_mode == "custom"
