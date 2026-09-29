# Copyright 2026 rannd1nt
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import errno
import pytest
from unittest.mock import MagicMock, call

from tetodl.core.domain.tagger import (
    _retry_on_permission_error,
    embed_cover,
    embed_metadata,
    embed_metadata_tags,
)


class TestRetryOnPermissionError:
    """Tests for _retry_on_permission_error helper."""

    def test_succeeds_on_first_attempt(self, mocker):
        mock_sleep = mocker.patch("time.sleep")
        func = MagicMock(return_value="success")

        result = _retry_on_permission_error(func, max_attempts=5, delay=0.01)

        assert result == "success"
        assert func.call_count == 1
        mock_sleep.assert_not_called()

    def test_retries_on_permission_error_and_succeeds(self, mocker):
        mock_sleep = mocker.patch("time.sleep")
        func = MagicMock(
            side_effect=[
                PermissionError("[Errno 13] Permission denied"),
                PermissionError("[Errno 13] Permission denied"),
                "recovered",
            ]
        )

        result = _retry_on_permission_error(func, max_attempts=5, delay=0.05)

        assert result == "recovered"
        assert func.call_count == 3
        assert mock_sleep.call_count == 2
        mock_sleep.assert_has_calls([call(0.05), call(0.1)])

    def test_retries_on_oserror_errno_13(self, mocker):
        mock_sleep = mocker.patch("time.sleep")
        err = OSError("Permission denied")
        err.errno = errno.EACCES
        func = MagicMock(side_effect=[err, "success_eacces"])

        result = _retry_on_permission_error(func, max_attempts=3, delay=0.1)

        assert result == "success_eacces"
        assert func.call_count == 2
        mock_sleep.assert_called_once_with(0.1)

    def test_does_not_retry_on_other_errors(self, mocker):
        mock_sleep = mocker.patch("time.sleep")
        func = MagicMock(side_effect=ValueError("Invalid data"))

        with pytest.raises(ValueError, match="Invalid data"):
            _retry_on_permission_error(func, max_attempts=5, delay=0.05)

        assert func.call_count == 1
        mock_sleep.assert_not_called()

    def test_exhausts_retries_and_raises_last_error(self, mocker):
        mocker.patch("time.sleep")
        func = MagicMock(side_effect=PermissionError("Locked permanently"))

        with pytest.raises(PermissionError, match="Locked permanently"):
            _retry_on_permission_error(func, max_attempts=4, delay=0.01)

        assert func.call_count == 4


class TestEmbedMetadata:
    """Tests for unified embed_metadata and convenience wrappers."""

    def test_embed_metadata_nonexistent_audio_returns_false(self):
        result = embed_metadata("/nonexistent/file.m4a", None, "m4a", None)
        assert result is False

    def test_embed_cover_delegates_to_embed_metadata(self, mocker):
        mock_embed = mocker.patch("tetodl.core.domain.tagger.embed_metadata", return_value=True)

        res = embed_cover("/path/audio.mp3", "/path/cover.jpg", "mp3")

        assert res is True
        mock_embed.assert_called_once_with("/path/audio.mp3", "/path/cover.jpg", "mp3", metadata=None)

    def test_embed_metadata_tags_delegates_to_embed_metadata(self, mocker):
        mock_embed = mocker.patch("tetodl.core.domain.tagger.embed_metadata", return_value=True)
        meta = {"title": "Song", "artist": "Artist"}

        res = embed_metadata_tags("/path/audio.mp3", "mp3", meta)

        assert res is True
        mock_embed.assert_called_once_with("/path/audio.mp3", None, "mp3", metadata=meta)
