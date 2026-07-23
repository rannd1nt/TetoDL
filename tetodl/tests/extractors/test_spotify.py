from __future__ import annotations

from unittest.mock import patch

import pytest

from tetodl.core.step import PipelineError
from tetodl.extractors.spotify import SpotifyExtractor


class TestSpotifyExtractorHandles:
    def test_handles_spotify_url(self):
        assert SpotifyExtractor.handles("https://open.spotify.com/track/abc123")

    def test_handles_spotify_playlist(self):
        assert SpotifyExtractor.handles("https://open.spotify.com/playlist/pl123")

    def test_handles_spotify_album(self):
        assert SpotifyExtractor.handles("https://open.spotify.com/album/al456")

    def test_rejects_youtube_url(self):
        assert not SpotifyExtractor.handles("https://youtube.com/watch?v=abc")

    def test_rejects_random_url(self):
        assert not SpotifyExtractor.handles("https://example.com")


class TestSpotifyExtractorExtract:
    def test_extract_track_returns_single(self):
        fake_tracks = [
            _fake_track(name="Test Song", artist="Test Artist", album="Test Album"),
        ]
        with patch("tetodl.extractors.spotify.SpotifyResolver") as MockResolver:
            MockResolver.return_value.resolve.return_value = fake_tracks
            extractor = SpotifyExtractor()
            info = extractor.extract("https://open.spotify.com/track/abc")

        assert info.title == "Test Song"
        assert not info.is_playlist
        assert info.entries is None
        assert info.artist == "Test Artist"
        assert info.track == "Test Song"

    def test_extract_playlist_returns_entries(self):
        fake_tracks = [
            _fake_track(name="Song A", artist="Artist A"),
            _fake_track(name="Song B", artist="Artist B"),
        ]
        with patch("tetodl.extractors.spotify.SpotifyResolver") as MockResolver:
            MockResolver.return_value.resolve.return_value = fake_tracks
            extractor = SpotifyExtractor()
            info = extractor.extract("https://open.spotify.com/playlist/pl")

        assert info.is_playlist
        assert info.entries is not None
        assert len(info.entries) == 2

    def test_extract_empty_tracks_raises(self):
        with patch("tetodl.extractors.spotify.SpotifyResolver") as MockResolver:
            MockResolver.return_value.resolve.return_value = []
            extractor = SpotifyExtractor()
            with pytest.raises(PipelineError, match="No tracks found"):
                extractor.extract("https://open.spotify.com/playlist/empty")

    def test_extract_resolver_error_raises(self):
        with patch("tetodl.extractors.spotify.SpotifyResolver") as MockResolver:
            MockResolver.return_value.resolve.side_effect = ValueError("Boom")
            extractor = SpotifyExtractor()
            with pytest.raises(PipelineError, match="Spotify extraction failed"):
                extractor.extract("https://open.spotify.com/track/bad")


def _fake_track(
    name: str = "Track",
    artist: str = "Artist",
    album: str = "Album",
) -> object:
    from tetodl.core.spotify import SpotifyTrack

    return SpotifyTrack(
        title=name,
        artist=artist,
        artists=[artist],
        album=album,
        duration_ms=200000,
        spotify_id="id123",
        cover_url="https://cover.url",
    )
