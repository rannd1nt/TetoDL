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

"""Server and engine configuration manager for tetodl.conf.

Provides parsing, default templating, and path resolution for the server-level
configuration file across Linux, macOS, and Windows.
"""
from __future__ import annotations

import os
import secrets
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ...constants import APP_NAME
from .env import env

DEFAULT_CONFIG_TEMPLATE = """# ==============================================================================
# TetoDL Server & Engine Configuration
# ==============================================================================

[server]
host = "0.0.0.0"
port = 7370
teto_password = ""               # Admin password for library writes; blank disables write authorization
teto_secret = ""                 # HMAC signing key (64 hex chars); auto-generated if blank
access_token_ttl_minutes = 60    # Short-lived HttpOnly session cookie
refresh_token_ttl_days = 30      # Long-lived HttpOnly refresh cookie (silent refresh)
url_prefix = ""                  # Set to "/tetodl" if behind reverse-proxy subpath

[storage]
music_root = ""                  # Custom override or blank to use default
video_root = ""

[defaults]
audio_quality = "m4a"
max_video_resolution = "720p"
"""


@dataclass
class ServerConfig:
    """Holds parsed configuration values from tetodl.conf."""

    host: str = "0.0.0.0"
    port: int = 7370
    teto_password: str = ""
    teto_secret: str = field(default_factory=lambda: secrets.token_hex(32))
    access_token_ttl_minutes: int = 60
    refresh_token_ttl_days: int = 30
    url_prefix: str = ""

    music_root: str = ""
    video_root: str = ""

    audio_quality: str = "m4a"
    max_video_resolution: str = "720p"

    config_file_path: Path | None = None


_cached_server_config: ServerConfig | None = None


def get_default_config_path() -> Path:
    """Determine the standard path for tetodl.conf based on platform and environment."""
    custom_path = os.environ.get("TETODL_CONFIG")
    if custom_path:
        return Path(custom_path).expanduser().resolve()

    home = Path.home()
    if env.get("is_windows"):
        appdata = os.environ.get("APPDATA")
        base = Path(appdata) if appdata else home / "AppData" / "Roaming"
        return (base / APP_NAME / "tetodl.conf").resolve()

    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    base_dir = Path(xdg_config) if xdg_config else home / ".config"

    # Support lowercase tetodl or uppercase TetoDL
    tetodl_dir = base_dir / "tetodl"
    if tetodl_dir.exists():
        return (tetodl_dir / "tetodl.conf").resolve()

    return (base_dir / APP_NAME.lower() / "tetodl.conf").resolve()


def ensure_default_server_config(path: Path | None = None) -> Path:
    """Create default tetodl.conf template if not present on disk."""
    target = path or get_default_config_path()
    if not target.exists():
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(DEFAULT_CONFIG_TEMPLATE, encoding="utf-8")
        except OSError:
            pass
    return target


def load_server_config(path: Path | None = None, reload: bool = False) -> ServerConfig:
    """Load configuration from tetodl.conf.

    Parameters
    ----------
    path : Path | None
        Optional explicit file path to load from.
    reload : bool
        If True, force re-reading the file even if cached.
    """
    global _cached_server_config
    if _cached_server_config is not None and not reload and path is None:
        return _cached_server_config

    cfg_path = path or get_default_config_path()
    cfg = ServerConfig(config_file_path=cfg_path)

    if cfg_path.exists() and cfg_path.is_file():
        try:
            with open(cfg_path, "rb") as f:
                data: dict[str, Any] = tomllib.load(f)

            server_sec = data.get("server", {})
            if "host" in server_sec:
                cfg.host = str(server_sec["host"])
            if "port" in server_sec:
                cfg.port = int(server_sec["port"])
            if "teto_password" in server_sec:
                cfg.teto_password = str(server_sec["teto_password"])
            if server_sec.get("teto_secret"):
                cfg.teto_secret = str(server_sec["teto_secret"])
            if "access_token_ttl_minutes" in server_sec:
                cfg.access_token_ttl_minutes = int(server_sec["access_token_ttl_minutes"])
            if "refresh_token_ttl_days" in server_sec:
                cfg.refresh_token_ttl_days = int(server_sec["refresh_token_ttl_days"])
            if "url_prefix" in server_sec:
                cfg.url_prefix = str(server_sec["url_prefix"])

            storage_sec = data.get("storage", {})
            if "music_root" in storage_sec:
                cfg.music_root = str(storage_sec["music_root"])
            if "video_root" in storage_sec:
                cfg.video_root = str(storage_sec["video_root"])

            defaults_sec = data.get("defaults", {})
            if "audio_quality" in defaults_sec:
                cfg.audio_quality = str(defaults_sec["audio_quality"])
            if "max_video_resolution" in defaults_sec:
                cfg.max_video_resolution = str(defaults_sec["max_video_resolution"])

        except (OSError, tomllib.TOMLDecodeError, ValueError, KeyError):
            pass

    # Ensure secret is non-empty
    if not cfg.teto_secret:
        cfg.teto_secret = secrets.token_hex(32)

    if path is None:
        _cached_server_config = cfg
    return cfg


def get_server_config() -> ServerConfig:
    """Return the cached ServerConfig singleton."""
    global _cached_server_config
    if _cached_server_config is None:
        _cached_server_config = load_server_config()
    return _cached_server_config
