
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
