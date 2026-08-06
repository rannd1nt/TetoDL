"""
Network utilities for CLI: file sharing server (FastAPI).
Extracted from utils/network.py to separate CLI-specific concerns.
"""
import re
import shutil
import subprocess
from pathlib import Path
from urllib.parse import quote

from tetodl.core.domain.env import env
from tetodl.utils.console import console
from tetodl.utils.i18n_keys import Keys
from tetodl.utils.network import find_free_port, get_best_ip


def _ufw_active() -> bool:
    """True if UFW is enabled (reads config; no sudo needed)."""
    try:
        return "ENABLED=yes" in Path("/etc/ufw/ufw.conf").read_text()
    except OSError:
        return False


def _ufw_allows_port(port) -> bool:
    """True if the port appears in the UFW user rules allow-list."""
    try:
        rules = Path("/etc/ufw/user.rules").read_text()
    except OSError:
        return True
    return re.search(rf"dport\s+{port}\b", rules) is not None


def check_firewall_status(port):
    """
    Memberikan HINTS kepada user jika port diblokir oleh firewall yang ketat.
    """
    if env.get("is_wsl"):
        return

    if shutil.which("ufw"):
        if _ufw_active() and not _ufw_allows_port(port):
            console.rich.print("\n[dim][Tip] Connection to your phone may be blocked by UFW:[/dim]")
            console.rich.print(f"[dim cyan]  sudo ufw allow {port}/tcp[/dim cyan]")

    elif shutil.which("firewall-cmd"):
        console.rich.print("\n[dim][Tip] If connection fails, allow port in FirewallD:[/dim]")
        console.rich.print(f"[dim cyan]  sudo firewall-cmd --add-port={port}/tcp --temporary[/dim cyan]")


def ensure_windows_firewall_allow(port):
    """Open an inbound TCP port in Windows Defender Firewall.

    Without this rule the API server still binds ``0.0.0.0`` but the
    OS firewall silently drops packets, so phones on the same Wi-Fi /
    hotspot can't reach ``http://<lan-ip>:<port>`` even though the
    server is running. Idempotent: netsh re-adding an identical rule
    just replaces it.

    ``netsh advfirewall`` requires elevation, so when we're not running
    as admin we detect the failure and print an actionable tip instead
    of silently pretending the port is open.
    """
    if not env.get("is_windows"):
        return
    rule = f"TetoDL API {port}"
    try:
        check = subprocess.run(
            ["netsh", "advfirewall", "firewall", "show", "rule",
             f"name={rule}"],
            capture_output=True, text=True, timeout=20,
        )
        if check.returncode == 0 and f"name={rule}" in check.stdout:
            return
    except Exception:
        pass
    try:
        add = subprocess.run(
            ["netsh", "advfirewall", "firewall", "add", "rule",
             f"name={rule}", "dir=in", "action=allow",
             "protocol=TCP", f"localport={port}",
             "profile=any"],
            capture_output=True, text=True, timeout=20,
        )
        if add.returncode != 0:
            console.rich.print(
                "\n[dim][Tip] Phone can't reach the server if Windows Firewall blocks the port."
            )
            console.rich.print(
                "[dim cyan]  Run this as Administrator (or once, permanently):[/dim cyan]"
            )
            console.rich.print(
                f"[dim cyan]  netsh advfirewall firewall add rule name=\"TetoDL API {port}\" dir=in action=allow protocol=TCP localport={port} profile=any[/dim cyan]"
            )
    except Exception:
        pass


def start_share_server(file_path_str: str, start_port=8989):
    import asyncio as _asyncio
    import threading as _threading
    import time as _time

    import qrcode
    import uvicorn
    from fastapi import FastAPI

    from tetodl.ui.share import create_share_router

    path = Path(file_path_str).resolve()

    if not path.exists():
        console.err(Keys.net.file_dir_not_found(path=str(path)))
        return

    port = find_free_port(start_port)
    if port is None:
        console.err(Keys.net.ports_busy(start=start_port, end=start_port+10))
        return

    if env.get("is_wsl"):
        ip_address = '127.0.0.1'
    else:
        ip_address = get_best_ip()

    if env.get("is_wsl"):
        console.rich.print("\n[bold yellow][!] WSL Environment Detected[/bold yellow]")
        console.warn(Keys.net.wsl_nat_warning)
        console.warn(Keys.net.wsl_share_tip)

    if ip_address.startswith("127.") and not env.get("is_wsl"):
        console.err(Keys.net.no_lan_ip)
        console.warn(Keys.net.localhost_only)

    if path.is_file():
        serve_dir = path.parent
        filename_url = quote(path.name)
        target_url = f"http://{ip_address}:{port}/{filename_url}"
    else:
        serve_dir = path
        target_url = f"http://{ip_address}:{port}/"

    app = FastAPI()
    router = create_share_router(str(serve_dir))
    app.include_router(router)

    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="error")
    server = uvicorn.Server(config)

    def _run():
        _asyncio.run(server.serve())

    thread = _threading.Thread(target=_run, name="share-server", daemon=True)
    thread.start()

    while not server.started:
        _time.sleep(0.05)

    console.ok(Keys.net.sharing_started)
    console.rich.print()

    console.rich.print(f"Hosting: [cyan]{path.name}[/cyan]")
    console.rich.print(f"Address: [yellow]{target_url}[/yellow]")

    check_firewall_status(port)

    qr = qrcode.QRCode(version=1, box_size=1, border=1)
    qr.add_data(target_url)
    qr.make(fit=True)

    console.rich.print()
    qr.print_ascii(invert=True)

    console.rich.print()
    console.rich.print("[dim]Scan QR above with your phone camera.[/dim]")
    console.rich.print("[bold red]Press Ctrl+C to stop server.[/bold red]")

    try:
        while thread.is_alive():
            thread.join(0.5)
    except KeyboardInterrupt:
        console.rich.print("\n[yellow]Sharing stopped.[/yellow]")
        raise KeyboardInterrupt
