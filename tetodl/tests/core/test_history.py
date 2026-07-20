import pytest


class TestHistory:
    """Tests for the download history system."""

    @pytest.fixture(autouse=True)
    def _setup(self, monkeypatch, tmp_path, mocker):
        """Reset global state and patch paths for every test."""
        history_file = tmp_path / "history.json"
        monkeypatch.setattr("tetodl.core.history.HISTORY_PATH", str(history_file))
        mocker.patch("tetodl.core.history.console.err")
        mocker.patch("tetodl.core.history.console.ok")
        mocker.patch("tetodl.core.history.registry.register_download")
        import tetodl.core.history as hist
        hist.reset_history()

    def test_add_to_history(self):
        """An entry added via add_to_history appears in history."""
        import tetodl.core.history as hist

        hist.add_to_history(
            id="vid123",
            file_path="/tmp/song.mp3",
            success=True,
            title="Test Song",
            content_type="audio/mp3",
            platform="YouTube Audio",
            download_type="audio",
            duration=180,
        )

        assert len(hist._download_history) == 1
        entry = hist._download_history[0]
        assert entry["id"] == "vid123"
        assert entry["title"] == "Test Song"
        assert entry["success"] is True

    def test_add_to_history_dedup(self):
        """Adding the same ID twice replaces the old entry."""
        import tetodl.core.history as hist

        hist.add_to_history(
            id="vid123", file_path="/tmp/v1.mp3", success=True,
            title="V1", content_type="audio/mp3", platform="YouTube Audio",
            download_type="audio", duration=100,
        )
        hist.add_to_history(
            id="vid123", file_path="/tmp/v2.mp3", success=True,
            title="V2", content_type="audio/mp3", platform="YouTube Audio",
            download_type="audio", duration=200,
        )

        matching = [e for e in hist._download_history if e["id"] == "vid123"]
        assert len(matching) == 1
        assert matching[0]["file_path"] == "/tmp/v2.mp3"

    def test_get_history_stats_empty(self):
        """get_history_stats returns all zeros when history is empty."""
        import tetodl.core.history as hist

        hist.reset_history()
        stats = hist.get_history_stats()
        assert stats["yt_video"] == 0
        assert stats["yt_audio"] == 0
        assert stats["yt_music"] == 0
        assert stats["spotify"] == 0
        assert stats["total_duration"] == 0

    def test_get_history_stats_with_entries(self):
        """get_history_stats returns correct counts for different platforms."""
        import tetodl.core.history as hist

        hist.add_to_history(
            id="v1", file_path="/tmp/v1.mp4", success=True,
            title="V1", content_type="video/mp4", platform="YouTube Video",
            download_type="video", duration=120,
        )
        hist.add_to_history(
            id="v2", file_path="/tmp/v2.mp4", success=True,
            title="V2", content_type="video/mp4", platform="YouTube Video",
            download_type="video", duration=60,
        )
        hist.add_to_history(
            id="a1", file_path="/tmp/a1.m4a", success=True,
            title="A1", content_type="audio/m4a", platform="YouTube Audio",
            download_type="audio", duration=240,
        )

        stats = hist.get_history_stats()
        assert stats["yt_video"] == 2
        assert stats["yt_audio"] == 1
        assert stats["yt_music"] == 0
        assert stats["spotify"] == 0
        assert stats["total_duration"] == 420

    def test_reset_history(self):
        """reset_history clears all entries and returns True."""
        import tetodl.core.history as hist

        hist.add_to_history("v1", "/tmp/v1.mp3", True, "T1", "audio", "YT", "audio", 100)
        hist.add_to_history("v2", "/tmp/v2.mp3", True, "T2", "audio", "YT", "audio", 200)
        assert len(hist._download_history) == 2

        result = hist.reset_history()
        assert result is True
        assert len(hist._download_history) == 0

    def test_add_to_history_skips_registry_when_no_id(self):
        """add_to_history does not call registry when id is empty."""
        import tetodl.core.history as hist

        hist.add_to_history(
            id="", file_path="/tmp/s.mp3", success=True,
            title="T", content_type="audio", platform="YT",
            download_type="audio", duration=0,
        )
        assert len(hist._download_history) == 1

    def test_save_and_load_persistence(self, monkeypatch, tmp_path):
        """History entries persist across save/load cycles."""
        history_file = tmp_path / "history.json"
        monkeypatch.setattr("tetodl.core.history.HISTORY_PATH", str(history_file))

        import tetodl.core.history as hist

        hist.add_to_history("v1", "/tmp/v1.mp3", True, "T1", "audio", "YT", "audio", 100)
        assert history_file.exists()

        hist._download_history.clear()

        hist.load_history()
        assert len(hist._download_history) == 1
        assert hist._download_history[0]["id"] == "v1"

    def test_get_history_stats_skips_failed(self):
        """get_history_stats only counts successful entries."""
        import tetodl.core.history as hist

        hist.add_to_history("v1", "/tmp/v1.mp4", True, "V1", "video", "YouTube Video", "video", 120)
        hist.add_to_history("v2", "/tmp/v2.mp4", False, "V2", "video", "YouTube Video", "video", 60)

        stats = hist.get_history_stats()
        assert stats["yt_video"] == 1
        assert stats["total_duration"] == 120
