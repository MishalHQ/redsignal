"""
RedSignal C2 Server - Main server component for command and control operations.
Handles client registration, command dispatch, and response collection.
"""

import asyncio
import json
import time
import uuid
from typing import Dict, Any, List, Optional
from pathlib import Path
import yaml

from fastapi import FastAPI, HTTPException, Depends, Request, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

from ..common.protocol import (
    BeaconMessage,
    CommandMessage,
    ResponseMessage,
    ProtocolHandler,
    MessageType,
    CommandType,
)
from ..common.logger import get_logger
from .client_manager import ClientManager
from .command_handler import CommandHandler
from .web_interface import create_web_interface

logger = get_logger(__name__)


class RedSignalServer:
    """Main C2 server for RedSignal platform."""

    def __init__(self, config_path: str = "config/server_config.yaml"):
        self.config = self._load_config(config_path)
        self.app = FastAPI(
            title="RedSignal C2 Server",
            description="Command and Control Emulation Platform",
            version="1.0.0",
        )

        # Initialize components
        self.client_manager = ClientManager()
        self.command_handler = CommandHandler()
        self.protocol_handler = ProtocolHandler()

        # Security
        self.security = HTTPBearer()
        self.api_key = self.config["security"]["api_key"]

        # Setup FastAPI app
        self._setup_middleware()
        self._setup_routes()

        logger.info("RedSignal C2 Server initialized")

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load server configuration from YAML file."""
        try:
            with open(config_path, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            # Return default config
            return {
                "server": {"host": "0.0.0.0", "port": 8443, "ssl_enabled": False},
                "security": {"api_key": "redsignal-demo-key-2024"},
                "features": {"web_interface": True},
            }

    def _setup_middleware(self):
        """Configure FastAPI middleware."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _setup_routes(self):
        """Setup API routes."""

        @self.app.post("/api/register")
        async def register_client(request: Request):
            """Register a new client agent."""
            try:
                data = await request.json()
                client_id = data.get("client_id")

                if not client_id:
                    raise HTTPException(status_code=400, detail="Missing client_id")

                # Register client
                self.client_manager.register_client(
                    client_id=client_id,
                    hostname=data.get("hostname", "unknown"),
                    platform=data.get("platform", "unknown"),
                    ip_address=data.get("ip_address", "127.0.0.1"),
                )

                logger.info(f"Client registered: {client_id}")
                return {"status": "registered", "client_id": client_id}

            except Exception as e:
                logger.error(f"Registration error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/beacon")
        async def receive_beacon(request: Request):
            """Receive beacon from client agent."""
            try:
                data = await request.body()
                beacon = self.protocol_handler.deserialize(data.decode())

                if not isinstance(beacon, BeaconMessage):
                    raise HTTPException(status_code=400, detail="Invalid beacon format")

                # Update client status
                self.client_manager.update_client_beacon(beacon)

                logger.debug(f"Beacon received from {beacon.client_id}")
                return {"status": "received"}

            except Exception as e:
                logger.error(f"Beacon error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/commands/{client_id}")
        async def get_commands(client_id: str):
            """Get pending commands for a client."""
            try:
                commands = self.command_handler.get_pending_commands(client_id)

                # Mark commands as dispatched
                for cmd in commands:
                    self.command_handler.mark_command_dispatched(cmd["message_id"])

                return {"commands": commands}

            except Exception as e:
                logger.error(f"Command retrieval error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/response")
        async def receive_response(request: Request):
            """Receive command response from client."""
            try:
                data = await request.body()
                response = self.protocol_handler.deserialize(data.decode())

                if not isinstance(response, ResponseMessage):
                    raise HTTPException(status_code=400, detail="Invalid response format")

                # Store response
                self.command_handler.store_response(response)

                logger.info(f"Response received from {response.client_id}")
                return {"status": "received"}

            except Exception as e:
                logger.error(f"Response error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/command")
        async def send_command(request: Request):
            """Send command to client (API endpoint)."""
            try:
                data = await request.json()

                command = CommandMessage(
                    client_id=data["client_id"],
                    command_type=CommandType(data["command_type"]),
                    parameters=data.get("parameters", {}),
                    timeout=data.get("timeout", 30),
                )

                # Queue command
                self.command_handler.queue_command(command)

                logger.info(
                    f"Command queued for {command.client_id}: {command.command_type.value}"
                )
                return {"status": "queued", "command_id": command.message_id}

            except Exception as e:
                logger.error(f"Command error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/clients")
        async def list_clients():
            """List all registered clients."""
            try:
                clients = self.client_manager.get_all_clients()
                return {"clients": clients}
            except Exception as e:
                logger.error(f"Client list error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/client/{client_id}")
        async def get_client_details(client_id: str):
            """Get detailed information about a specific client."""
            try:
                client = self.client_manager.get_client(client_id)
                if not client:
                    raise HTTPException(status_code=404, detail="Client not found")

                return {"client": client}
            except Exception as e:
                logger.error(f"Client details error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # Web interface routes
        if self.config["features"]["web_interface"]:
            self._setup_web_interface()

    def _setup_web_interface(self):
        """Setup web interface routes."""

        @self.app.get("/", response_class=HTMLResponse)
        async def web_dashboard():
            """Main dashboard page."""
            return create_web_interface().render_dashboard(
                clients=self.client_manager.get_all_clients(),
                recent_commands=self.command_handler.get_recent_commands(),
            )

        @self.app.get("/clients", response_class=HTMLResponse)
        async def web_clients():
            """Clients management page."""
            return create_web_interface().render_clients(
                clients=self.client_manager.get_all_clients()
            )

        @self.app.get("/commands", response_class=HTMLResponse)
        async def web_commands():
            """Commands management page."""
            return create_web_interface().render_commands(
                commands=self.command_handler.get_all_commands()
            )

    async def start(self):
        """Start the C2 server."""
        host = self.config["server"]["host"]
        port = self.config["server"]["port"]

        logger.info(f"Starting RedSignal C2 Server on {host}:{port}")

        config = uvicorn.Config(
            self.app,
            host=host,
            port=port,
            log_level="info",
        )

        server = uvicorn.Server(config)
        await server.serve()


def create_server(config_path: str = "config/server_config.yaml") -> RedSignalServer:
    """Factory function to create server instance."""
    return RedSignalServer(config_path)


async def main():
    """Main entry point for the server."""
    server = create_server()
    await server.start()


if __name__ == "__main__":
    asyncio.run(main())

