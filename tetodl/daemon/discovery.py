import socket
from zeroconf import ServiceInfo, Zeroconf
from ..utils.console import console
from ..utils.i18n_keys import Keys

class MDNSBroadcaster:
    def __init__(self, port: int, hostname: str = "tetodl"):
        self.port = port
        self.hostname = f"{hostname}.local."
        self.zeroconf = None
        self.info = None

    def start(self):
        try:
            from ..utils.network import get_best_ip
            ip_str = get_best_ip()
            ip_bytes = socket.inet_aton(ip_str)

            self.info = ServiceInfo(
                "_http._tcp.local.",
                f"TetoDL Web API._http._tcp.local.",
                addresses=[ip_bytes],
                port=self.port,
                server=self.hostname,
                properties={"version": "1.3.0", "description": "TetoDL Daemon"}
            )
            self.zeroconf = Zeroconf()
            self.zeroconf.register_service(self.info)
            console.warn(Keys.daemon.mdns_broadcast_active(hostname=self.hostname[:-1], port=self.port))
        except Exception as e:
            console.warn(Keys.daemon.mdns_broadcast_failed(error=e))

    def stop(self):
        if self.zeroconf and self.info:
            self.zeroconf.unregister_service(self.info)
            self.zeroconf.close()