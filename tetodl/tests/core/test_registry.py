import sys

import pytest


class TestRegistry:
    """Tests for the download registry system."""

    @pytest.fixture
    def fresh_registry(self, monkeypatch, tmp_path):
        """Create a RegistryManager with isolated temp paths."""
        reg_path = tmp_path / "registry.json"
        reg_path.write_text("{}")
        # Patch REGISTRY_PATH on the actual module (not the shadowing attribute)
        reg_module = sys.modules["tetodl.core.registry"]
        monkeypatch.setattr(reg_module, "REGISTRY_PATH", str(reg_path))
        from tetodl.core.registry import RegistryManager
        return RegistryManager()

    @pytest.fixture
    def base(self, tmp_path):
        return tmp_path

    def test_is_cached(self, fresh_registry, base):
        """check_existing returns (False, None) for an uncached file."""
        found, meta = fresh_registry.check_existing("nonexistent_id", "audio", str(base))
        assert found is False
        assert meta is None

    def test_register_download(self, fresh_registry, base):
        """register_download adds an entry to the registry."""
        path = str(base / "music" / "song.mp3")
        fresh_registry.register_download(
            video_id="vid123",
            file_path=path,
            content_type="audio/mp3",
            metadata={"title": "My Song", "artist": "Artist", "album": "Album"},
        )

        assert "vid123" in fresh_registry.data
        assert "audio" in fresh_registry.data["vid123"]
        entry = fresh_registry.data["vid123"]["audio"]
        assert path in entry["paths"]
        assert entry["t"] == "My Song"
        assert entry["a"] == "Artist"

    def test_register_download_increments_count(self, fresh_registry, base):
        """register_download increments the counter on each call."""
        fresh_registry.register_download("vid1", str(base / "s1.mp3"), "audio", {"title": "S1"})
        fresh_registry.register_download("vid1", str(base / "s2.mp3"), "audio", {"title": "S2"})
        assert fresh_registry.data["vid1"]["audio"]["c"] == 2

    def test_register_multiple_types(self, fresh_registry, base):
        """register_download separates audio and video entries."""
        fresh_registry.register_download("vid1", str(base / "a.mp3"), "audio", {"title": "A"})
        fresh_registry.register_download("vid1", str(base / "v.mp4"), "video", {"title": "V"})

        assert "audio" in fresh_registry.data["vid1"]
        assert "video" in fresh_registry.data["vid1"]

    def test_update_path(self, fresh_registry, tmp_path):
        """update_path moves a path from old to new location."""
        old = str(tmp_path / "old" / "song.mp3")
        new = str(tmp_path / "new" / "song.mp3")

        fresh_registry.register_download("vid1", old, "audio", {"title": "S1"})
        fresh_registry.update_path(old, new)

        entry = fresh_registry.data["vid1"]["audio"]
        assert old not in entry["paths"]
        assert new in entry["paths"]

    def test_update_path_no_match(self, fresh_registry, base):
        """update_path does nothing when old_path is not registered."""
        fresh_registry.register_download("vid1", str(base / "s1.mp3"), "audio", {"title": "S1"})
        fresh_registry.update_path(str(base / "nonexistent" / "old.mp3"), str(base / "new.mp3"))

        assert len(fresh_registry.data["vid1"]["audio"]["paths"]) == 1

    def test_register_download_empty_id(self, fresh_registry, base):
        """register_download exits early when video_id is empty."""
        fresh_registry.register_download("", str(base / "s.mp3"), "audio", {"title": "T"})
        assert fresh_registry.data == {}

    def test_register_download_empty_content_type(self, fresh_registry, base):
        """register_download exits early when content_type is empty."""
        fresh_registry.register_download("vid1", str(base / "s.mp3"), "", {"title": "T"})
        assert "vid1" not in fresh_registry.data

    def test_reset(self, fresh_registry, base):
        """reset clears all data and removes the file."""
        fresh_registry.register_download("vid1", str(base / "s.mp3"), "audio", {"title": "T"})
        fresh_registry.reset()
        assert fresh_registry.data == {}

    def test_check_existing_found(self, fresh_registry, tmp_path):
        """check_existing returns (True, metadata) when file exists in target folder."""
        music_dir = tmp_path / "music"
        music_dir.mkdir()
        song = music_dir / "song.mp3"
        song.write_text("content")

        fresh_registry.register_download("vid1", str(song), "audio", {"title": "S1"})
        found, meta = fresh_registry.check_existing("vid1", "audio", str(music_dir))
        assert found is True
        assert meta["title"] == "S1"

    def test_check_existing_audio_category(self, fresh_registry, tmp_path):
        """check_existing categorises 'music' content_type as audio."""
        music_dir = tmp_path / "music"
        music_dir.mkdir()
        song = music_dir / "song.mp3"
        song.write_text("content")

        fresh_registry.register_download("vid1", str(song), "music", {"title": "S1"})
        found, meta = fresh_registry.check_existing("vid1", "music", str(music_dir))
        assert found is True

    def test_check_existing_missing_type(self, fresh_registry, base):
        """check_existing returns (False, None) when content_type not registered."""
        fresh_registry.register_download("vid1", str(base / "a.mp3"), "audio", {"title": "A"})
        found, meta = fresh_registry.check_existing("vid1", "video", str(base))
        assert found is False
        assert meta is None
