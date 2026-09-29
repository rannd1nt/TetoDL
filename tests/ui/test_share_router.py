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

import asyncio
from pathlib import Path
from fastapi import FastAPI, HTTPException
import pytest

from tetodl.ui.share import (
    _resolve_path,
    create_share_router,
    list_entries,
    render_dir_listing,
)


class TestShareRouter:
    def test_resolve_path_valid(self, tmp_path: Path):
        file = tmp_path / "song.mp3"
        file.write_text("audio")
        resolved = _resolve_path(str(tmp_path), "song.mp3")
        assert resolved == str(file.resolve())

    def test_resolve_path_traversal_denied(self, tmp_path: Path):
        with pytest.raises(HTTPException) as exc:
            _resolve_path(str(tmp_path), "../outside.txt", no_parent=True)
        assert exc.value.status_code == 403

    def test_resolve_path_flat_mode(self, tmp_path: Path):
        subdir = tmp_path / "sub"
        subdir.mkdir()
        subfile = subdir / "track.mp3"
        subfile.write_text("track")

        # Accessing subdirectory in flat mode is denied
        with pytest.raises(HTTPException) as exc:
            _resolve_path(str(tmp_path), "sub", flat=True)
        assert exc.value.status_code == 403

        # Accessing nested file in flat mode is denied
        with pytest.raises(HTTPException) as exc2:
            _resolve_path(str(tmp_path), "sub/track.mp3", flat=True)
        assert exc2.value.status_code == 403

    def test_list_entries_flat_filters_subdirs(self, tmp_path: Path):
        (tmp_path / "song1.mp3").write_text("data")
        (tmp_path / "album_folder").mkdir()

        normal_entries = list_entries(str(tmp_path), flat=False)
        assert len(normal_entries) == 2
        assert any(e["is_dir"] for e in normal_entries)

        flat_entries = list_entries(str(tmp_path), flat=True)
        assert len(flat_entries) == 1
        assert flat_entries[0]["name"] == "song1.mp3"
        assert not flat_entries[0]["is_dir"]

    def test_render_dir_listing_flat_view(self, tmp_path: Path):
        entries = [{"name": "track1.m4a", "is_dir": False, "size_str": "5 MB"}]
        html = render_dir_listing(str(tmp_path), "/", entries, flat=True)
        assert "Flat View" in html
        assert "Parent Directory" not in html
        assert "track1.m4a" in html

    def test_router_endpoints_with_flat_mode(self, tmp_path: Path):
        (tmp_path / "direct.mp3").write_text("direct audio")
        subdir = tmp_path / "sub"
        subdir.mkdir()
        (subdir / "nested.mp3").write_text("nested audio")

        router = create_share_router(str(tmp_path), flat=True, no_parent=True)
        app = FastAPI()
        app.include_router(router)

        # Call root
        async def call_route(method, path):
            scope = {
                "type": "http",
                "method": method,
                "path": path,
                "raw_path": path.encode(),
                "query_string": b"",
                "headers": [],
            }
            messages = []
            async def receive():
                return {"type": "http.request", "body": b"", "more_body": False}
            async def send(m):
                messages.append(m)
            await app(scope, receive, send)
            status = 500
            for m in messages:
                if m["type"] == "http.response.start":
                    status = m["status"]
            return status

        # Direct root listing is 200
        status_root = asyncio.run(call_route("GET", "/"))
        assert status_root == 200

        # Subdirectory access in flat mode is 403 Forbidden
        status_sub = asyncio.run(call_route("GET", "/sub"))
        assert status_sub == 403
