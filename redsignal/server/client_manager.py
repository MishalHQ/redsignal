"""
Client management for RedSignal C2 server.
Handles client registration, status tracking, and session management.
"""

import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from ..common.protocol import BeaconMessage
from ..common.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ClientInfo:
    """Information about a registered client."""

    client_id: str
    hostname: str
    platform: str
    ip_address: str
    registration_time: float
    last_beacon: float
    status: str  # 'active', 'inactive', 'offline'
    beacon_count: int
    last_command_time: Optional[float] = None
    last_response_time: Optional[float] = None


class ClientManager:
    """Manages registered clients and their status."""

    def __init__(self):
        self.clients: Dict[str, ClientInfo] = {}
        self.beacon_timeout = 120  # 2 minutes

    def register_client(
        self, client_id: str, hostname: str, platform: str, ip_address: str
    ) -> bool:
        """Register a new client or update existing registration."""
        try:
            current_time = time.time()

            if client_id in self.clients:
                # Update existing client
                client = self.clients[client_id]
                client.hostname = hostname
                client.platform = platform
                client.ip_address = ip_address
                client.last_beacon = current_time
                client.status = "active"
                logger.info(f"Updated existing client: {client_id}")
            else:
                # Register new client
                self.clients[client_id] = ClientInfo(
                    client_id=client_id,
                    hostname=hostname,
                    platform=platform,
                    ip_address=ip_address,
                    registration_time=current_time,
                    last_beacon=current_time,
                    status="active",
                    beacon_count=0,
                )
                logger.info(f"Registered new client: {client_id}")

            return True

        except Exception as e:
            logger.error(f"Client registration failed: {e}")
            return False

    def update_client_beacon(self, beacon: BeaconMessage) -> bool:
        """Update client status based on received beacon."""
        try:
            client_id = beacon.client_id

            if client_id not in self.clients:
                # Auto-register client from beacon
                self.register_client(
                    client_id=client_id,
                    hostname=beacon.hostname,
                    platform=beacon.os_info,
                    ip_address=beacon.ip_address,
                )

            # Update beacon info
            client = self.clients[client_id]
            client.last_beacon = beacon.timestamp
            client.beacon_count += 1
            client.status = "active"

            # Update system info if changed
            client.hostname = beacon.hostname
            client.ip_address = beacon.ip_address

            logger.debug(f"Updated beacon for client {client_id}")
            return True

        except Exception as e:
            logger.error(f"Beacon update failed: {e}")
            return False

    def get_client(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific client."""
        if client_id in self.clients:
            client = self.clients[client_id]
            self._update_client_status(client)
            return asdict(client)
        return None

    def get_all_clients(self) -> List[Dict[str, Any]]:
        """Get information about all registered clients."""
        clients = []
        current_time = time.time()

        for client in self.clients.values():
            self._update_client_status(client)
            client_dict = asdict(client)

            # Add computed fields
            client_dict["time_since_beacon"] = current_time - client.last_beacon
            client_dict["uptime"] = current_time - client.registration_time

            clients.append(client_dict)

        return sorted(clients, key=lambda x: x["last_beacon"], reverse=True)

    def get_active_clients(self) -> List[str]:
        """Get list of currently active client IDs."""
        active_clients = []

        for client_id, client in self.clients.items():
            self._update_client_status(client)
            if client.status == "active":
                active_clients.append(client_id)

        return active_clients

    def remove_client(self, client_id: str) -> bool:
        """Remove a client from the registry."""
        if client_id in self.clients:
            del self.clients[client_id]
            logger.info(f"Removed client: {client_id}")
            return True
        return False

    def update_command_time(self, client_id: str):
        """Update the last command time for a client."""
        if client_id in self.clients:
            self.clients[client_id].last_command_time = time.time()

    def update_response_time(self, client_id: str):
        """Update the last response time for a client."""
        if client_id in self.clients:
            self.clients[client_id].last_response_time = time.time()

    def _update_client_status(self, client: ClientInfo):
        """Update client status based on last beacon time."""
        current_time = time.time()
        time_since_beacon = current_time - client.last_beacon

        if time_since_beacon > self.beacon_timeout:
            client.status = "offline"
        elif time_since_beacon > self.beacon_timeout / 2:
            client.status = "inactive"
        else:
            client.status = "active"

    def get_client_statistics(self) -> Dict[str, Any]:
        """Get overall client statistics."""
        total_clients = len(self.clients)
        active_count = len([c for c in self.clients.values() if c.status == "active"])
        inactive_count = len(
            [c for c in self.clients.values() if c.status == "inactive"]
        )
        offline_count = len(
            [c for c in self.clients.values() if c.status == "offline"]
        )

        total_beacons = sum(c.beacon_count for c in self.clients.values())

        return {
            "total_clients": total_clients,
            "active_clients": active_count,
            "inactive_clients": inactive_count,
            "offline_clients": offline_count,
            "total_beacons": total_beacons,
            "beacon_timeout": self.beacon_timeout,
        }

