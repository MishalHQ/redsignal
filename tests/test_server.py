"""
Unit tests for RedSignal C2 Server components.
"""

import unittest
import asyncio
import json
import time
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from redsignal.server.client_manager import ClientManager, ClientInfo
from redsignal.server.command_handler import CommandHandler, CommandStatus
from redsignal.common.protocol import (
    BeaconMessage,
    CommandMessage,
    CommandType,
    ResponseMessage,
)


class TestClientManager(unittest.TestCase):
    """Test cases for ClientManager."""

    def setUp(self):
        self.client_manager = ClientManager()

    def test_register_client(self):
        """Test client registration."""
        success = self.client_manager.register_client(
            client_id="test-client-1",
            hostname="test-host",
            platform="Linux",
            ip_address="192.168.1.100",
        )

        self.assertTrue(success)
        self.assertIn("test-client-1", self.client_manager.clients)

        client = self.client_manager.clients["test-client-1"]
        self.assertEqual(client.hostname, "test-host")
        self.assertEqual(client.platform, "Linux")
        self.assertEqual(client.status, "active")

    def test_update_beacon(self):
        """Test beacon update functionality."""
        # Create a beacon message
        beacon = BeaconMessage(
            client_id="test-client-2",
            hostname="beacon-host",
            os_info="Windows 10",
            ip_address="192.168.1.101",
            process_id=1234,
            uptime=3600.0,
        )

        success = self.client_manager.update_client_beacon(beacon)
        self.assertTrue(success)

        # Check if client was auto-registered
        self.assertIn("test-client-2", self.client_manager.clients)

        client = self.client_manager.clients["test-client-2"]
        self.assertEqual(client.beacon_count, 1)
        self.assertEqual(client.status, "active")

    def test_get_active_clients(self):
        """Test getting active clients."""
        # Register multiple clients
        self.client_manager.register_client("client-1", "host1", "Linux", "192.168.1.1")
        self.client_manager.register_client("client-2", "host2", "Windows", "192.168.1.2")

        # Make one client offline by setting old beacon time
        self.client_manager.clients["client-2"].last_beacon = time.time() - 200

        active_clients = self.client_manager.get_active_clients()
        self.assertEqual(len(active_clients), 1)
        self.assertIn("client-1", active_clients)

    def test_client_statistics(self):
        """Test client statistics generation."""
        # Register some clients
        self.client_manager.register_client("client-1", "host1", "Linux", "192.168.1.1")
        self.client_manager.register_client("client-2", "host2", "Windows", "192.168.1.2")

        stats = self.client_manager.get_client_statistics()

        self.assertEqual(stats["total_clients"], 2)
        self.assertGreaterEqual(stats["active_clients"], 0)
        self.assertIn("beacon_timeout", stats)


class TestCommandHandler(unittest.TestCase):
    """Test cases for CommandHandler."""

    def setUp(self):
        self.command_handler = CommandHandler()

    def test_queue_command(self):
        """Test command queuing."""
        command = CommandMessage(
            client_id="test-client",
            command_type=CommandType.COLLECT_SYSTEM_INFO,
            parameters={"type": "basic"},
            timeout=30,
        )

        command_id = self.command_handler.queue_command(command)

        self.assertIsNotNone(command_id)
        self.assertIn(command_id, self.command_handler.command_history)

        record = self.command_handler.command_history[command_id]
        self.assertEqual(record.status, CommandStatus.QUEUED)
        self.assertEqual(record.client_id, "test-client")

    def test_get_pending_commands(self):
        """Test retrieving pending commands."""
        command = CommandMessage(
            client_id="test-client",
            command_type=CommandType.LIST_FILES,
            parameters={"path": "/tmp"},
            timeout=20,
        )

        self.command_handler.queue_command(command)

        pending = self.command_handler.get_pending_commands("test-client")
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["command_type"], "list_files")

        # Should be empty after retrieval
        pending_again = self.command_handler.get_pending_commands("test-client")
        self.assertEqual(len(pending_again), 0)

    def test_store_response(self):
        """Test storing command responses."""
        # First queue a command
        command = CommandMessage(
            client_id="test-client",
            command_type=CommandType.SHELL_COMMAND,
            parameters={"command": "whoami"},
            timeout=15,
        )

        command_id = self.command_handler.queue_command(command)

        # Mark as dispatched
        self.command_handler.mark_command_dispatched(command_id)

        # Create response
        response = ResponseMessage(
            client_id="test-client",
            command_id=command_id,
            success=True,
            data={"stdout": "testuser", "stderr": "", "exit_code": 0},
            execution_time=0.5,
        )

        # Store response
        self.command_handler.store_response(response)

        # Check status
        record = self.command_handler.command_history[command_id]
        self.assertEqual(record.status, CommandStatus.COMPLETED)
        self.assertEqual(record.execution_time, 0.5)
        self.assertIsNotNone(record.response_data)

    def test_command_statistics(self):
        """Test command statistics generation."""
        # Queue some commands
        for i in range(3):
            command = CommandMessage(
                client_id=f"client-{i}",
                command_type=CommandType.BEACON,
                parameters={},
                timeout=10,
            )
            self.command_handler.queue_command(command)

        stats = self.command_handler.get_statistics()

        self.assertEqual(stats["total_commands"], 3)
        self.assertIn("status_breakdown", stats)
        self.assertEqual(stats["status_breakdown"]["queued"], 3)


class TestProtocolIntegration(unittest.TestCase):
    """Integration tests for protocol components."""

    def test_beacon_to_dict_conversion(self):
        """Test beacon message serialization."""
        beacon = BeaconMessage(
            client_id="integration-test",
            hostname="test-host",
            os_info="Linux Ubuntu 20.04",
            ip_address="10.0.0.1",
            process_id=9999,
            uptime=7200.0,
        )

        beacon_dict = beacon.to_dict()

        self.assertEqual(beacon_dict["client_id"], "integration-test")
        self.assertEqual(beacon_dict["hostname"], "test-host")
        self.assertEqual(beacon_dict["message_type"], "beacon")
        self.assertIn("timestamp", beacon_dict)

    def test_command_message_creation(self):
        """Test command message creation and conversion."""
        command = CommandMessage(
            client_id="test-client",
            command_type=CommandType.SIMULATE_EXFILTRATION,
            parameters={
                "files": ["/etc/passwd", "/etc/hosts"],
                "method": "http",
                "chunk_size": 1024,
            },
            timeout=60,
        )

        command_dict = command.to_dict()

        self.assertEqual(command_dict["client_id"], "test-client")
        self.assertEqual(command_dict["command_type"], "simulate_exfiltration")
        self.assertEqual(command_dict["timeout"], 60)
        self.assertIn("parameters", command_dict)

    def test_response_message_handling(self):
        """Test response message creation and handling."""
        response = ResponseMessage(
            client_id="test-client",
            command_id="cmd-12345",
            success=False,
            data={},
            error_message="Command execution failed",
            execution_time=2.5,
        )

        response_dict = response.to_dict()

        self.assertEqual(response_dict["client_id"], "test-client")
        self.assertEqual(response_dict["command_id"], "cmd-12345")
        self.assertFalse(response_dict["success"])
        self.assertEqual(response_dict["error_message"], "Command execution failed")


if __name__ == "__main__":
    unittest.main()

