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

"""Dual-Token HMAC authentication and HttpOnly cookie management for TetoDL Daemon.

Implements short-lived access tokens and long-lived refresh tokens signed with
HMAC-SHA256, providing secure silent refresh without exposing tokens to frontend JavaScript.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any, Literal

from fastapi import Request, Response

from ...core.domain.server_config import ServerConfig, get_server_config

ACCESS_COOKIE_NAME = "tetodl_access"
REFRESH_COOKIE_NAME = "tetodl_refresh"


def _b64url_encode(data: bytes) -> str:
    """Base64url encode without trailing '=' padding."""
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64url_decode(data: str) -> bytes:
    """Base64url decode with restored padding."""
    rem = len(data) % 4
    if rem:
        data += "=" * (4 - rem)
    return base64.urlsafe_b64decode(data.encode("ascii"))


def create_token(
    token_type: Literal["access", "refresh"],
    secret: str,
    ttl_seconds: int,
    subject: str = "admin",
) -> str:
    """Generate an HMAC-SHA256 signed compact token."""
    now = int(time.time())
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + ttl_seconds,
    }
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    payload_b64 = _b64url_encode(payload_bytes)

    sig = hmac.new(secret.encode("utf-8"), payload_b64.encode("ascii"), hashlib.sha256).digest()
    sig_b64 = _b64url_encode(sig)

    return f"{payload_b64}.{sig_b64}"


def verify_token(
    token: str,
    secret: str,
    expected_type: Literal["access", "refresh"],
) -> dict[str, Any] | None:
    """Verify HMAC signature and expiration of a token.

    Returns the payload dictionary if valid, or None if invalid/expired.
    """
    if not token or "." not in token:
        return None

    try:
        payload_b64, sig_b64 = token.split(".", 1)
        expected_sig = hmac.new(
            secret.encode("utf-8"), payload_b64.encode("ascii"), hashlib.sha256
        ).digest()
        actual_sig = _b64url_decode(sig_b64)

        if not hmac.compare_digest(expected_sig, actual_sig):
            return None

        payload_bytes = _b64url_decode(payload_b64)
        payload = json.loads(payload_bytes.decode("utf-8"))

        if payload.get("type") != expected_type:
            return None

        if payload.get("exp", 0) <= int(time.time()):
            return None

        return payload
    except (json.JSONDecodeError, ValueError, KeyError, TypeError):
        return None


def verify_admin_password(password: str, cfg: ServerConfig | None = None) -> bool:
    """Compare input password with teto_password using constant-time comparison."""
    server_cfg = cfg or get_server_config()
    if not server_cfg.teto_password:
        return False
    return hmac.compare_digest(
        password.encode("utf-8"), server_cfg.teto_password.encode("utf-8")
    )


def issue_token_pair(cfg: ServerConfig | None = None) -> tuple[str, str]:
    """Generate fresh (access_token, refresh_token) pair."""
    server_cfg = cfg or get_server_config()
    access_ttl = server_cfg.access_token_ttl_minutes * 60
    refresh_ttl = server_cfg.refresh_token_ttl_days * 86400

    access_token = create_token("access", server_cfg.teto_secret, access_ttl)
    refresh_token = create_token("refresh", server_cfg.teto_secret, refresh_ttl)
    return access_token, refresh_token


def set_auth_cookies(
    response: Response,
    access_token: str | None = None,
    refresh_token: str | None = None,
    cfg: ServerConfig | None = None,
) -> None:
    """Set HttpOnly SameSite=Strict session cookies."""
    server_cfg = cfg or get_server_config()
    access_ttl = server_cfg.access_token_ttl_minutes * 60
    refresh_ttl = server_cfg.refresh_token_ttl_days * 86400

    if access_token:
        response.set_cookie(
            key=ACCESS_COOKIE_NAME,
            value=access_token,
            max_age=access_ttl,
            httponly=True,
            samesite="strict",
            path="/",
        )
    if refresh_token:
        response.set_cookie(
            key=REFRESH_COOKIE_NAME,
            value=refresh_token,
            max_age=refresh_ttl,
            httponly=True,
            samesite="strict",
            path="/",
        )


def clear_auth_cookies(response: Response) -> None:
    """Delete authentication cookies on logout."""
    response.delete_cookie(key=ACCESS_COOKIE_NAME, path="/", samesite="strict")
    response.delete_cookie(key=REFRESH_COOKIE_NAME, path="/", samesite="strict")


def verify_request_auth(
    request: Request,
    response: Response | None = None,
    cfg: ServerConfig | None = None,
) -> tuple[bool, str | None]:
    """Check request auth with silent refresh support.

    Parameters
    ----------
    request : Request
        Incoming FastAPI/Starlette request.
    response : Response | None
        Outgoing response where a silently refreshed access token can be attached.
    cfg : ServerConfig | None
        Server config instance.

    Returns
    -------
    tuple[bool, str | None]
        (is_authenticated, token_source) where token_source is "access", "refreshed", or None.
    """
    server_cfg = cfg or get_server_config()

    # 1. Check access cookie
    access_cookie = request.cookies.get(ACCESS_COOKIE_NAME)
    if access_cookie:
        payload = verify_token(access_cookie, server_cfg.teto_secret, "access")
        if payload is not None:
            return True, "access"

    # 2. Check refresh cookie (Silent Refresh)
    refresh_cookie = request.cookies.get(REFRESH_COOKIE_NAME)
    if refresh_cookie:
        payload = verify_token(refresh_cookie, server_cfg.teto_secret, "refresh")
        if payload is not None:
            # Issue a new short-lived access token
            access_ttl = server_cfg.access_token_ttl_minutes * 60
            new_access = create_token("access", server_cfg.teto_secret, access_ttl)
            if response is not None:
                set_auth_cookies(response, access_token=new_access, cfg=server_cfg)
            return True, "refreshed"

    return False, None
