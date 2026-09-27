"""
Daemon URL display utility.
Prints URL + QR for a running daemon, and exposes shared helpers used by
both ``service daemon display`` and ``service serve``:

* :func:`detect_lan_ip` -- cross-platform LAN IPv4 detection.
* :func:`get_daemon_port` -- reads the configured daemon port.
* :func:`is_service_running` -- checks whether the daemon process is alive.
"""
import json
import os
import re
import subprocess
from pathlib import Path

from ...core.domain.env import env
from ...utils.console import console
from ...utils.formatters import color
from ...utils.i18n_keys import Keys


def get_best_ip():
    from ...utils.network import get_best_ip as _gbip
    return _gbip()



def _get_ip_from_ip_a():
    """Parse `ip -4 -o addr show` for non-loopback inet addresses,
    filtering out Docker/bridge/veth interfaces.

    Returns a list of IPv4 addresses (empty if detection fails).
    """
    try:
        out = subprocess.check_output(
            ["ip", "-4", "-o", "addr", "show"],
            stderr=subprocess.DEVNULL, text=True
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return []

    ips: list[str] = []
    for line in out.splitlines():
        parts = line.split()
        if len(parts) < 4:
            continue
        iface = parts[1].strip()
        if iface in ("lo",) or iface.startswith(("docker", "br-", "veth", "tun", "virbr")):
            continue
        m = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', line)
        if m:
            ip = m.group(1)
            if not ip.startswith("127.") and not ip.startswith("169.254."):
                ips.append(ip)
    return ips


def _get_ip_from_ipconfig():
    """Parse `ipconfig` (Windows) for all active adapter IPv4 addresses.

    Adapters carrying a default gateway are listed first -- they are the
    ones phones on the same LAN usually reach -- followed by gateway-less
    adapters (e.g. the PC's own Mobile Hotspot). Loopback and APIPA
    link-local addresses are skipped, and disconnected adapters ignored.
    """
    try:
        out = subprocess.check_output(
            ["ipconfig"],
            stderr=subprocess.DEVNULL, text=True
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return []

    # Split ipconfig output into per-adapter blocks. A block header is a
    # non-indented line ending with ':' (e.g. "Wireless LAN adapter Wi-Fi:").
    blocks: list[list[str]] = []
    for line in out.splitlines():
        if re.match(r'^\S.*:$', line):
            blocks.append([line])
        elif blocks:
            blocks[-1].append(line)

    gateway_ips: list[str] = []
    other_ips: list[str] = []
    for block in blocks:
        text = "\n".join(block)
        if "Media disconnected" in text or "Media State" in text:
            continue
        m = re.search(r'IPv4[^\n]*[:\s]+(\d+\.\d+\.\d+\.\d+)', text)
        if not m:
            continue
        ip = m.group(1)
        if ip.startswith("127.") or ip.startswith("169.254."):
            continue
        has_gateway = re.search(r'Default Gateway[^\n]*:\s*\S', text) is not None
        (gateway_ips if has_gateway else other_ips).append(ip)

    seen: set[str] = set()
    ordered: list[str] = []
    for ip in gateway_ips + other_ips:
        if ip not in seen:
            seen.add(ip)
            ordered.append(ip)
    return ordered


def detect_lan_ips():
    """Return all candidate LAN IPv4 addresses for this machine.

    Falls back to :func:`get_best_ip` (the default-route address) when
    no native adapter has an IPv4 address.
    """
    if env.get('is_windows'):
        ips = _get_ip_from_ipconfig()
    else:
        ips = _get_ip_from_ip_a()
    if not ips:
        best = get_best_ip()
        if best and not best.startswith("127."):
            ips = [best]
    return ips


def detect_lan_ip():
    """Best-effort single LAN IP, cross-platform.

    Prefers the default-route address from :func:`get_best_ip` (this is
    the pre-2.3.0 behaviour and matches the IP phones on the same LAN
    actually reach), falling back to the first adapter-detected IP.
    """
    best = get_best_ip()
    if best and not best.startswith("127."):
        return best
    ips = detect_lan_ips()
    return ips[0] if ips else None


def daemon_urls(port: int):
    """Return ``http://<ip>:<port>`` for every detected LAN IP."""
    return [f"http://{ip}:{port}" for ip in detect_lan_ips()]


def _pid_is_alive(pid: int) -> bool:
    """Check whether a PID refers to a live process.

    NOTE: ``os.kill(pid, 0)`` is only safe on POSIX. On Windows, any
    signal other than ``CTRL_C_EVENT``/``CTRL_BREAK_EVENT`` is sent via
    ``TerminateProcess`` -- i.e. it *kills* the process instead of
    probing it. So on Windows we probe with ``tasklist`` instead.
    """
    if not pid or pid <= 0:
        return False
    if env.get("is_windows"):
        return _win_pid_is_alive(pid)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _win_pid_is_alive(pid: int) -> bool:
    """Probe a PID on Windows without killing it (tasklist filter)."""
    try:
        out = subprocess.check_output(
            ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=15,
        )
        return re.search(rf"\b{pid}\b", out) is not None
    except Exception:
        return False


def get_daemon_port() -> int:
    """Read the daemon port from the platform service state.

    Order: systemd service file (Linux) -> ``<data_dir>/daemon.json``
    (Windows) -> ``config.json`` ``daemon_port`` -> default 7370.
    """
    service_path = env.get('service_path')
    config_path = env.get('config_path')
    if os.path.exists(service_path):
        text = Path(service_path).read_text()
        m = re.search(r'--port\s+(\d+)', text)
        if m:
            return int(m.group(1))

    daemon_json = Path(env.get('data_dir')) / 'daemon.json'
    if daemon_json.exists():
        try:
            with open(daemon_json) as f:
                cfg = json.load(f)
            port = cfg.get('port')
            if port:
                return int(port)
        except Exception:
            pass

    if os.path.exists(config_path):
        try:
            with open(config_path) as f:
                cfg = json.load(f)
            port = cfg.get('daemon_port')
            if port:
                return int(port)
        except Exception:
            pass

    return 7370


def is_service_running() -> bool:
    """Check whether the daemon service is currently active.

    Linux: systemd unit is-active. Windows: PID from ``daemon.pid``.
    """
    if env.get('is_windows'):
        pid = _read_windows_pid()
        return _pid_is_alive(pid)

    try:
        out = subprocess.check_output(
            ["systemctl", "--user", "is-active", "tetodl.service"],
            stderr=subprocess.DEVNULL, text=True
        )
        return "active" in out.strip()
    except Exception:
        return False


def _read_windows_pid() -> int:
    """Read the PID stored by ``WindowsServiceManager`` at setup."""
    pid_file = Path(env.get('data_dir')) / 'daemon.pid'
    try:
        return int(pid_file.read_text().strip())
    except Exception:
        return 0


def display_daemon_url():
    """Main entry for `tetodl service daemon display`."""
    running = is_service_running()
    if not running:
        service_path = env.get('service_path')
        config_path = env.get('config_path')
        daemon_json = Path(env.get('data_dir')) / 'daemon.json'
        has_state = (os.path.exists(service_path)
                     or os.path.exists(config_path)
                     or daemon_json.exists())
        if not has_state:
            console.err(Keys.daemon.not_configured)
            console.warn(Keys.daemon.run_setup)
            console.warn(Keys.daemon.or_run_manually)
        else:
            console.warn(Keys.daemon.registered_not_running)
            if not env.get('is_windows'):
                console.warn(Keys.daemon.start_with_systemctl)
            else:
                console.warn(Keys.daemon.run_setup)
        return 1

    # State: running
    port = get_daemon_port()
    urls = daemon_urls(port)

    if not urls:
        console.err(Keys.daemon.could_not_detect_lan_ip)
        return 1

    print()
    for url in urls:
        console.ok(Keys.daemon.daemon_url(url=color(url, 'c')))
    console.warn(Keys.daemon.daemon_port(port=port))
    print()

    try:
        import qrcode
        qr = qrcode.QRCode(version=1, box_size=1, border=1)
        qr.add_data(urls[0])
        qr.make(fit=True)
        qr.print_ascii(invert=True)
        print()
        console.warn(Keys.daemon.scan_qr)
    except ImportError:
        console.warn(Keys.daemon.open_browser(url=urls[0]))

    return 0
