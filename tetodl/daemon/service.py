import os
import sys
import shutil
import subprocess
from pathlib import Path

from ..utils.styles import print_success, print_error, print_info, print_process, color

def get_executable_path():
    """
    Secara pintar mencari lokasi executable tetodl saat ini.
    Menghindari error jika dipanggil via symlink, venv, atau shell script.
    """
    # 1. Cek jika tetodl ada di PATH environment (misal diinstall via yay/pip)
    tetodl_path = shutil.which("tetodl")
    if tetodl_path:
        return tetodl_path
    
    # 2. Fallback: Ambil dari path argumen saat ini (misal ./tetodl.sh)
    return os.path.abspath(sys.argv[0])

def setup_systemd(host: str, port: int):
    """Membuat dan mendaftarkan file .service ke Systemd User."""
    print_process("Configuring systemd user service...")
    
    exec_path = get_executable_path()
    
    # Ambil PATH environment saat ini (penting agar yt-dlp & ffmpeg terdeteksi oleh daemon)
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
        
        with open(service_file, "w") as f:
            f.write(service_content)

        subprocess.run(["systemctl", "--user", "daemon-reload"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        print_success(f"Systemd service file created at: {service_file}\n")
        print_info(
            f"To start the daemon right now, run: {color("systemctl --user start tetodl.service", 'g', True)}"
        )
        print_info(
            f"To enable it to start on boot automatically, run: {color("systemctl --user enable tetodl.service", 'g', True)}"
        )
        print_info(
            f"To ensure the daemon starts on boot even before you log in: {color(f"sudo loginctl enable-linger {os.getenv('USER')}", 'g', True)}"
        )
        
    except Exception as e:
        print_error(f"Failed to setup systemd service: {e}")

def remove_systemd():
    """Menghapus file .service dengan aman."""
    print_process("Removing systemd service...")
    service_file = Path.home() / ".config" / "systemd" / "user" / "tetodl.service"
    
    if not service_file.exists():
        print_error("TetoDL daemon is not installed.")
        return

    try:
        # Hentikan dan matikan autostart terlebih dahulu
        subprocess.run(["systemctl", "--user", "stop", "tetodl.service"], stderr=subprocess.DEVNULL)
        subprocess.run(["systemctl", "--user", "disable", "tetodl.service"], stderr=subprocess.DEVNULL)
        
        # Hapus file secara fisik
        os.remove(service_file)
        
        # Reload daemon
        subprocess.run(["systemctl", "--user", "daemon-reload"], stderr=subprocess.DEVNULL)
        
        print_success("Daemon service successfully removed.")
    except Exception as e:
        print_error(f"Failed to remove systemd service: {e}")