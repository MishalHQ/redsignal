"""
Unit tests for RedSignal Protocol components.
"""

import unittest
import json
import time
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from redsignal.common.protocol import (
    BeaconMessage,
    CommandMessage,
    ResponseMessage,
    ProtocolHandler,
    MessageType,
    CommandType,
)


class TestProtocolMessages(unittest.TestCase):
    """Test cases for protocol message classes."""

    def test_beacon_message_creation(self):
        """Test BeaconMessage creation and serialization."""
        beacon = BeaconMessage(
            client_id="test-client",
            hostname="test-host",
            os_info="Linux Ubuntu 20.04",
            ip_address="192.168.1.100",
            process_id=1234,
            uptime=3600.0,
        )

        self.assertEqual(beacon.client_id, "test-client")
        self.assertEqual(beacon.hostname, "test-host")
        self.assertEqual(beacon.message_type, MessageType.BEACON)
        self.assertIsInstance(beacon.timestamp, float)

        # Test to_dict conversion
        beacon_dict = beacon.to_dict()
        self.assertEqual(beacon_dict["message_type"], "beacon")
        self.assertEqual(beacon_dict["client_id"], "test-client")
        self.assertIn("timestamp", beacon_dict)

    def test_command_message_creation(self):
        """Test CommandMessage creation and serialization."""
        command = CommandMessage(
            client_id="test-client",
            command_type=CommandType.LIST_FILES,
            parameters={"path": "/tmp", "recursive": False},
            timeout=30,
        )

        self.assertEqual(command.client_id, "test-client")
        self.assertEqual(command.command_type, CommandType.LIST_FILES)
        self.assertEqual(command.message_type, MessageType.COMMAND)
        self.assertEqual(command.timeout, 30)

        # Test to_dict conversion
        command_dict = command.to_dict()
        self.assertEqual(command_dict["message_type"], "command")
        self.assertEqual(command_dict["command_type"], "list_files")
        self.assertEqual(command_dict["parameters"]["path"], "/tmp")

    def test_response_message_creation(self):
        """Test ResponseMessage creation and serialization."""
        response = ResponseMessage(
            client_id="test-client",
            command_id="cmd-12345",
            success=True,
            data={"files": ["file1.txt", "file2.txt"], "count": 2},
            execution_time=1.5,
        )

        self.assertEqual(response.client_id, "test-client")
        self.assertEqual(response.command_id, "cmd-12345")
        self.assertTrue(response.success)
        self.assertEqual(response.execution_time, 1.5)

        # Test to_dict conversion
        response_dict = response.to_dict()
        self.assertEqual(response_dict["message_type"], "response")
        self.assertTrue(response_dict["success"])
        self.assertEqual(response_dict["data"]["count"], 2)

    def test_error_response_message(self):
        """Test ResponseMessage with error."""
        response = ResponseMessage(
            client_id="test-client",
            command_id="cmd-67890",
            success=False,
            data={},
            error_message="Command execution failed",
            execution_time=0.1,
        )

        self.assertFalse(response.success)
        self.assertEqual(response.error_message, "Command execution failed")

        response_dict = response.to_dict()
        self.assertFalse(response_dict["success"])
        self.assertEqual(response_dict["error_message"], "Command execution failed")


class TestProtocolHandler(unittest.TestCase):
    """Test cases for ProtocolHandler."""

    def setUp(self):
        self.handler = ProtocolHandler()

    def test_serialize_beacon(self):
        """Test beacon message serialization."""
        beacon = BeaconMessage(
            client_id="serialize-test",
            hostname="test-host",
            os_info="Windows 10",
            ip_address="10.0.0.1",
            process_id=5678,
            uptime=1800.0,
        )

        serialized = self.handler.serialize(beacon)
        self.assertIsInstance(serialized, str)

        # Should be valid JSON
        parsed = json.loads(serialized)
        self.assertEqual(parsed["client_id"], "serialize-test")
        self.assertEqual(parsed["message_type"], "beacon")

    def test_serialize_command(self):
        """Test command message serialization."""
        command = CommandMessage(
            client_id="serialize-test",
            command_type=CommandType.SHELL_COMMAND,
            parameters={"command": "whoami", "timeout": 10},
            timeout=15,
        )

        serialized = self.handler.serialize(command)
        parsed = json.loads(serialized)

        self.assertEqual(parsed["command_type"], "shell_command")
        self.assertEqual(parsed["parameters"]["command"], "whoami")

    def test_deserialize_beacon(self):
        """Test beacon message deserialization."""
        beacon_data = {
            "message_type": "beacon",
            "client_id": "deserialize-test",
            "hostname": "test-host",
            "os_info": "Linux",
            "ip_address": "172.16.0.1",
            "process_id": 9999,
            "uptime": 7200.0,
            "timestamp": time.time(),
        }

        serialized = json.dumps(beacon_data)
        deserialized = self.handler.deserialize(serialized)

        self.assertIsInstance(deserialized, BeaconMessage)
        self.assertEqual(deserialized.client_id, "deserialize-test")
        self.assertEqual(deserialized.hostname, "test-host")

    def test_deserialize_command(self):
        """Test command message deserialization."""
        command_data = {
            "message_type": "command",
            "client_id": "deserialize-test",
            "command_type": "collect_system_info",
            "parameters": {"type": "comprehensive"},
            "timeout": 45,
            "timestamp": time.time(),
            "message_id": "cmd-test-123",
        }

        serialized = json.dumps(command_data)
        deserialized = self.handler.deserialize(serialized)

        self.assertIsInstance(deserialized, CommandMessage)
        self.assertEqual(deserialized.command_type, CommandType.COLLECT_SYSTEM_INFO)
        self.assertEqual(deserialized.parameters["type"], "comprehensive")

    def test_deserialize_response(self):
        """Test response message deserialization."""
        response_data = {
            "message_type": "response",
            "client_id": "deserialize-test",
            "command_id": "cmd-response-test",
            "success": True,
            "data": {"result": "success", "value": 42},
            "execution_time": 2.3,
            "timestamp": time.time(),
            "message_id": "resp-test-456",
        }

        serialized = json.dumps(response_data)
        deserialized = self.handler.deserialize(serialized)

        self.assertIsInstance(deserialized, ResponseMessage)
        self.assertTrue(deserialized.success)
        self.assertEqual(deserialized.data["value"], 42)
        self.assertEqual(deserialized.execution_time, 2.3)

    def test_invalid_message_type(self):
        """Test handling of invalid message types."""
        invalid_data = {
            "message_type": "invalid_type",
            "client_id": "test",
        }

        serialized = json.dumps(invalid_data)

        with self.assertRaises(ValueError):
            self.handler.deserialize(serialized)

    def test_malformed_json(self):
        """Test handling of malformed JSON."""
        malformed_json = '{"message_type": "beacon", "client_id": "test"'  # Missing closing brace

        with self.assertRaises(json.JSONDecodeError):
            self.handler.deserialize(malformed_json)

    def test_round_trip_serialization(self):
        """Test complete serialization/deserialization round trip."""
        original_beacon = BeaconMessage(
            client_id="round-trip-test",
            hostname="round-trip-host",
            os_info="macOS Big Sur",
            ip_address="192.168.0.50",
            process_id=8888,
            uptime=14400.0,
        )

        # Serialize
        serialized = self.handler.serialize(original_beacon)

        # Deserialize
        deserialized = self.handler.deserialize(serialized)

        # Compare
        self.assertEqual(original_beacon.client_id, deserialized.client_id)
        self.assertEqual(original_beacon.hostname, deserialized.hostname)
        self.assertEqual(original_beacon.os_info, deserialized.os_info)
        self.assertEqual(original_beacon.ip_address, deserialized.ip_address)
        self.assertEqual(original_beacon.process_id, deserialized.process_id)


class TestCommandTypes(unittest.TestCase):
    """Test cases for CommandType enum."""

    def test_command_type_values(self):
        """Test CommandType enum values."""
        expected_commands = [
            "collect_system_info",
            "list_files",
            "shell_command",
            "simulate_exfiltration",
            "persistence_check",
            "beacon",
        ]

        for expected in expected_commands:
            # Should be able to create CommandType from string
            cmd_type = CommandType(expected)
            self.assertEqual(cmd_type.value, expected)

    def test_invalid_command_type(self):
        """Test invalid command type handling."""
        with self.assertRaises(ValueError):
            CommandType("invalid_command_type")


if __name__ == "__main__":
    unittest.main()

