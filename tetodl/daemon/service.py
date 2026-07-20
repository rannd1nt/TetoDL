import os
import sys
import shutil
import subprocess
import abc
from pathlib import Path

from ..utils.console import console
from ..utils.formatters import color
from ..utils.i18n_keys import Keys
from ..constants import IS_WINDOWS


class ServiceManager(abc.ABC):
    """Abstract base for platform-specific daemon service management."""

    @abc.abstractmethod
    def setup(self, host: str, port: int):
        ...

    @abc.abstractmethod
    def remove(self):
        ...


class SystemdServiceManager(ServiceManager):
    """Systemd user service manager — Linux."""

    def get_executable_path(self):
        tetodl_path = shutil.which("tetodl")
        if tetodl_path:
            return tetodl_path
        return os.path.abspath(sys.argv[0])

    def setup(self, host: str, port: int):
        console.proc(Keys.daemon.configuring_systemd)
        exec_path = self.get_executable_path()
        env_path = os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin")

        service_content = f"""[Unit]
Description=TetoDL Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart={exec_path} daemon --run --host {host} --port {port}
Restart=always
RestartSec=5
Environment="PATH={env_path}"
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=default.target
"""
        systemd_dir = Path.home() / ".config" / "systemd" / "user"
        try:
            systemd_dir.mkdir(parents=True, exist_ok=True)
            service_file = systemd_dir / "tetodl.service"
            service_file.write_text(service_content)

            subprocess.run(["systemctl", "--user", "daemon-reload"],
                           check=True,
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)

            console.ok(Keys.daemon.service_file_created(path=str(service_file)))
            start_cmd = 'systemctl --user start tetodl.service'
            enable_cmd = 'systemctl --user enable tetodl.service'
            linger_cmd = f'sudo loginctl enable-linger {os.getenv("USER")}'
            console.warn(
                f"To start the daemon right now, run: {color(start_cmd, 'g', True)}"
            )
            console.warn(
                f"To enable it to start on boot automatically, run: {color(enable_cmd, 'g', True)}"
            )
            console.warn(
                f"To ensure the daemon starts on boot even before you log in: {color(linger_cmd, 'g', True)}"
            )
        except Exception as e:
            console.err(Keys.daemon.failed_setup_systemd(error=str(e)))

    def remove(self):
        console.proc(Keys.daemon.removing_systemd)
        service_file = Path.home() / ".config" / "systemd" / "user" / "tetodl.service"
        if not service_file.exists():
            console.err(Keys.daemon.daemon_not_installed)
            return

        try:
            subprocess.run(["systemctl", "--user", "stop", "tetodl.service"],
                           stderr=subprocess.DEVNULL)
            subprocess.run(["systemctl", "--user", "disable", "tetodl.service"],
                           stderr=subprocess.DEVNULL)
            service_file.unlink()
            subprocess.run(["systemctl", "--user", "daemon-reload"],
                           stderr=subprocess.DEVNULL)
            console.ok(Keys.daemon.daemon_removed)
        except Exception as e:
            console.err(Keys.daemon.failed_remove_systemd(error=str(e)))


class NullServiceManager(ServiceManager):
    """Stub service manager — Windows (not yet implemented)."""

    def setup(self, host: str, port: int):
        console.warn("Daemon service registration is not yet supported on Windows.")
        console.warn(f"You can still run the daemon manually: tetodl daemon --run --host {host} --port {port}")

    def remove(self):
        console.warn("Daemon service removal is not yet supported on Windows.")


_service_manager: ServiceManager | None = None


def get_service_manager() -> ServiceManager:
    global _service_manager
    if _service_manager is None:
        if IS_WINDOWS:
            _service_manager = NullServiceManager()
        else:
            _service_manager = SystemdServiceManager()
    return _service_manager


def setup_systemd(host: str, port: int):
    get_service_manager().setup(host, port)


def remove_systemd():
    get_service_manager().remove()
