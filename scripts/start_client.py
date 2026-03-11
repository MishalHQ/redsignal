#!/usr/bin/env python3
"""
RedSignal Client Agent Startup Script
Starts the client agent with proper configuration.
"""

import asyncio
import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from redsignal.client.agent import RedSignalAgent
from redsignal.common.logger import get_logger

logger = get_logger(__name__)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="RedSignal Client Agent - C2 Emulation Client"
    )

    parser.add_argument(
        "--config",
        "-c",
        type=str,
        default="config/client_config.yaml",
        help="Path to client configuration file",
    )

    parser.add_argument(
        "--server",
        "-s",
        type=str,
        help="C2 server URL (overrides config)",
    )

    parser.add_argument(
        "--beacon-interval",
        "-b",
        type=int,
        help="Beacon interval in seconds (overrides config)",
    )

    parser.add_argument(
        "--client-id",
        type=str,
        help="Client identifier (overrides config)",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    return parser.parse_args()


async def main():
    """Main entry point for the client."""
    args = parse_arguments()

    try:
        # Create and configure agent
        agent = RedSignalAgent(args.config)

        # Override config with command line arguments
        if args.server:
            agent.server_url = args.server
            agent.config["client"]["server_url"] = args.server

        if args.beacon_interval:
            agent.beacon_interval = args.beacon_interval
            agent.config["client"]["beacon_interval"] = args.beacon_interval

        if args.client_id:
            agent.client_id = args.client_id

        if args.debug:
            import logging

            logging.getLogger().setLevel(logging.DEBUG)

        # Display startup information
        print("🔴 RedSignal Client Agent")
        print("=" * 50)
        print(f"Client ID: {agent.client_id}")
        print(f"Server URL: {agent.server_url}")
        print(f"Beacon Interval: {agent.beacon_interval}s")
        print("=" * 50)
        print("Press Ctrl+C to stop the agent")
        print()

        # Start agent
        await agent.start()

    except KeyboardInterrupt:
        logger.info("Agent stopped by user")
    except Exception as e:
        logger.error(f"Agent startup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

