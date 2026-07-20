import hashlib

import pytest


class TestCache:
    """Tests for the metadata cache system."""

    def test_cache_metadata_read_write(self, monkeypatch, tmp_path):
        """Writing and then reading metadata returns the same data."""
        cache_file = tmp_path / "cache.json"
        monkeypatch.setattr("tetodl.core.cache.CACHE_PATH", str(cache_file))

        from tetodl.core.cache import cache_metadata, get_cached_metadata

        url = "https://example.com/video"
        metadata = {"title": "Test Video", "duration": 120}
        cache_metadata(url, metadata)

        cached = get_cached_metadata(url)
        assert cached is not None
        assert cached["metadata"]["title"] == "Test Video"
        assert cached["metadata"]["duration"] == 120

    def test_get_cached_metadata_missing(self, monkeypatch, tmp_path):
        """get_cached_metadata returns None for an unknown URL."""
        cache_file = tmp_path / "cache.json"
        monkeypatch.setattr("tetodl.core.cache.CACHE_PATH", str(cache_file))

        from tetodl.core.cache import get_cached_metadata

        result = get_cached_metadata("https://example.com/unknown")
        assert result is None

    def test_get_url_hash(self):
        """get_url_hash returns a consistent MD5 hash."""
        from tetodl.core.cache import get_url_hash

        url = "https://example.com/video"
        expected = hashlib.md5(url.encode()).hexdigest()
        assert get_url_hash(url) == expected

    def test_get_url_hash_consistency(self):
        """get_url_hash returns the same hash for the same URL."""
        from tetodl.core.cache import get_url_hash

        url = "https://example.com/video"
        assert get_url_hash(url) == get_url_hash(url)

    def test_get_url_hash_different_urls(self):
        """get_url_hash returns different hashes for different URLs."""
        from tetodl.core.cache import get_url_hash

        assert get_url_hash("https://example.com/a") != get_url_hash("https://example.com/b")

    def test_cache_persists_across_loads(self, monkeypatch, tmp_path):
        """Cached data persists when cache is reloaded from disk."""
        cache_file = tmp_path / "cache.json"
        monkeypatch.setattr("tetodl.core.cache.CACHE_PATH", str(cache_file))

        from tetodl.core.cache import cache_metadata, load_cache

        url = "https://example.com/video"
        cache_metadata(url, {"title": "Test"})

        loaded = load_cache()
        url_hash = hashlib.md5(url.encode()).hexdigest()
        assert url_hash in loaded
        assert loaded[url_hash]["metadata"]["title"] == "Test"

    def test_load_cache_missing_file(self, monkeypatch, tmp_path):
        """load_cache returns empty dict when the cache file doesn't exist."""
        cache_file = tmp_path / "cache.json"
        monkeypatch.setattr("tetodl.core.cache.CACHE_PATH", str(cache_file))

        from tetodl.core.cache import load_cache

        assert load_cache() == {}

    def test_reset_cache_deletes_file(self, monkeypatch, tmp_path):
        """reset_cache removes the cache file and returns True."""
        cache_file = tmp_path / "cache.json"
        cache_file.write_text("{}")
        monkeypatch.setattr("tetodl.core.cache.CACHE_PATH", str(cache_file))

        from tetodl.core.cache import reset_cache

        assert reset_cache() is True
        assert not cache_file.exists()

    def test_reset_cache_no_file(self, monkeypatch, tmp_path):
        """reset_cache returns True even when no cache file exists."""
        cache_file = tmp_path / "cache.json"
        monkeypatch.setattr("tetodl.core.cache.CACHE_PATH", str(cache_file))

        from tetodl.core.cache import reset_cache

        assert reset_cache() is True

    def test_get_cache_size(self, monkeypatch, tmp_path):
        """get_cache_size returns a human-readable string."""
        cache_file = tmp_path / "cache.json"
        cache_file.write_text('{"key": "value"}')
        monkeypatch.setattr("tetodl.core.cache.CACHE_PATH", str(cache_file))

        from tetodl.core.cache import get_cache_size

        size_str = get_cache_size()
        assert isinstance(size_str, str)
        assert size_str != "Unknown"

    def test_get_cache_size_no_file(self, monkeypatch, tmp_path):
        """get_cache_size returns '0 B' when no cache file exists."""
        cache_file = tmp_path / "cache.json"
        monkeypatch.setattr("tetodl.core.cache.CACHE_PATH", str(cache_file))

        from tetodl.core.cache import get_cache_size

        assert get_cache_size() == "0 B"
