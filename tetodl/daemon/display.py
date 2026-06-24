"""
Daemon URL display utility (--display flag).
Parses ip a for LAN IP, reads port from config/service, prints URL + QR.
"""
import os
import re
import json
import subprocess
from pathlib import Path

from ..utils.styles import print_error, print_info, print_success, color
from ..constants import SERVICE_PATH, CONFIG_PATH

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
        print_error("TetoDL daemon is not configured.")
        print_info("Run 'tetodl daemon --setup' to register a systemd service,")
        print_info("or 'tetodl daemon --run' to start it manually.")
        return 1

    running = _is_service_running()
    if not running:
        if service_exists:
            print_info("TetoDL daemon is registered but not currently running.")
            print_info("Start it with:  systemctl --user start tetodl.service")
        else:
            print_info("TetoDL daemon service is unavailable.")
            print_info("Run 'tetodl daemon --setup' to register a systemd service,")
        return 1

    # State 3: running
    port = _get_daemon_port()
    ip = _get_ip_from_ip_a()

    if not ip:
        print_error("Could not detect LAN IP address. Are you connected to a network?")
        return 1

    url = f"http://{ip}:{port}"
    print()
    print_success(f"TetoDL Daemon URL: {color(url, 'c')}")
    print_info(f"Port: {port}")
    print()

    try:
        import qrcode
        qr = qrcode.QRCode(version=1, box_size=1, border=1)
        qr.add_data(url)
        qr.make(fit=True)
        qr.print_ascii(invert=True)
        print()
        print_info("Scan QR above with your phone camera to open the daemon.")
    except ImportError:
        print_info(f"Open {url} in your browser.")

    return 0
