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
import json
import urllib.parse
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from tetodl.core.domain.server_config import ServerConfig
from tetodl.ui.daemon.api import active_tasks, app
from tetodl.ui.daemon.auth import ACCESS_COOKIE_NAME, REFRESH_COOKIE_NAME
from tetodl.utils.files import TempManager


class ASGIResponse:
    def __init__(self, status_code: int, headers: list[tuple[bytes, bytes]], body: bytes):
        self.status_code = status_code
        self.raw_headers = headers
        self.headers: dict[str, str] = {k.decode("latin1").lower(): v.decode("latin1") for k, v in headers}
        self.content = body

    def json(self) -> Any:
        return json.loads(self.content.decode("utf-8"))

    def get_cookies(self) -> dict[str, str]:
        cookies = {}
        for k, v in self.raw_headers:
            if k.lower() == b"set-cookie":
                cookie_str = v.decode("latin1")
                parts = cookie_str.split(";", 1)[0].split("=", 1)
                if len(parts) == 2:
                    cookies[parts[0].strip()] = parts[1].strip()
        return cookies


class ASGIClient:
    """Lightweight pure-python ASGI test client with session cookies."""

    def __init__(self, asgi_app):
        self.app = asgi_app
        self.cookies: dict[str, str] = {}

    def request(
        self,
        method: str,
        path: str,
        query: dict[str, Any] | str | None = None,
        json_data: Any = None,
        headers: dict[str, str] | None = None,
    ) -> ASGIResponse:
        req_headers = {k.lower(): v for k, v in (headers or {}).items()}

        body = b""
        if json_data is not None:
            body = json.dumps(json_data).encode("utf-8")
            req_headers["content-type"] = "application/json"

        if self.cookies:
            cookie_hdr = "; ".join(f"{k}={v}" for k, v in self.cookies.items())
            req_headers["cookie"] = cookie_hdr

        query_str = ""
        if "?" in path and not query:
            path, query_str = path.split("?", 1)
        elif isinstance(query, dict):
            query_str = urllib.parse.urlencode(query)
        elif isinstance(query, str):
            query_str = query

        header_list = [(k.encode("latin1"), v.encode("latin1")) for k, v in req_headers.items()]

        scope = {
            "type": "http",
            "method": method.upper(),
            "path": path,
            "raw_path": path.encode("ascii"),
            "query_string": query_str.encode("ascii"),
            "headers": header_list,
        }

        messages: list[dict[str, Any]] = []

        async def receive():
            return {"type": "http.request", "body": body, "more_body": False}

        async def send(message):
            messages.append(message)

        async def run_req():
            await self.app(scope, receive, send)

        asyncio.run(run_req())

        status = 500
        resp_headers = []
        body_parts = []

        for m in messages:
            if m["type"] == "http.response.start":
                status = m["status"]
                resp_headers = m.get("headers", [])
            elif m["type"] == "http.response.body":
                body_parts.append(m.get("body", b""))

        resp = ASGIResponse(status, resp_headers, b"".join(body_parts))
        new_cookies = resp.get_cookies()
        for k, v in new_cookies.items():
            if v == '""' or not v:
                self.cookies.pop(k, None)
            else:
                self.cookies[k] = v

        return resp

    def get(self, path: str, **kwargs) -> ASGIResponse:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, json: Any = None, **kwargs) -> ASGIResponse:
        return self.request("POST", path, json_data=json, **kwargs)

    def patch(self, path: str, json: Any = None, **kwargs) -> ASGIResponse:
        return self.request("PATCH", path, json_data=json, **kwargs)


@pytest.fixture
def client():
    return ASGIClient(app)


class TestDaemonSecurity:
    def test_zero_browse_endpoints_removed(self, client: ASGIClient):
        """Verify host browsing and streaming routes return 404."""
        assert client.get("/api/v1/share/browse").status_code == 404
        assert client.get("/api/v1/share/stream").status_code == 404
        assert client.get("/api/v1/share/browse_html").status_code == 404
        assert client.get("/api/v1/share/player").status_code == 404
        assert client.post("/api/v1/share/launch", json={"path": "/"}).status_code == 404

    def test_config_patch_removed(self, client: ASGIClient):
        """Verify PATCH /api/v1/config is rejected."""
        res = client.patch("/api/v1/config", json={"daemon_default_temp": False})
        assert res.status_code == 405  # Method Not Allowed

    def test_auth_status_unauthenticated(self, client: ASGIClient, monkeypatch):
        test_cfg = ServerConfig(teto_password="secretpassword")
        monkeypatch.setattr("tetodl.ui.daemon.api.get_server_config", lambda: test_cfg)

        res = client.get("/api/v1/auth/status")
        assert res.status_code == 200
        data = res.json()
        assert data["authenticated"] is False
        assert data["password_configured"] is True

    def test_auth_verify_success_and_logout(self, client: ASGIClient, monkeypatch):
        test_cfg = ServerConfig(teto_password="mypassword123")
        monkeypatch.setattr("tetodl.ui.daemon.api.get_server_config", lambda: test_cfg)
        monkeypatch.setattr("tetodl.ui.daemon.auth.get_server_config", lambda: test_cfg)

        # 1. Invalid password
        bad_res = client.post("/api/v1/auth/verify", json={"password": "wrong"})
        assert bad_res.status_code == 401

        # 2. Correct password
        ok_res = client.post("/api/v1/auth/verify", json={"password": "mypassword123"})
        assert ok_res.status_code == 200
        assert ok_res.json()["authenticated"] is True

        assert ACCESS_COOKIE_NAME in client.cookies
        assert REFRESH_COOKIE_NAME in client.cookies

        # 3. Status is now authenticated
        status_res = client.get("/api/v1/auth/status")
        assert status_res.status_code == 200
        assert status_res.json()["authenticated"] is True

        # 4. Logout
        logout_res = client.post("/api/v1/auth/logout")
        assert logout_res.status_code == 200
        assert logout_res.json()["authenticated"] is False

    def test_download_permanent_requires_auth(self, client: ASGIClient, monkeypatch):
        test_cfg = ServerConfig(teto_password="mypassword123")
        monkeypatch.setattr("tetodl.ui.daemon.api.get_server_config", lambda: test_cfg)

        # Unauthenticated request trying to write to permanent library
        res = client.post(
            "/api/v1/download",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "share": True},
        )
        assert res.status_code == 401
        assert "authorization" in res.json()["detail"].lower()

    @patch("tetodl.ui.daemon.api.background_task_runner")
    def test_download_guest_temp_allowed(self, mock_runner, client: ASGIClient, monkeypatch):
        test_cfg = ServerConfig(teto_password="mypassword123")
        monkeypatch.setattr("tetodl.ui.daemon.api.get_server_config", lambda: test_cfg)

        # Unauthenticated guest request saving to temp storage
        res = client.post(
            "/api/v1/download",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "share_temp": True},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "queued"
        assert "Temporary Storage" in data["message"]

    def test_deliverable_download_jailed_to_temp(self, client: ASGIClient, tmp_path: Path):
        # Create a temp file inside TempManager temp dir
        temp_dir = TempManager.get_temp_dir()
        temp_file = temp_dir / "test_song.m4a"
        temp_file.write_bytes(b"M4A DUMMY DATA")

        task_id = "testtask1"
        active_tasks[task_id] = {
            "status": "completed",
            "file_path": str(temp_file),
            "title": "Test Song",
        }

        try:
            # Deliverable download within temp succeeds
            res = client.get(f"/api/v1/download/file/{task_id}")
            assert res.status_code == 200
            assert res.content == b"M4A DUMMY DATA"
            assert "attachment" in res.headers["content-disposition"]
        finally:
            active_tasks.pop(task_id, None)
            if temp_file.exists():
                temp_file.unlink()

    def test_deliverable_outside_temp_requires_auth(self, client: ASGIClient, tmp_path: Path, monkeypatch):
        test_cfg = ServerConfig(teto_password="pwd")
        monkeypatch.setattr("tetodl.ui.daemon.api.get_server_config", lambda: test_cfg)

        # File outside TempManager temp dir
        outside_file = tmp_path / "outside_library.m4a"
        outside_file.write_bytes(b"OUTSIDE DATA")

        task_id = "testtask2"
        active_tasks[task_id] = {
            "status": "completed",
            "file_path": str(outside_file),
            "title": "Outside Song",
        }

        try:
            # Unauthenticated request for file outside temp is blocked
            res = client.get(f"/api/v1/download/file/{task_id}")
            assert res.status_code == 401
        finally:
            active_tasks.pop(task_id, None)

    def test_share_download_path_traversal_blocked(self, client: ASGIClient, tmp_path: Path, monkeypatch):
        test_cfg = ServerConfig(teto_password="pwd")
        monkeypatch.setattr("tetodl.ui.daemon.api.get_server_config", lambda: test_cfg)

        outside_file = tmp_path / "secret.txt"
        outside_file.write_text("classified")

        # Calling /share/download with path outside temp is blocked for guests
        res = client.get(f"/api/v1/share/download?path={outside_file}")
        assert res.status_code == 403
