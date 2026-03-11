#!/usr/bin/env python3
"""
RedSignal C2 Server Startup Script
Starts the command and control server with proper configuration.
"""

import asyncio
import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from redsignal.server.c2_server import create_server
from redsignal.common.logger import get_logger

logger = get_logger(__name__)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="RedSignal C2 Server - Command and Control Emulation Platform"
    )

    parser.add_argument(
        "--config",
        "-c",
        type=str,
        default="config/server_config.yaml",
        help="Path to server configuration file",
    )

    parser.add_argument(
        "--host",
        type=str,
        help="Server host address (overrides config)",
    )

    parser.add_argument(
        "--port",
        "-p",
        type=int,
        help="Server port (overrides config)",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    return parser.parse_args()


async def main():
    """Main entry point for the server."""
    args = parse_arguments()

    try:
        # Create and configure server
        server = create_server(args.config)

        # Override config with command line arguments
        if args.host:
            server.config["server"]["host"] = args.host
        if args.port:
            server.config["server"]["port"] = args.port

        if args.debug:
            import logging

            logging.getLogger().setLevel(logging.DEBUG)

        # Display startup information
        host = server.config["server"]["host"]
        port = server.config["server"]["port"]

        print("🔴 RedSignal C2 Server")
        print("=" * 50)
        print(f"Server URL: http://{host}:{port}")
        print(f"Web Interface: http://{host}:{port}")
        print(f"API Endpoint: http://{host}:{port}/api")
        print("=" * 50)
        print("Press Ctrl+C to stop the server")
        print()

        # Start server
        await server.start()

    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server startup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

