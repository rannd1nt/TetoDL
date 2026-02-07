import subprocess
from ..constants import IS_WSL
from .styles import print_info, print_success, print_error, console, print_neutral


def get_wsl_ip():
    """Ambil IP Address internal WSL."""
    cmd = "hostname -I | awk '{print $1}'"
    try:
        return subprocess.check_output(cmd, shell=True).decode().strip()
    except:
        return None

def get_windows_host_ip():
    """
    Ambil IP Address Windows (Host) dari dalam WSL.
    """
    try:
        cmd = "ip route show | grep default | awk '{print $3}'"
        gateway = subprocess.check_output(cmd, shell=True).decode().strip()
        
        ps_cmd = "powershell.exe -Command \"(Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias 'Wi-Fi').IPAddress\""
        
        ps_cmd_universal = "powershell.exe -Command \"Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notlike '*Loopback*' -and $_.InterfaceAlias -notlike '*vEthernet*' } | Select-Object -ExpandProperty IPAddress\""
        
        output = subprocess.check_output(ps_cmd_universal, shell=True).decode().strip().split('\r\n')[0]
        return output
    except Exception as e:
        return None

def setup_wsl_port_forwarding(port=8989):
    """
    Menjalankan command netsh via PowerShell (Admin) untuk bridging port.
    """
    wsl_ip = get_wsl_ip()
    if not wsl_ip:
        print_error("Could not detect WSL IP.")
        return False

    print_info(f"WSL Detected. IP: {wsl_ip}")
    print_info("WSL is behind a NAT. To allow phone connection, we need to forward port on Windows.")
    
    # User Confirmation
    try:
        choice = input(print_neutral("Attempt to auto-configure Windows Port Forwarding (Admin UAC will pop up)? (Y/n) > ", str_only=True, symbol="[?]")).lower()
    except KeyboardInterrupt:
        return False

    if choice not in ['y', 'yes', '']:
        return False

    # Forwarding
    netsh_cmd = f"netsh interface portproxy add v4tov4 listenport={port} listenaddress=0.0.0.0 connectport={port} connectaddress={wsl_ip}"
    
    # Firewall Rule
    firewall_cmd = f"netsh advfirewall firewall add rule name=\"TetoDL Share\" dir=in action=allow protocol=TCP localport={port}"
    
    full_ps_command = f"Start-Process powershell -Verb RunAs -ArgumentList '-Command {netsh_cmd}; {firewall_cmd}; Write-Host Done. Press any key...; Read-Host'"

    try:
        print_info("Requesting Admin privileges on Windows...")
        subprocess.call(f"powershell.exe -Command \"{full_ps_command}\"", shell=True)
        print_success("Windows Port Forwarding configured!")
        
        windows_ip = get_windows_host_ip()
        return windows_ip
        
    except Exception as e:
        print_error(f"Failed to configure WSL bridge: {e}")
        return False

def cleanup_wsl_forwarding(port=8989):
    if not IS_WSL: return
    pass