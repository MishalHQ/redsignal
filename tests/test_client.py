"""
Unit tests for RedSignal Client components.
"""

import unittest
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from redsignal.client.command_executor import CommandExecutor
from redsignal.client.beacon import BeaconManager
from redsignal.common.protocol import CommandType


class TestCommandExecutor(unittest.TestCase):
    """Test cases for CommandExecutor."""

    def setUp(self):
        self.executor = CommandExecutor("test-client-id")

    def test_system_info_collection(self):
        """Test system information collection."""
        result = self.executor.execute_command(
            CommandType.COLLECT_SYSTEM_INFO, {"type": "basic"}
        )

        self.assertIn("basic_info", result)
        self.assertIn("hostname", result["basic_info"])
        self.assertIn("platform", result["basic_info"])
        self.assertIn("username", result["basic_info"])

    def test_file_listing_safe_path(self):
        """Test file listing with safe paths."""
        # Create a temporary directory with some files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("test content")

            result = self.executor.execute_command(
                CommandType.LIST_FILES, {"path": temp_dir, "max_files": 10}
            )

            self.assertIn("files", result)
            self.assertGreater(len(result["files"]), 0)
            self.assertEqual(result["file_count"], 1)

    def test_file_listing_restricted_path(self):
        """Test file listing with restricted paths."""
        result = self.executor.execute_command(
            CommandType.LIST_FILES, {"path": "/etc/shadow"}  # Restricted path
        )

        self.assertIn("error", result)
        self.assertIn("restricted", result["error"].lower())

    def test_shell_command_safe(self):
        """Test safe shell command execution."""
        result = self.executor.execute_command(
            CommandType.SHELL_COMMAND,
            {"command": "echo 'hello world'", "timeout": 5},
        )

        # Should be simulated, not actually executed
        self.assertIn("simulated", result.get("note", "").lower())
        self.assertIn("stdout", result)

    def test_shell_command_dangerous(self):
        """Test dangerous shell command blocking."""
        dangerous_commands = [
            "rm -rf /",
            "del C:\\Windows\\System32",
            "format C:",
            "sudo rm -rf /*",
        ]

        for cmd in dangerous_commands:
            result = self.executor.execute_command(
                CommandType.SHELL_COMMAND, {"command": cmd}
            )

            self.assertIn("error", result)
            self.assertIn("blocked", result["error"].lower())

    def test_exfiltration_simulation(self):
        """Test data exfiltration simulation."""
        result = self.executor.execute_command(
            CommandType.SIMULATE_EXFILTRATION,
            {
                "files": ["test1.txt", "test2.txt"],
                "method": "http",
                "chunk_size": 1024,
            },
        )

        self.assertIn("processed_files", result)
        self.assertIn("total_size", result)
        self.assertIn("SIMULATION", result.get("note", ""))

    def test_persistence_check(self):
        """Test persistence mechanism checking."""
        result = self.executor.execute_command(
            CommandType.PERSISTENCE_CHECK, {"type": "all"}
        )

        self.assertIn("results", result)
        self.assertIn("startup_folders", result["results"])
        self.assertIn("registry_keys", result["results"])
        self.assertIn("SIMULATION", result.get("note", ""))

    def test_invalid_command_type(self):
        """Test handling of invalid command types."""
        # This should raise an exception or return an error
        with self.assertRaises((ValueError, KeyError)):
            self.executor.execute_command("INVALID_COMMAND", {})


class TestBeaconManager(unittest.TestCase):
    """Test cases for BeaconManager."""

    def setUp(self):
        self.beacon_manager = BeaconManager("test-beacon-client")

    def test_beacon_creation(self):
        """Test beacon message creation."""
        beacon = self.beacon_manager.create_beacon()

        self.assertEqual(beacon.client_id, "test-beacon-client")
        self.assertEqual(beacon.hostname, self.beacon_manager.hostname)
        self.assertIsNotNone(beacon.ip_address)
        self.assertGreater(beacon.uptime, 0)

    def test_extended_status(self):
        """Test extended status collection."""
        status = self.beacon_manager.get_extended_status()

        # Should contain system metrics
        expected_keys = ["cpu_percent", "memory_percent", "disk_usage"]
        for key in expected_keys:
            self.assertIn(key, status)

    @patch("socket.socket")
    def test_ip_address_detection(self, mock_socket):
        """Test IP address detection with mocked socket."""
        # Mock socket behavior
        mock_sock = MagicMock()
        mock_sock.getsockname.return_value = ("192.168.1.100", 12345)
        mock_socket.return_value.__enter__.return_value = mock_sock

        ip = self.beacon_manager._get_primary_ip()
        self.assertEqual(ip, "192.168.1.100")


class TestClientIntegration(unittest.TestCase):
    """Integration tests for client components."""

    def setUp(self):
        self.client_id = "integration-test-client"
        self.executor = CommandExecutor(self.client_id)
        self.beacon_manager = BeaconManager(self.client_id)

    def test_beacon_and_command_flow(self):
        """Test the flow from beacon to command execution."""
        # Create beacon
        beacon = self.beacon_manager.create_beacon()
        self.assertIsNotNone(beacon)

        # Execute a command
        result = self.executor.execute_command(
            CommandType.COLLECT_SYSTEM_INFO, {"type": "basic"}
        )

        self.assertNotIn("error", result)
        self.assertIn("basic_info", result)

    def test_multiple_command_execution(self):
        """Test executing multiple commands in sequence."""
        commands = [
            (CommandType.COLLECT_SYSTEM_INFO, {"type": "basic"}),
            (CommandType.LIST_FILES, {"path": ".", "max_files": 5}),
            (CommandType.BEACON, {}),
        ]

        results = []
        for cmd_type, params in commands:
            result = self.executor.execute_command(cmd_type, params)
            results.append(result)
            self.assertNotIn("error", result, f"Command {cmd_type} failed")

        self.assertEqual(len(results), 3)

    def test_error_handling(self):
        """Test error handling in command execution."""
        # Test with invalid parameters
        result = self.executor.execute_command(
            CommandType.LIST_FILES, {"path": "/nonexistent/path/12345"}
        )

        # Should handle gracefully
        self.assertTrue(
            "error" in result or "files" in result,
            "Should either return error or empty file list",
        )


if __name__ == "__main__":
    unittest.main()

