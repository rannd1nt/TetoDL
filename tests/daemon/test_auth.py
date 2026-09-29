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

import time
from starlette.requests import Request
from starlette.responses import Response

from tetodl.core.domain.server_config import ServerConfig
from tetodl.ui.daemon.auth import (
    ACCESS_COOKIE_NAME,
    REFRESH_COOKIE_NAME,
    clear_auth_cookies,
    create_token,
    issue_token_pair,
    set_auth_cookies,
    verify_admin_password,
    verify_request_auth,
    verify_token,
)


class TestDaemonAuth:
    def test_create_and_verify_token(self):
        secret = "supersecretkey1234567890abcdef"
        token = create_token("access", secret, ttl_seconds=3600)
        assert isinstance(token, str)
        assert "." in token

        payload = verify_token(token, secret, expected_type="access")
        assert payload is not None
        assert payload["type"] == "access"
        assert payload["sub"] == "admin"
        assert payload["exp"] > time.time()

    def test_verify_token_wrong_secret(self):
        secret = "secretA"
        token = create_token("access", secret, ttl_seconds=3600)
        assert verify_token(token, "wrongSecret", expected_type="access") is None

    def test_verify_token_wrong_type(self):
        secret = "mysecret"
        token = create_token("refresh", secret, ttl_seconds=3600)
        # Expecting access token, but token is refresh
        assert verify_token(token, secret, expected_type="access") is None

    def test_verify_token_expired(self):
        secret = "mysecret"
        token = create_token("access", secret, ttl_seconds=-10)
        assert verify_token(token, secret, expected_type="access") is None

    def test_verify_token_tampered(self):
        secret = "mysecret"
        token = create_token("access", secret, ttl_seconds=3600)
        tampered = token[:-4] + "xxxx"
        assert verify_token(tampered, secret, expected_type="access") is None

    def test_verify_admin_password(self):
        cfg = ServerConfig(teto_password="myadminpassword")
        assert verify_admin_password("myadminpassword", cfg) is True
        assert verify_admin_password("wrong", cfg) is False

    def test_verify_admin_password_empty_config(self):
        cfg = ServerConfig(teto_password="")
        assert verify_admin_password("anything", cfg) is False
        assert verify_admin_password("", cfg) is False

    def test_set_and_clear_auth_cookies(self):
        res = Response()
        cfg = ServerConfig()
        access_tok, refresh_tok = issue_token_pair(cfg)
        set_auth_cookies(res, access_token=access_tok, refresh_token=refresh_tok, cfg=cfg)

        cookies = res.headers.getlist("set-cookie")
        assert any(ACCESS_COOKIE_NAME in c for c in cookies)
        assert any(REFRESH_COOKIE_NAME in c for c in cookies)
        assert any("HttpOnly" in c for c in cookies)
        assert any("samesite=strict" in c.lower() for c in cookies)

        # Clear
        clear_res = Response()
        clear_auth_cookies(clear_res)
        clear_cookies = clear_res.headers.getlist("set-cookie")
        assert any(ACCESS_COOKIE_NAME in c and 'max-age=0' in c.lower() for c in clear_cookies)

    def test_silent_refresh_flow(self):
        secret = "testsecretkeyfordaemon12345678"
        cfg = ServerConfig(teto_secret=secret, access_token_ttl_minutes=15, refresh_token_ttl_days=7)

        # Expired access token, valid refresh token
        expired_access = create_token("access", secret, ttl_seconds=-10)
        valid_refresh = create_token("refresh", secret, ttl_seconds=86400)

        # Construct request with cookies
        scope = {
            "type": "http",
            "headers": [
                (
                    b"cookie",
                    f"{ACCESS_COOKIE_NAME}={expired_access}; {REFRESH_COOKIE_NAME}={valid_refresh}".encode(),
                )
            ],
        }
        req = Request(scope)
        res = Response()

        is_auth, source = verify_request_auth(req, response=res, cfg=cfg)
        assert is_auth is True
        assert source == "refreshed"

        # Check that response received fresh access token
        new_cookies = res.headers.getlist("set-cookie")
        assert any(ACCESS_COOKIE_NAME in c for c in new_cookies)
