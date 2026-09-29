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

from pathlib import Path

from tetodl.core.domain.server_config import (
    ServerConfig,
    ensure_default_server_config,
    get_default_config_path,
    load_server_config,
)


class TestServerConfig:
    def test_default_values(self):
        cfg = ServerConfig()
        assert cfg.host == "0.0.0.0"
        assert cfg.port == 7370
        assert cfg.teto_password == ""
        assert len(cfg.teto_secret) >= 32
        assert cfg.access_token_ttl_minutes == 60
        assert cfg.refresh_token_ttl_days == 30
        assert cfg.audio_quality == "m4a"

    def test_load_from_toml(self, tmp_path: Path):
        conf_file = tmp_path / "tetodl.conf"
        conf_file.write_text(
            """
[server]
host = "127.0.0.1"
port = 8888
teto_password = "supersecretpassword"
teto_secret = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
access_token_ttl_minutes = 15
refresh_token_ttl_days = 7

[storage]
music_root = "/mnt/music"
video_root = "/mnt/video"

[defaults]
audio_quality = "opus"
max_video_resolution = "1080p"
""",
            encoding="utf-8",
        )

        cfg = load_server_config(conf_file, reload=True)
        assert cfg.host == "127.0.0.1"
        assert cfg.port == 8888
        assert cfg.teto_password == "supersecretpassword"
        assert cfg.teto_secret == "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
        assert cfg.access_token_ttl_minutes == 15
        assert cfg.refresh_token_ttl_days == 7
        assert cfg.music_root == "/mnt/music"
        assert cfg.video_root == "/mnt/video"
        assert cfg.audio_quality == "opus"
        assert cfg.max_video_resolution == "1080p"

    def test_auto_generate_secret_when_empty(self, tmp_path: Path):
        conf_file = tmp_path / "tetodl.conf"
        conf_file.write_text(
            """
[server]
teto_password = "mypassword"
teto_secret = ""
""",
            encoding="utf-8",
        )
        cfg = load_server_config(conf_file, reload=True)
        assert cfg.teto_password == "mypassword"
        assert len(cfg.teto_secret) >= 32

    def test_ensure_default_template(self, tmp_path: Path):
        conf_file = tmp_path / "subdir" / "tetodl.conf"
        assert not conf_file.exists()
        ensure_default_server_config(conf_file)
        assert conf_file.exists()
        content = conf_file.read_text(encoding="utf-8")
        assert "teto_password" in content
        assert "teto_secret" in content

    def test_get_default_config_path_respects_env(self, monkeypatch, tmp_path: Path):
        custom = tmp_path / "custom.conf"
        monkeypatch.setenv("TETODL_CONFIG", str(custom))
        resolved = get_default_config_path()
        assert resolved == custom.resolve()
