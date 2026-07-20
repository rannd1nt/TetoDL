

from tetodl.core.models import (
    AppConfig,
    CoverResult,
    DownloadedFile,
    LyricsMetadata,
    MediaInfo,
    PipelineContext,
)
from tetodl.pipeline.steps.lyrics import LyricsStep


class TestLyricsStep:
    """Tests for LyricsStep."""

    def test_skip_lyrics_when_disabled(self, app_config: AppConfig):
        """Returns ctx unchanged when lyrics_mode is disabled."""
        config = app_config.model_copy(update={"lyrics_mode": False})
        step = LyricsStep()
        ctx = PipelineContext(
            config=config,
            url="https://youtube.com/watch?v=test",
            target_dir="/tmp",
            media_type="audio",
        )
        result = step(ctx)
        assert result is ctx
        assert result.lyrics_embedded is False

    def test_skip_lyrics_for_video(self, app_config: AppConfig):
        """Returns ctx unchanged when media_type is video."""
        config = app_config.model_copy(update={"lyrics_mode": True})
        step = LyricsStep()
        ctx = PipelineContext(
            config=config,
            url="https://youtube.com/watch?v=test",
            target_dir="/tmp",
            media_type="video",
        )
        result = step(ctx)
        assert result is ctx
        assert result.lyrics_embedded is False

    def test_skip_when_no_downloaded_file(self, app_config: AppConfig):
        """Returns ctx unchanged when downloaded_file is None."""
        config = app_config.model_copy(update={"lyrics_mode": True})
        step = LyricsStep()
        ctx = PipelineContext(
            config=config,
            url="https://youtube.com/watch?v=test",
            target_dir="/tmp",
            media_type="audio",
        )
        result = step(ctx)
        assert result is ctx
        assert result.lyrics_embedded is False

    def test_skip_when_downloaded_file_missing_on_disk(
        self, app_config: AppConfig,
    ):
        """Returns ctx unchanged when downloaded file does not exist on disk."""
        config = app_config.model_copy(update={"lyrics_mode": True})
        step = LyricsStep()
        dl_file = DownloadedFile(
            path="/nonexistent/path/song.mp3",
            container="mp3",
            title="Test Song",
        )
        ctx = PipelineContext(
            config=config,
            url="https://youtube.com/watch?v=test",
            target_dir="/tmp",
            media_type="audio",
            downloaded_file=dl_file,
        )
        result = step(ctx)
        assert result is ctx
        assert result.lyrics_embedded is False

    def test_resolve_search_terms_uses_cover_metadata(
        self, app_config: AppConfig,
    ):
        """Uses cover_result.metadata for artist/title when available."""
        app_config.model_copy(update={"lyrics_mode": True})
        step = LyricsStep()
        info = MediaInfo(
            id="abc123",
            title="Some Other Title",
            url="https://youtube.com/watch?v=abc123",
            uploader="Some Channel",
        )
        cover_meta = LyricsMetadata(
            artist="Cover Artist",
            title="Cover Title",
        )
        cover = CoverResult(
            thumbnail_path="/tmp/thumb.jpg",
            metadata=cover_meta,
        )
        artist, title = step._resolve_search_terms(info, cover)
        assert artist == "Cover Artist"
        assert title == "Cover Title"

    def test_resolve_search_terms_parses_title_pattern(
        self, app_config: AppConfig,
    ):
        """Parses artist - title pattern from media_info.title."""
        step = LyricsStep()
        info = MediaInfo(
            id="abc123",
            title="Artist Name - Song Title (Official Video)",
            url="https://youtube.com/watch?v=abc123",
            uploader="Some Channel",
        )
        artist, title = step._resolve_search_terms(info, None)
        assert artist == "Artist Name"
        assert title == "Song Title"

    def test_resolve_search_terms_falls_back_to_uploader_and_track(
        self, app_config: AppConfig,
    ):
        """Falls back to info.artist/info.track when no cover metadata."""
        step = LyricsStep()
        info = MediaInfo(
            id="abc123",
            title="Video Title",
            url="https://youtube.com/watch?v=abc123",
            uploader="Artist Channel",
            artist="Artist Name",
            track="Track Name",
        )
        artist, title = step._resolve_search_terms(info, None)
        assert artist == "Artist Name"
        assert title == "Track Name"

    def test_resolve_search_terms_falls_back_to_uploader_and_title(
        self, app_config: AppConfig,
    ):
        """Falls back to uploader/title when artist/track are None and no dash pattern."""
        step = LyricsStep()
        info = MediaInfo(
            id="abc123",
            title="Video Title",
            url="https://youtube.com/watch?v=abc123",
            uploader="Artist Channel - Topic",
        )
        artist, title = step._resolve_search_terms(info, None)
        assert artist == "Artist Channel"
        assert title == "Video Title"
