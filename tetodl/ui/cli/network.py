"""
Network utilities for CLI: file sharing server (FastAPI).
Extracted from utils/network.py to separate CLI-specific concerns.
"""
import os
import shutil
import socket
from pathlib import Path
from urllib.parse import quote

from tetodl.core.domain.env import env
from tetodl.utils.console import console
from tetodl.utils.i18n_keys import Keys
from tetodl.utils.formatters import console as rich_console
from tetodl.utils.network import find_free_port, get_best_ip


def check_firewall_status(port):
    """
    Memberikan HINTS kepada user jika terdeteksi di Distro yang ketat.
    """
    if env.get("is_wsl"):
        return

    if shutil.which("ufw"):
        rich_console.print("\n[dim][Tip] If connection fails, allow port in UFW:[/dim]")
        rich_console.print(f"[dim cyan]  sudo ufw allow {port}/tcp[/dim cyan]")

    elif shutil.which("firewall-cmd"):
        rich_console.print("\n[dim][Tip] If connection fails, allow port in FirewallD:[/dim]")
        rich_console.print(f"[dim cyan]  sudo firewall-cmd --add-port={port}/tcp --temporary[/dim cyan]")


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
        rich_console.print("\n[bold yellow][!] WSL Environment Detected[/bold yellow]")
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
    rich_console.print()

    rich_console.print(f"Hosting: [cyan]{path.name}[/cyan]")
    rich_console.print(f"Address: [yellow]{target_url}[/yellow]")

    check_firewall_status(port)

    qr = qrcode.QRCode(version=1, box_size=1, border=1)
    qr.add_data(target_url)
    qr.make(fit=True)

    rich_console.print()
    qr.print_ascii(invert=True)

    rich_console.print()
    rich_console.print("[dim]Scan QR above with your phone camera.[/dim]")
    rich_console.print("[bold red]Press Ctrl+C to stop server.[/bold red]")

    try:
        while thread.is_alive():
            thread.join(0.5)
    except KeyboardInterrupt:
        rich_console.print("\n[yellow]Sharing stopped.[/yellow]")
        raise KeyboardInterrupt
