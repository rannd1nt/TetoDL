from __future__ import annotations

from unittest.mock import patch

import pytest

from tetodl.core.spotify import SpotifyParseError, SpotifyResolver


def _fake_embed_html(entity_json: str) -> str:
    return (
        '<html><head></head><body>'
        '<script id="__NEXT_DATA__" type="application/json">'
        f'{{"props":{{"pageProps":{{"state":{{"data":{{"entity":{entity_json}}},"settings":{{"session":{{"accessToken":"tok"}}}}}}}}}}}}'
        '</script>'
        '</body></html>'
    )


def _fake_track_entity(
    name: str = "Never Gonna Give You Up",
    artist: str = "Rick Astley",
    track_id: str = "abc123",
    duration: int = 212000,
) -> dict:
    return {
        "type": "track",
        "id": track_id,
        "name": name,
        "title": name,
        "uri": f"spotify:track:{track_id}",
        "artists": [{"name": artist}],
        "duration": duration,
        "isPlayable": True,
        "visualIdentity": {
            "image": [
                {"url": "https://cover.url", "maxHeight": 300, "maxWidth": 300},
            ],
        },
    }


def _fake_playlist_entry(
    title: str = "Song",
    artist: str = "Artist",
    track_id: str = "t1",
    duration: int = 200000,
) -> dict:
    return {
        "uri": f"spotify:track:{track_id}",
        "uid": "uid123",
        "title": title,
        "subtitle": artist,
        "duration": duration,
        "isPlayable": True,
        "entityType": "track",
    }


class TestSpotifyURLParsing:
    def test_parse_track_url(self):
        url = "https://open.spotify.com/track/abc123"
        resolver = SpotifyResolver()
        with patch.object(
            resolver._client, "get_track",
            return_value=_fake_track_entity(),
        ):
            tracks = resolver.resolve(url)
        assert len(tracks) == 1
        assert tracks[0].title == "Never Gonna Give You Up"
        assert tracks[0].artist == "Rick Astley"

    def test_parse_playlist_url(self):
        url = "https://open.spotify.com/playlist/pl123"
        fake_items = [
            _fake_playlist_entry(title="Song A", artist="Artist A", track_id="a1"),
            _fake_playlist_entry(title="Song B", artist="Artist B", track_id="b2"),
        ]
        resolver = SpotifyResolver()
        with patch.object(
            resolver._client, "get_playlist",
            return_value={"title": "My Playlist", "trackList": fake_items},
        ):
            tracks = resolver.resolve(url)
        assert len(tracks) == 2
        assert tracks[0].title == "Song A"
        assert tracks[1].title == "Song B"

    def test_parse_album_url(self):
        url = "https://open.spotify.com/album/al456"
        fake_items = [
            _fake_playlist_entry(title="Track 1", artist="Artist", track_id="t1"),
            _fake_playlist_entry(title="Track 2", artist="Artist", track_id="t2"),
        ]
        resolver = SpotifyResolver()
        with patch.object(
            resolver._client, "get_album",
            return_value={"title": "My Album", "trackList": fake_items, "visualIdentity": {"image": []}},
        ):
            tracks = resolver.resolve(url)
        assert len(tracks) == 2

    def test_parse_invalid_url_raises(self):
        resolver = SpotifyResolver()
        with pytest.raises(SpotifyParseError):
            resolver.resolve("https://youtube.com/watch?v=abc")


class TestTrackModelConversion:
    def test_entity_to_track_minimal(self):
        entity = {"name": "Test", "artists": None, "visualIdentity": None, "duration": None, "id": None}
        resolver = SpotifyResolver()
        track = resolver._entity_to_track(entity)
        assert track.title == "Test"
        assert track.artist == ""
        assert track.album == ""
        assert track.duration_ms == 0
        assert track.spotify_id == ""
        assert track.cover_url == ""

    def test_entity_to_track_full(self):
        entity = {
            "name": "Test Song",
            "artists": [{"name": "Artist One"}, {"name": "Artist Two"}],
            "duration": 180000,
            "id": "id_xyz",
            "visualIdentity": {
                "image": [{"url": "https://cover.url"}],
            },
        }
        resolver = SpotifyResolver()
        track = resolver._entity_to_track(entity)
        assert track.title == "Test Song"
        assert track.artist == "Artist One"
        assert track.artists == ["Artist One", "Artist Two"]
        assert track.album == ""
        assert track.duration_ms == 180000
        assert track.spotify_id == "id_xyz"
        assert track.cover_url == "https://cover.url"

    def test_entry_to_track(self):
        entry = {
            "uri": "spotify:track:id_xyz",
            "title": "Test Song",
            "subtitle": "Artist One, Artist Two",
            "duration": 180000,
        }
        resolver = SpotifyResolver()
        track = resolver._entry_to_track(entry)
        assert track.title == "Test Song"
        assert track.artist == "Artist One"
        assert track.artists == ["Artist One", "Artist Two"]
        assert track.album == ""
        assert track.duration_ms == 180000
        assert track.spotify_id == "id_xyz"
        assert track.cover_url == ""

    def test_entry_without_artist(self):
        entry = {
            "uri": "spotify:track:id_x",
            "title": "Test",
            "subtitle": "",
            "duration": 100000,
        }
        resolver = SpotifyResolver()
        track = resolver._entry_to_track(entry)
        assert track.artist == ""
        assert track.artists == []

    def test_playlist_skips_entries_without_uri(self):
        fake_items = [
            _fake_playlist_entry(title="Song A", artist="Artist A", track_id="a1"),
            {"title": "Orphan", "duration": 100000},  # no uri
            _fake_playlist_entry(title="Song C", artist="Artist C", track_id="c3"),
        ]
        resolver = SpotifyResolver()
        with patch.object(
            resolver._client, "get_playlist",
            return_value={"title": "PL", "trackList": fake_items},
        ):
            tracks = resolver.resolve("https://open.spotify.com/playlist/pl123")
        assert len(tracks) == 2
        assert tracks[0].title == "Song A"
        assert tracks[1].title == "Song C"


class TestSpotifyClient:
    def test_get_track(self, mocker):
        from tetodl.core.spotify.auth import SpotifyAuth
        from tetodl.core.spotify.client import SpotifyClient

        auth = SpotifyAuth()
        client = SpotifyClient(auth)
        mock_get = mocker.patch.object(client._session, "get")
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = _fake_embed_html(
            '{"type":"track","id":"abc","name":"Test","artists":[{"name":"Art"}],"duration":1000}'
        )

        result = client.get_track("abc")
        assert result["id"] == "abc"
        assert result["type"] == "track"
        mock_get.assert_called_once_with(
            "https://open.spotify.com/embed/track/abc",
            timeout=15,
        )

    def test_get_playlist(self, mocker):
        from tetodl.core.spotify.auth import SpotifyAuth
        from tetodl.core.spotify.client import SpotifyClient

        auth = SpotifyAuth()
        client = SpotifyClient(auth)
        mock_get = mocker.patch.object(client._session, "get")
        tracks_json = '[{"uri":"spotify:track:a","title":"A","subtitle":"Art","duration":1000}]'
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = _fake_embed_html(
            f'{{"type":"playlist","name":"PL","trackList":{tracks_json}}}'
        )

        entity = client.get_playlist("pl")
        assert entity["name"] == "PL"
        assert len(entity["trackList"]) == 1
        assert entity["trackList"][0]["title"] == "A"

    def test_get_album(self, mocker):
        from tetodl.core.spotify.auth import SpotifyAuth
        from tetodl.core.spotify.client import SpotifyClient

        auth = SpotifyAuth()
        client = SpotifyClient(auth)
        mock_get = mocker.patch.object(client._session, "get")
        tracks_json = '[{"uri":"spotify:track:t1","title":"T1","subtitle":"Art","duration":1000}]'
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = _fake_embed_html(
            f'{{"type":"album","name":"AL","trackList":{tracks_json}}}'
        )

        entity = client.get_album("al")
        assert entity["name"] == "AL"
        assert len(entity["trackList"]) == 1

    def test_http_error_raises(self, mocker):
        from tetodl.core.spotify.auth import SpotifyAuth
        from tetodl.core.spotify.client import SpotifyClient

        auth = SpotifyAuth()
        client = SpotifyClient(auth)
        mock_get = mocker.patch.object(client._session, "get")
        mock_get.return_value.status_code = 404

        with pytest.raises(SpotifyParseError, match="HTTP 404"):
            client.get_track("nonexistent")

    def test_missing_next_data_raises(self, mocker):
        from tetodl.core.spotify.auth import SpotifyAuth
        from tetodl.core.spotify.client import SpotifyClient

        auth = SpotifyAuth()
        client = SpotifyClient(auth)
        mock_get = mocker.patch.object(client._session, "get")
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = "<html></html>"

        with pytest.raises(SpotifyParseError, match="No __NEXT_DATA__"):
            client.get_track("x")

    def test_invalid_json_raises(self, mocker):
        from tetodl.core.spotify.auth import SpotifyAuth
        from tetodl.core.spotify.client import SpotifyClient

        auth = SpotifyAuth()
        client = SpotifyClient(auth)
        mock_get = mocker.patch.object(client._session, "get")
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = (
            '<script id="__NEXT_DATA__">not json</script>'
        )

        with pytest.raises(SpotifyParseError, match="Invalid JSON"):
            client.get_track("x")
