import abc
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from ...core.domain.env import env
from ...utils.console import console
from ...utils.i18n_keys import Keys
from .display import _pid_is_alive, detect_lan_ip, get_daemon_port


class ServiceManager(abc.ABC):
    """Abstract base for platform-specific daemon service management."""

    @abc.abstractmethod
    def setup(self, host: str, port: int) -> int:
        ...

    @abc.abstractmethod
    def remove(self) -> int:
        ...

    @abc.abstractmethod
    def status(self) -> int:
        ...

    @abc.abstractmethod
    def logs(self, tail: int, follow: bool) -> int:
        ...

    def get_executable_path(self) -> str:
        tetodl_path = shutil.which("tetodl")
        if tetodl_path:
            return tetodl_path
        return os.path.abspath(sys.argv[0])


class SystemdServiceManager(ServiceManager):
    """Systemd user service manager — Linux."""

    SERVICE_NAME = "tetodl.service"

    def _service_file(self) -> Path:
        return Path.home() / ".config" / "systemd" / "user" / self.SERVICE_NAME

    def _user(self) -> str:
        return os.environ.get("USER") or Path.home().name

    def _is_active(self) -> bool:
        try:
            out = subprocess.check_output(
                ["systemctl", "--user", "is-active", self.SERVICE_NAME],
                stderr=subprocess.DEVNULL,
                text=True,
            )
            return "active" in out.strip()
        except Exception:
            return False

    def _is_enabled(self) -> bool:
        try:
            out = subprocess.check_output(
                ["systemctl", "--user", "is-enabled", self.SERVICE_NAME],
                stderr=subprocess.DEVNULL,
                text=True,
            )
            return "enabled" in out.strip()
        except Exception:
            return False

    def _is_linger_enabled(self) -> bool:
        try:
            out = subprocess.check_output(
                ["loginctl", "show-user", self._user(), "--property=Linger", "--value"],
                stderr=subprocess.DEVNULL,
                text=True,
            )
            return "yes" in out.strip().lower()
        except Exception:
            return False

    def _enable_linger(self):
        try:
            subprocess.run(
                ["loginctl", "enable-linger", self._user()],
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass

    def setup(self, host: str, port: int) -> int:
        console.proc(Keys.daemon.configuring_systemd)
        exec_path = self.get_executable_path()
        env_path = os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin")

        service_file = self._service_file()
        exists = service_file.exists()
        if exists:
            console.warn(Keys.service.setup_already_installed)

        service_content = f"""[Unit]
Description=TetoDL Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart={exec_path} service serve --host {host} --port {port}
Restart=always
RestartSec=5
Environment="PATH={env_path}"
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=default.target
"""
        try:
            service_file.parent.mkdir(parents=True, exist_ok=True)
            service_file.write_text(service_content)

            subprocess.run(
                ["systemctl", "--user", "daemon-reload"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            console.ok(Keys.daemon.service_file_created(path=str(service_file)))

            self._enable_linger()
            try:
                subprocess.run(
                    ["systemctl", "--user", "enable", self.SERVICE_NAME],
                    check=True,
                    stderr=subprocess.DEVNULL,
                )
            except Exception:
                pass

            active = self._is_active()
            try:
                if active:
                    subprocess.run(
                        ["systemctl", "--user", "restart", self.SERVICE_NAME],
                        check=True,
                        stderr=subprocess.DEVNULL,
                    )
                    console.ok(Keys.service.setup_restarted)
                else:
                    subprocess.run(
                        ["systemctl", "--user", "start", self.SERVICE_NAME],
                        check=True,
                        stderr=subprocess.DEVNULL,
                    )
                    console.ok(Keys.service.setup_started)
            except subprocess.CalledProcessError as e:
                if active:
                    console.err(Keys.service.failed_systemd_restart(error=e))
                else:
                    console.err(Keys.service.failed_systemd_start(error=e))

            console.ok(Keys.service.setup_complete)
            return 0
        except Exception as e:
            console.err(Keys.daemon.failed_setup_systemd(error=str(e)))
            return 1

    def remove(self) -> int:
        console.proc(Keys.daemon.removing_systemd)
        service_file = self._service_file()
        if not service_file.exists():
            console.err(Keys.daemon.daemon_not_installed)
            return 1

        try:
            subprocess.run(
                ["systemctl", "--user", "stop", self.SERVICE_NAME],
                stderr=subprocess.DEVNULL,
            )
            subprocess.run(
                ["systemctl", "--user", "disable", self.SERVICE_NAME],
                stderr=subprocess.DEVNULL,
            )
            service_file.unlink()
            subprocess.run(
                ["systemctl", "--user", "daemon-reload"],
                stderr=subprocess.DEVNULL,
            )
            console.ok(Keys.daemon.daemon_removed)
            return 0
        except Exception as e:
            console.err(Keys.daemon.failed_remove_systemd(error=str(e)))
            return 1

    def status(self) -> int:
        console.ok(Keys.service.status_title)
        registered = "Yes" if self._service_file().exists() else "No"
        console.warn(Keys.service.status_registered(value=registered))
        active = "active (running)" if self._is_active() else "inactive (dead)"
        console.warn(Keys.service.status_active(value=active))
        enabled = "enabled" if self._is_enabled() else "disabled"
        console.warn(Keys.service.status_enabled(value=enabled))
        linger = "enabled" if self._is_linger_enabled() else "disabled"
        console.warn(Keys.service.status_linger(value=linger))
        port = get_daemon_port()
        console.warn(Keys.service.status_port(port=port))
        ip = detect_lan_ip()
        url = f"http://{ip}:{port}" if ip else "N/A"
        console.warn(Keys.service.status_url(url=url))
        return 0

    def logs(self, tail: int, follow: bool) -> int:
        service_file = self._service_file()
        if not service_file.exists():
            console.err(Keys.service.logs_not_available)
            return 1
        cmd = [
            "journalctl", "--user", "-u", self.SERVICE_NAME,
            "-n", str(tail), "--no-pager",
        ]
        if follow:
            cmd.append("-f")
            console.warn(Keys.service.logs_follow_hint)
        try:
            subprocess.run(cmd)
        except KeyboardInterrupt:
            pass
        return 0


class WindowsServiceManager(ServiceManager):
    """Windows daemon manager — hidden process + Startup shortcut."""

    CREATE_NO_WINDOW = 0x08000000

    def _data_dir(self) -> Path:
        return Path(env.get("data_dir"))

    def _pid_file(self) -> Path:
        return self._data_dir() / "daemon.pid"

    def _conf_file(self) -> Path:
        return self._data_dir() / "daemon.json"

    def _log_file(self) -> Path:
        return self._data_dir() / "daemon.log"

    def _shortcut(self) -> Path:
        startup = os.environ.get("APPDATA", "")
        return (
            Path(startup) / "Microsoft" / "Windows" / "Start Menu"
            / "Programs" / "Startup" / "TetoDL Daemon.lnk"
        )

    def _read_pid(self) -> int | None:
        try:
            return int(self._pid_file().read_text().strip())
        except Exception:
            return None

    def _read_port(self) -> int:
        try:
            data = json.loads(self._conf_file().read_text())
            return int(data.get("port", 7370))
        except Exception:
            return 7370

    def _stop_old(self):
        pid = self._read_pid()
        if pid and _pid_is_alive(pid):
            console.warn(Keys.service.windows_killed_old(pid=pid))
            try:
                subprocess.run(
                    ["taskkill", "/PID", str(pid), "/F"],
                    stderr=subprocess.DEVNULL,
                )
            except Exception:
                pass

    def _create_shortcut(self, target: str, args: list):
        shortcut = self._shortcut()
        try:
            shortcut.parent.mkdir(parents=True, exist_ok=True)
            arg_str = " ".join(args)
            ps = (
                "$ws = New-Object -ComObject WScript.Shell; "
                f"$sc = $ws.CreateShortcut('{shortcut}'); "
                f"$sc.TargetPath = '{target}'; "
                f"$sc.Arguments = '{arg_str}'; "
                "$sc.WindowStyle = 7; "
                "$sc.Save()"
            )
            subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            console.err(Keys.service.windows_shortcut_failed)

    def setup(self, host: str, port: int) -> int:
        self._data_dir().mkdir(parents=True, exist_ok=True)
        self._stop_old()
        exec_path = self.get_executable_path()
        log_file = self._log_file()
        cmd = [
            exec_path, "service", "serve",
            "--host", host, "--port", str(port),
            "--log-file", str(log_file),
        ]
        try:
            proc = subprocess.Popen(
                cmd, creationflags=self.CREATE_NO_WINDOW
            )
        except Exception as e:
            console.err(Keys.daemon.failed_setup_systemd(error=str(e)))
            return 1
        self._pid_file().write_text(str(proc.pid))
        self._conf_file().write_text(json.dumps({
            "host": host,
            "port": port,
            "log_file": str(log_file),
        }))
        self._create_shortcut(exec_path, cmd[1:])
        console.ok(Keys.service.windows_shortcut_created)
        console.ok(Keys.service.windows_spawned(pid=proc.pid))
        console.ok(Keys.service.setup_complete)
        return 0

    def remove(self) -> int:
        self._stop_old()
        removed = False
        for path, key in (
            (self._pid_file(), Keys.service.windows_removed_pid),
            (self._log_file(), Keys.service.windows_removed_log),
            (self._shortcut(), Keys.service.windows_removed_shortcut),
        ):
            try:
                if path.exists():
                    if path.is_dir():
                        shutil.rmtree(path)
                    else:
                        path.unlink()
                    console.ok(key)
                    removed = True
            except Exception:
                pass
        if not removed:
            console.err(Keys.daemon.daemon_not_installed)
            return 1
        return 0

    def status(self) -> int:
        console.ok(Keys.service.status_title)
        pid = self._read_pid()
        running = pid is not None and _pid_is_alive(pid)
        registered = (
            "Yes"
            if self._shortcut().exists() or self._conf_file().exists()
            else "No"
        )
        console.warn(Keys.service.status_registered(value=registered))
        if running:
            console.warn(Keys.service.status_active(value=f"running (PID {pid})"))
        else:
            console.warn(Keys.service.status_active(value="not running"))
        enabled = "Yes" if self._shortcut().exists() else "No"
        console.warn(Keys.service.status_enabled(value=enabled))
        console.warn(Keys.service.status_linger(value="N/A"))
        port = self._read_port()
        console.warn(Keys.service.status_port(port=port))
        ip = detect_lan_ip()
        url = f"http://{ip}:{port}" if ip else "N/A"
        console.warn(Keys.service.status_url(url=url))
        return 0

    def logs(self, tail: int, follow: bool) -> int:
        log_file = self._log_file()
        if not log_file.exists():
            console.err(Keys.service.logs_not_available)
            return 1
        lines = log_file.read_text(
            encoding="utf-8", errors="replace"
        ).splitlines()
        start = max(0, len(lines) - tail)
        for line in lines[start:]:
            print(line)
        if follow:
            console.warn(Keys.service.logs_follow_hint)
            position = len(lines)
            try:
                while True:
                    time.sleep(1)
                    new = log_file.read_text(
                        encoding="utf-8", errors="replace"
                    ).splitlines()
                    for line in new[position:]:
                        print(line)
                    position = len(new)
            except KeyboardInterrupt:
                pass
        return 0


class NullServiceManager(ServiceManager):
    """Stub manager for unsupported platforms (Termux, WSL, etc.)."""

    def setup(self, host: str, port: int) -> int:
        console.warn(Keys.service.not_supported)
        console.warn(Keys.daemon.run_daemon_manually(host=host, port=port))
        return 0

    def remove(self) -> int:
        console.warn(Keys.service.remove_not_supported)
        return 0

    def status(self) -> int:
        console.warn(Keys.service.not_supported)
        return 0

    def logs(self, tail: int, follow: bool) -> int:
        console.warn(Keys.service.not_supported)
        return 1


_service_manager: ServiceManager | None = None


def get_service_manager() -> ServiceManager:
    global _service_manager
    if _service_manager is None:
        if env.get("is_windows"):
            _service_manager = WindowsServiceManager()
        elif env.get("is_termux"):
            _service_manager = NullServiceManager()
        else:
            _service_manager = SystemdServiceManager()
    return _service_manager
