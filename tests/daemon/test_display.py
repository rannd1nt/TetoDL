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

"""Tests for LAN IP detection and daemon URL helpers."""

from tetodl.ui.daemon import display as display_mod


IPCONFIG_SAMPLE = """\
Windows IP Configuration


Wireless LAN adapter Local Area Connection* 9:

   Media State . . . . . . . . . . . : Media disconnected
   Connection-specific DNS Suffix  . :

Wireless LAN adapter Local Area Connection* 10:

   Connection-specific DNS Suffix  . :
   Link-local IPv6 Address . . . . . : fe80::4779:de92:8aef:dbe4%13
   IPv4 Address. . . . . . . . . . . : 192.168.137.1
   Subnet Mask . . . . . . . . . . . : 255.255.255.0
   Default Gateway . . . . . . . . . :

Wireless LAN adapter Wi-Fi:

   Connection-specific DNS Suffix  . :
   IPv6 Address. . . . . . . . . . . : 2400:9800::1
   Link-local IPv6 Address . . . . . : fe80::517f:ef03:56af:fa77%10
   IPv4 Address. . . . . . . . . . . : 10.74.51.210
   Subnet Mask . . . . . . . . . . . : 255.255.255.0
   Default Gateway . . . . . . . . . : 10.74.51.111

Ethernet adapter Ethernet:

   Media State . . . . . . . . . . . : Media disconnected
"""


class TestGetIpFromIpconfig:
    def test_skips_disconnected_and_prefers_gateway(self, mocker):
        """Returns only active adapters, ordering gateway adapters first."""
        mock = mocker.patch("subprocess.check_output")
        mock.return_value = IPCONFIG_SAMPLE

        assert display_mod._get_ip_from_ipconfig() == [
            "10.74.51.210",  # Wi-Fi (has default gateway)
            "192.168.137.1",  # hotspot (no gateway)
        ]

    def test_skips_loopback_and_apipa(self, mocker):
        mock = mocker.patch("subprocess.check_output")
        mock.return_value = (
            "Adapter A:\n"
            "   IPv4 Address. . . . . . . . . . . : 127.0.0.1\n"
            "   Default Gateway . . . . . . . . . : 1.1.1.1\n"
            "Adapter B:\n"
            "   IPv4 Address. . . . . . . . . . . : 169.254.12.34\n"
            "Adapter C:\n"
            "   IPv4 Address. . . . . . . . . . . : 192.168.1.10\n"
            "   Default Gateway . . . . . . . . . : 192.168.1.1\n"
        )

        assert display_mod._get_ip_from_ipconfig() == ["192.168.1.10"]

    def test_empty_on_command_failure(self, mocker):
        mocker.patch(
            "subprocess.check_output",
            side_effect=FileNotFoundError,
        )
        assert display_mod._get_ip_from_ipconfig() == []


class TestGetIpFromIpA:
    def test_returns_non_virtual_ips(self, mocker):
        mock = mocker.patch("subprocess.check_output")
        mock.return_value = (
            "1: lo    inet 127.0.0.1/8 scope host lo\n"
            "2: eth0  inet 192.168.1.5/24 brd 192.168.1.255 scope global eth0\n"
            "3: docker0 inet 172.17.0.1/16 scope global docker0\n"
            "4: wlan0 inet 10.0.0.9/24 scope global wlan0\n"
        )

        assert display_mod._get_ip_from_ip_a() == ["192.168.1.5", "10.0.0.9"]

    def test_empty_on_command_failure(self, mocker):
        mocker.patch(
            "subprocess.check_output",
            side_effect=FileNotFoundError,
        )
        assert display_mod._get_ip_from_ip_a() == []


class TestDetectLan:
    def test_detect_lan_ip_prefers_default_route(self, mocker):
        """detect_lan_ip prefers get_best_ip (pre-2.3.0 behaviour)."""
        mocker.patch.object(display_mod, "get_best_ip",
                            return_value="10.74.51.210")
        mocker.patch.object(display_mod, "detect_lan_ips",
                            return_value=["192.168.137.1"])

        assert display_mod.detect_lan_ip() == "10.74.51.210"

    def test_detect_lan_ip_falls_back_to_adapter_ips(self, mocker):
        mocker.patch.object(display_mod, "get_best_ip",
                            return_value="127.0.0.1")
        mocker.patch.object(display_mod, "detect_lan_ips",
                            return_value=["192.168.137.1", "10.74.51.210"])

        assert display_mod.detect_lan_ip() == "192.168.137.1"

    def test_detect_lan_ip_none_when_no_ips(self, mocker):
        mocker.patch.object(display_mod, "get_best_ip",
                            return_value="127.0.0.1")
        mocker.patch.object(display_mod, "detect_lan_ips", return_value=[])

        assert display_mod.detect_lan_ip() is None

    def test_detect_lan_ips_windows(self, mocker):
        mocker.patch.object(display_mod.env, "get",
                            side_effect=lambda k: k == "is_windows")
        mocker.patch.object(display_mod, "_get_ip_from_ipconfig",
                            return_value=["10.74.51.210", "192.168.137.1"])

        assert display_mod.detect_lan_ips() == [
            "10.74.51.210", "192.168.137.1"
        ]

    def test_detect_lan_ips_falls_back_to_best_ip(self, mocker):
        mocker.patch.object(display_mod.env, "get", return_value=False)
        mocker.patch.object(display_mod, "_get_ip_from_ip_a", return_value=[])
        mocker.patch.object(display_mod, "get_best_ip",
                            return_value="10.74.51.210")

        assert display_mod.detect_lan_ips() == ["10.74.51.210"]


class TestDaemonUrls:
    def test_builds_urls_for_every_ip(self, mocker):
        mocker.patch.object(display_mod, "detect_lan_ips",
                            return_value=["10.74.51.210", "192.168.137.1"])

        assert display_mod.daemon_urls(7370) == [
            "http://10.74.51.210:7370",
            "http://192.168.137.1:7370",
        ]

    def test_empty_when_no_ips(self, mocker):
        mocker.patch.object(display_mod, "detect_lan_ips", return_value=[])

        assert display_mod.daemon_urls(7370) == []