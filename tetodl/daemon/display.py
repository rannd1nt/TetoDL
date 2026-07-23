"""
Daemon URL display utility (--display flag).
Parses ip a for LAN IP, reads port from config/service, prints URL + QR.
"""
import json
import os
import re
import subprocess
from pathlib import Path

from ..constants import CONFIG_PATH, SERVICE_PATH
from ..utils.console import console
from ..utils.formatters import color
from ..utils.i18n_keys import Keys


def _get_ip_from_ip_a():
    """Parse `ip -4 -o addr show` for non-loopback inet addresses,
    filtering out Docker/bridge/veth interfaces."""
    try:
        out = subprocess.check_output(
            ["ip", "-4", "-o", "addr", "show"],
            stderr=subprocess.DEVNULL, text=True
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None

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
            if not ip.startswith("127."):
                return ip
    return None


def _get_daemon_port():
    """Read port from systemd service file, or fall back to default 7370."""
    if os.path.exists(SERVICE_PATH):
        text = Path(SERVICE_PATH).read_text()
        m = re.search(r'--port\s+(\d+)', text)
        if m:
            return int(m.group(1))

    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH) as f:
                cfg = json.load(f)
            port = cfg.get("daemon_port")
            if port:
                return int(port)
        except Exception:
            pass

    return 7370


def _is_service_running():
    """Check if the systemd tetodl service is currently active."""
    try:
        out = subprocess.check_output(
            ["systemctl", "--user", "is-active", "tetodl.service"],
            stderr=subprocess.DEVNULL, text=True
        )
        return "active" in out.strip()
    except Exception:
        return False


def display_daemon_url():
    """Main entry for `tetodl daemon --display`."""
    service_exists = os.path.exists(SERVICE_PATH)
    config_exists = os.path.exists(CONFIG_PATH)

    if not service_exists and not config_exists:
        console.err(Keys.daemon.not_configured)
        console.warn("Run 'tetodl daemon --setup' to register a systemd service,")
        console.warn("or 'tetodl daemon --run' to start it manually.")
        return 1

    running = _is_service_running()
    if not running:
        if service_exists:
            console.warn(Keys.daemon.registered_not_running)
            console.warn(Keys.daemon.start_with_systemctl)
        else:
            console.warn(Keys.daemon.service_unavailable)
            console.warn("Run 'tetodl daemon --setup' to register a systemd service,")
        return 1

    # State 3: running
    port = _get_daemon_port()
    ip = _get_ip_from_ip_a()

    if not ip:
        console.err(Keys.daemon.could_not_detect_lan_ip)
        return 1

    url = f"http://{ip}:{port}"
    print()
    console.ok(f"TetoDL Daemon URL: {color(url, 'c')}")
    console.warn(Keys.daemon.daemon_port(port=port))
    print()

    try:
        import qrcode
        qr = qrcode.QRCode(version=1, box_size=1, border=1)
        qr.add_data(url)
        qr.make(fit=True)
        qr.print_ascii(invert=True)
        print()
        console.warn(Keys.daemon.scan_qr)
    except ImportError:
        console.warn(Keys.daemon.open_browser(url=url))

    return 0
