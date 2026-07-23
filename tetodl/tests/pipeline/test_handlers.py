
from tetodl.core.models import AppConfig, DownloadResult, DownloadSession


class TestDownloadAudioYoutube:
    """Tests for download_audio_youtube handler."""

    def test_download_audio_youtube_calls_execute(self, mocker):
        """Verify download_audio_youtube calls _execute with correct args."""
        mock_execute = mocker.patch(
            "tetodl.pipeline.handlers._execute",
            return_value=DownloadResult(success=True, file_path="/tmp/song.mp3"),
        )

        from tetodl.pipeline.handlers import download_audio_youtube

        config = AppConfig(music_root="/music")
        session = DownloadSession(url="https://music.youtube.com/watch?v=test")

        result = download_audio_youtube(
            url="https://music.youtube.com/watch?v=test",
            session=session,
            config=config,
        )

        mock_execute.assert_called_once_with(
            url="https://music.youtube.com/watch?v=test",
            session=session,
            config=config,
            ui=mocker.ANY,
            target_root="/music",
            media_type="audio",
            registry_media_type="audio",
            check_youtube_music=True,
        )
        assert result.success is True
        assert result.file_path == "/tmp/song.mp3"


class TestDownloadVideoYoutube:
    """Tests for download_video_youtube handler."""

    def test_download_video_youtube_calls_execute(self, mocker):
        """Verify download_video_youtube calls _execute with correct args."""
        mock_execute = mocker.patch(
            "tetodl.pipeline.handlers._execute",
            return_value=DownloadResult(success=True, file_path="/tmp/video.mp4"),
        )

        from tetodl.pipeline.handlers import download_video_youtube

        config = AppConfig(video_root="/video")
        session = DownloadSession(url="https://youtube.com/watch?v=test")

        result = download_video_youtube(
            url="https://youtube.com/watch?v=test",
            session=session,
            config=config,
        )

        mock_execute.assert_called_once_with(
            url="https://youtube.com/watch?v=test",
            session=session,
            config=config,
            ui=mocker.ANY,
            target_root="/video",
            media_type="video",
            registry_media_type="video",
            check_youtube_music=False,
        )
        assert result.success is True
        assert result.file_path == "/tmp/video.mp4"


class TestDownloadSpotify:
    """Tests for download_spotify handler."""

    def test_download_spotify_empty_tracks(self, mocker):
        """Spotify resolver returning no tracks returns failed DownloadResult."""
        mock_resolver = mocker.patch("tetodl.core.spotify.SpotifyResolver", autospec=True)
        mock_resolver.return_value.resolve_meta.return_value = (None, [])

        from tetodl.pipeline.handlers import download_spotify

        config = AppConfig(music_root="/music")
        session = DownloadSession(url="https://open.spotify.com/playlist/empty")

        result = download_spotify(
            url="https://open.spotify.com/playlist/empty",
            session=session,
            config=config,
        )

        assert result.success is False
        assert result.file_path is None

    def test_download_spotify_single_track(self, mocker):
        """Single track resolves YT Music URL then calls _handle_single."""
        from tetodl.core.spotify import SpotifyTrack

        fake_track = SpotifyTrack(
            title="Test Song",
            artist="Test Artist",
            artists=["Test Artist"],
            album="Test Album",
            duration_ms=200000,
            spotify_id="id123",
            cover_url="",
        )

        mock_resolver = mocker.patch("tetodl.core.spotify.SpotifyResolver", autospec=True)
        mock_resolver.return_value.resolve_meta.return_value = (None, [fake_track])

        mock_search = mocker.patch(
            "tetodl.pipeline.handlers._search_ytmusic",
            return_value="https://music.youtube.com/watch?v=abc123",
        )

        mock_single = mocker.patch(
            "tetodl.pipeline.handlers._handle_single",
            return_value=DownloadResult(success=True, file_path="/music/Test Song - Test Artist.mp3"),
        )

        from tetodl.pipeline.handlers import download_spotify

        config = AppConfig(music_root="/music")
        session = DownloadSession(url="https://open.spotify.com/track/id123")

        result = download_spotify(
            url="https://open.spotify.com/track/id123",
            session=session,
            config=config,
        )

        mock_search.assert_called_once_with("Test Song - Test Artist", target_duration_ms=200000)
        mock_single.assert_called_once()
        call_kwargs = mock_single.call_args.kwargs
        assert call_kwargs["url"] == "https://music.youtube.com/watch?v=abc123"
        assert call_kwargs["media_type"] == "audio"
        assert call_kwargs["is_youtube_music"] is True
        assert result.success is True

    def test_download_spotify_playlist_resolves_all_tracks(self, mocker):
        """Playlist with multiple tracks resolves each and passes to _handle_playlist."""
        from tetodl.core.spotify import SpotifyTrack

        tracks = [
            SpotifyTrack(title="Song A", artist="Art"),
            SpotifyTrack(title="Song B", artist="Art"),
        ]

        mock_resolver = mocker.patch("tetodl.core.spotify.SpotifyResolver", autospec=True)
        mock_resolver.return_value.resolve_meta.return_value = ("My Mix", tracks)

        mock_search = mocker.patch(
            "tetodl.pipeline.handlers._search_ytmusic",
            side_effect=[
                "https://music.youtube.com/watch?v=a1",
                "https://music.youtube.com/watch?v=b2",
            ],
        )

        mock_playlist = mocker.patch(
            "tetodl.pipeline.handlers._handle_playlist",
            return_value=DownloadResult(success=True),
        )

        from tetodl.pipeline.handlers import download_spotify

        config = AppConfig(music_root="/music")
        session = DownloadSession(url="https://open.spotify.com/album/al")

        download_spotify(
            url="https://open.spotify.com/album/al",
            session=session,
            config=config,
        )

        assert mock_search.call_count == 2
        mock_search.assert_any_call("Song A - Art", target_duration_ms=0)
        mock_search.assert_any_call("Song B - Art", target_duration_ms=0)

        call_kwargs = mock_playlist.call_args.kwargs
        assert call_kwargs["content_title"] == "My Mix"
        assert call_kwargs["urls"] == [
            "https://music.youtube.com/watch?v=a1",
            "https://music.youtube.com/watch?v=b2",
        ]

    def test_download_spotify_no_results_returns_failure(self, mocker):
        """When search returns nothing, returns failed DownloadResult."""
        from tetodl.core.spotify import SpotifyTrack

        fake_track = SpotifyTrack(title="Unknown", artist="Nobody")
        mock_resolver = mocker.patch("tetodl.core.spotify.SpotifyResolver", autospec=True)
        mock_resolver.return_value.resolve_meta.return_value = (None, [fake_track])

        mocker.patch(
            "tetodl.pipeline.handlers._search_ytmusic",
            return_value=None,
        )

        from tetodl.pipeline.handlers import download_spotify

        config = AppConfig(music_root="/music")
        session = DownloadSession(url="https://open.spotify.com/track/x")

        result = download_spotify(url="https://open.spotify.com/track/x", session=session, config=config)
        assert result.success is False
        assert result.file_path is None
