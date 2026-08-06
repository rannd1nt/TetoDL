"""Tests for the daemon service managers."""

import json

import pytest

import tetodl.ui.daemon.service as service_mod


@pytest.fixture(autouse=True)
def _reset_manager_singleton():
    """Reset the cached ``get_service_manager`` between tests."""
    saved = service_mod._service_manager
    service_mod._service_manager = None
    yield
    service_mod._service_manager = saved


class TestSystemdServiceManager:
    def test_setup_writes_unit_and_starts(self, mocker, tmp_path, monkeypatch):
        """Setup writes the unit file, enables linger and starts the service."""
        monkeypatch.setattr(__import__("pathlib").Path, "home",
                            lambda: tmp_path)
        from tetodl.ui.daemon.service import SystemdServiceManager

        mgr = SystemdServiceManager()
        mock_run = mocker.patch("subprocess.run")
        mocker.patch.object(mgr, "_is_active", return_value=False)

        assert mgr.setup("0.0.0.0", 7370) == 0

        unit = tmp_path / ".config/systemd/user/tetodl.service"
        assert unit.exists()
        content = unit.read_text()
        assert "service serve --host 0.0.0.0 --port 7370" in content

        commands = [call.args[0] for call in mock_run.call_args_list]
        assert ["systemctl", "--user", "daemon-reload"] in commands
        assert ["systemctl", "--user", "start", "tetodl.service"] in commands
        assert any(c[0] == "loginctl" and c[1] == "enable-linger"
                   for c in commands)

    def test_setup_restarts_when_active(self, mocker, tmp_path, monkeypatch):
        """Setup restarts an already-active service."""
        monkeypatch.setattr(__import__("pathlib").Path, "home",
                            lambda: tmp_path)
        from tetodl.ui.daemon.service import SystemdServiceManager

        mgr = SystemdServiceManager()
        mock_run = mocker.patch("subprocess.run")
        mocker.patch.object(mgr, "_is_active", return_value=True)

        assert mgr.setup("0.0.0.0", 7370) == 0

        commands = [call.args[0] for call in mock_run.call_args_list]
        assert ["systemctl", "--user", "restart", "tetodl.service"] in commands

    def test_setup_reports_failed_start(self, mocker, tmp_path, monkeypatch):
        """A failed start returns exit code 1."""
        monkeypatch.setattr(__import__("pathlib").Path, "home",
                            lambda: tmp_path)
        from tetodl.ui.daemon.service import SystemdServiceManager

        mgr = SystemdServiceManager()
        mocker.patch("subprocess.run", side_effect=Exception("boom"))
        mocker.patch.object(mgr, "_is_active", return_value=False)

        assert mgr.setup("0.0.0.0", 7370) == 1

    def test_remove_deletes_unit(self, mocker, tmp_path, monkeypatch):
        """Remove stops, disables and deletes the unit file."""
        monkeypatch.setattr(__import__("pathlib").Path, "home",
                            lambda: tmp_path)
        from tetodl.ui.daemon.service import SystemdServiceManager

        unit = tmp_path / ".config/systemd/user/tetodl.service"
        unit.parent.mkdir(parents=True)
        unit.write_text("[Unit]\n")

        mgr = SystemdServiceManager()
        mock_run = mocker.patch("subprocess.run")

        assert mgr.remove() == 0
        assert not unit.exists()

        commands = [call.args[0] for call in mock_run.call_args_list]
        assert ["systemctl", "--user", "stop", "tetodl.service"] in commands
        assert ["systemctl", "--user", "disable", "tetodl.service"] in commands

    def test_remove_when_not_installed(self, mocker, tmp_path, monkeypatch):
        """Remove without a unit file reports an error."""
        monkeypatch.setattr(__import__("pathlib").Path, "home",
                            lambda: tmp_path)
        from tetodl.ui.daemon.service import SystemdServiceManager

        mgr = SystemdServiceManager()
        mocker.patch("subprocess.run")

        assert mgr.remove() == 1

    def test_status_queries_runtime_state(self, mocker, tmp_path, monkeypatch):
        """Status aggregates registered/active/enabled/linger/port/url."""
        monkeypatch.setattr(__import__("pathlib").Path, "home",
                            lambda: tmp_path)
        from tetodl.ui.daemon.service import SystemdServiceManager

        (tmp_path / ".config/systemd/user").mkdir(parents=True)
        (tmp_path / ".config/systemd/user/tetodl.service").write_text("[Unit]\n")

        mgr = SystemdServiceManager()
        mocker.patch.object(mgr, "_is_active", return_value=True)
        mocker.patch.object(mgr, "_is_enabled", return_value=True)
        mocker.patch.object(mgr, "_is_linger_enabled", return_value=False)
        mocker.patch.object(service_mod, "detect_lan_ip",
                            return_value="192.168.1.5")
        mocker.patch.object(service_mod, "get_daemon_port", return_value=7370)

        assert mgr.status() == 0

    def test_logs_when_not_installed(self, mocker, tmp_path, monkeypatch):
        """Logs without an installed unit returns exit code 1."""
        monkeypatch.setattr(__import__("pathlib").Path, "home",
                            lambda: tmp_path)
        from tetodl.ui.daemon.service import SystemdServiceManager

        mgr = SystemdServiceManager()
        assert mgr.logs(tail=50, follow=False) == 1

    def test_logs_runs_journalctl(self, mocker, tmp_path, monkeypatch):
        """Logs invokes journalctl with tail and no-pager."""
        monkeypatch.setattr(__import__("pathlib").Path, "home",
                            lambda: tmp_path)
        from tetodl.ui.daemon.service import SystemdServiceManager

        (tmp_path / ".config/systemd/user").mkdir(parents=True)
        (tmp_path / ".config/systemd/user/tetodl.service").write_text("[Unit]\n")

        mgr = SystemdServiceManager()
        mock_run = mocker.patch("subprocess.run")

        assert mgr.logs(tail=10, follow=True) == 0
        cmd = mock_run.call_args.args[0]
        assert cmd[:4] == ["journalctl", "--user", "-u", "tetodl.service"]
        assert cmd[4:7] == ["-n", "10", "--no-pager"]
        assert cmd[-1] == "-f"


class TestWindowsServiceManager:
    def test_setup_spawns_process_and_tracks_state(self, mocker, tmp_path):
        """Windows setup spawns a hidden process and writes pid/conf files."""
        from tetodl.ui.daemon.service import WindowsServiceManager

        mgr = WindowsServiceManager()
        data_dir = tmp_path / "data"
        mocker.patch.object(mgr, "_data_dir", return_value=data_dir)
        mocker.patch.object(mgr, "_shortcut",
                            return_value=tmp_path / "Startup" / "TetoDL Daemon.lnk")
        mocker.patch.object(mgr, "_stop_old")
        mocker.patch.object(mgr, "_create_shortcut")

        proc = mocker.MagicMock()
        proc.pid = 4242
        proc.poll.return_value = None
        mock_popen = mocker.patch("subprocess.Popen", return_value=proc)
        mocker.patch("subprocess.run")

        assert mgr.setup("0.0.0.0", 9000) == 0

        args, kwargs = mock_popen.call_args
        assert "service" in args[0]
        assert "serve" in args[0]
        assert kwargs["creationflags"] == WindowsServiceManager.CREATE_NO_WINDOW

        assert (data_dir / "daemon.pid").read_text() == "4242"
        conf = json.loads((data_dir / "daemon.json").read_text())
        assert conf["host"] == "0.0.0.0"
        assert conf["port"] == 9000
        assert "--log-file" in args[0]

    def test_remove_cleans_trackers(self, mocker, tmp_path):
        """Windows remove deletes pid/log/shortcut and returns 0."""
        from tetodl.ui.daemon.service import WindowsServiceManager

        mgr = WindowsServiceManager()
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        pid_file = data_dir / "daemon.pid"
        log_file = data_dir / "daemon.log"
        shortcut = tmp_path / "Startup" / "TetoDL Daemon.lnk"
        pid_file.write_text("4242")
        log_file.write_text("line")
        shortcut.parent.mkdir(parents=True)
        shortcut.write_text("x")

        mocker.patch.object(mgr, "_data_dir", return_value=data_dir)
        mocker.patch.object(mgr, "_shortcut", return_value=shortcut)
        mocker.patch.object(mgr, "_stop_old")
        mocker.patch("subprocess.run")

        assert mgr.remove() == 0
        assert not pid_file.exists()
        assert not log_file.exists()
        assert not shortcut.exists()

    def test_logs_when_not_available(self, mocker, tmp_path):
        """Windows logs without a log file returns exit code 1."""
        from tetodl.ui.daemon.service import WindowsServiceManager

        mgr = WindowsServiceManager()
        mocker.patch.object(mgr, "_log_file",
                            return_value=tmp_path / "missing.log")

        assert mgr.logs(tail=10, follow=False) == 1

    def test_setup_reports_early_exit(self, mocker, tmp_path):
        """Windows setup returns 1 when the daemon exits immediately."""
        from tetodl.ui.daemon.service import WindowsServiceManager

        mgr = WindowsServiceManager()
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        mocker.patch.object(mgr, "_data_dir", return_value=data_dir)
        mocker.patch.object(mgr, "_log_file",
                            return_value=data_dir / "daemon.log")
        mocker.patch.object(mgr, "_stop_old")
        mocker.patch.object(mgr, "_create_shortcut")

        proc = mocker.MagicMock()
        proc.pid = 999
        proc.poll.return_value = 1
        mocker.patch("subprocess.Popen", return_value=proc)

        assert mgr.setup("0.0.0.0", 9000) == 1
        assert not (data_dir / "daemon.pid").exists()


class TestNullServiceManager:
    def test_setup_not_supported(self, mocker):
        from tetodl.ui.daemon.service import NullServiceManager

        assert NullServiceManager().setup("0.0.0.0", 7370) == 0

    def test_logs_not_supported(self, mocker):
        from tetodl.ui.daemon.service import NullServiceManager

        assert NullServiceManager().logs(tail=10, follow=False) == 1


class TestGetServiceManager:
    def test_selects_windows(self, mocker):
        mocker.patch.object(service_mod.env, "get",
                            side_effect=lambda k: k == "is_windows")
        from tetodl.ui.daemon.service import (
            WindowsServiceManager,
            get_service_manager,
        )

        assert isinstance(get_service_manager(), WindowsServiceManager)

    def test_selects_termux_null(self, mocker):
        mocker.patch.object(
            service_mod.env, "get",
            side_effect=lambda k: k == "is_termux",
        )
        from tetodl.ui.daemon.service import (
            NullServiceManager,
            get_service_manager,
        )

        assert isinstance(get_service_manager(), NullServiceManager)

    def test_selects_systemd_default(self, mocker):
        mocker.patch.object(service_mod.env, "get", return_value=False)
        from tetodl.ui.daemon.service import (
            SystemdServiceManager,
            get_service_manager,
        )

        assert isinstance(get_service_manager(), SystemdServiceManager)

    def test_stop_old_reclaims_orphan_on_port(self, mocker, tmp_path):
        """Windows _stop_old kills a process listening on the daemon port
        even when the pid file is stale/missing."""
        from tetodl.ui.daemon.service import WindowsServiceManager

        mgr = WindowsServiceManager()
        mocker.patch.object(mgr, "_read_pid", return_value=None)
        mocker.patch.object(mgr, "_read_port", return_value=7370)
        mock_run = mocker.patch("subprocess.run")
        netstat = (
            "protopid TCP? ignored\n"
            "  TCP    0.0.0.0:7370    0.0.0.0:0    LISTENING    5555\n"
            "  TCP    127.0.0.1:1234  0.0.0.0:0    LISTENING    1234\n"
        )
        mock_run.return_value.stdout = netstat

        mocker.patch("tetodl.ui.daemon.service._pid_is_alive", return_value=True)

        mgr._stop_old()

        calls = [c.args[0] if c.args else None for c in mock_run.call_args_list]
        assert ["taskkill", "/PID", "5555", "/F"] in calls

    def test_port_pids_parses_netstat(self, mocker):
        from tetodl.ui.daemon.service import WindowsServiceManager

        netstat = (
            "  TCP    0.0.0.0:7370    0.0.0.0:0    LISTENING    5555\n"
            "  TCP    [::]:7370      [::]:0       LISTENING    5555\n"
            "  UDP    0.0.0.0:7370    0.0.0.0:0    LISTENING    7777\n"
            "  TCP    0.0.0.0:9090    0.0.0.0:0    LISTENING    8888\n"
        )
        mock_run = mocker.patch("tetodl.ui.daemon.service.subprocess.run")
        mock_run.return_value.stdout = netstat

        mgr = WindowsServiceManager()
        assert mgr._port_pids(7370) == [5555]
