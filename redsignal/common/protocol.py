"""
Communication protocol definitions for RedSignal C2 platform.
Defines message structures and serialization methods.
"""

import json
import time
import uuid
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, List
from enum import Enum


class MessageType(Enum):
    """Enumeration of message types in the protocol."""

    BEACON = "beacon"
    COMMAND = "command"
    RESPONSE = "response"
    HEARTBEAT = "heartbeat"
    REGISTRATION = "registration"
    ERROR = "error"


class CommandType(Enum):
    """Available command types for client execution."""

    COLLECT_SYSTEM_INFO = "collect_system_info"
    LIST_FILES = "list_files"
    SIMULATE_EXFILTRATION = "simulate_exfiltration"
    BEACON = "beacon"
    SHELL_COMMAND = "shell_command"
    DOWNLOAD_FILE = "download_file"
    UPLOAD_FILE = "upload_file"
    PERSISTENCE_CHECK = "persistence_check"


@dataclass
class BaseMessage:
    """Base message structure for all communications."""

    message_id: str
    message_type: MessageType
    timestamp: float
    client_id: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for JSON serialization."""
        data = asdict(self)
        data["message_type"] = self.message_type.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create message instance from dictionary."""
        data["message_type"] = MessageType(data["message_type"])
        return cls(**data)


@dataclass
class BeaconMessage(BaseMessage):
    """Client beacon message with system status."""

    hostname: str
    os_info: str
    ip_address: str
    process_id: int
    uptime: float

    def __init__(
        self,
        client_id: str,
        hostname: str,
        os_info: str,
        ip_address: str,
        process_id: int,
        uptime: float,
    ):
        super().__init__(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.BEACON,
            timestamp=time.time(),
            client_id=client_id,
        )
        self.hostname = hostname
        self.os_info = os_info
        self.ip_address = ip_address
        self.process_id = process_id
        self.uptime = uptime


@dataclass
class CommandMessage(BaseMessage):
    """Server command message to client."""

    command_type: CommandType
    parameters: Dict[str, Any]
    timeout: int = 30

    def __init__(
        self,
        client_id: str,
        command_type: CommandType,
        parameters: Dict[str, Any],
        timeout: int = 30,
    ):
        super().__init__(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.COMMAND,
            timestamp=time.time(),
            client_id=client_id,
        )
        self.command_type = command_type
        self.parameters = parameters
        self.timeout = timeout

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["command_type"] = self.command_type.value
        return data


@dataclass
class ResponseMessage(BaseMessage):
    """Client response message to server."""

    command_id: str
    success: bool
    data: Any
    error_message: Optional[str] = None
    execution_time: float = 0.0

    def __init__(
        self,
        client_id: str,
        command_id: str,
        success: bool,
        data: Any,
        error_message: Optional[str] = None,
        execution_time: float = 0.0,
    ):
        super().__init__(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.RESPONSE,
            timestamp=time.time(),
            client_id=client_id,
        )
        self.command_id = command_id
        self.success = success
        self.data = data
        self.error_message = error_message
        self.execution_time = execution_time


class ProtocolHandler:
    """Handles message serialization and deserialization."""

    @staticmethod
    def serialize(message: BaseMessage) -> str:
        """Serialize message to JSON string."""
        try:
            return json.dumps(message.to_dict(), default=str)
        except Exception as e:
            raise ValueError(f"Failed to serialize message: {e}")

    @staticmethod
    def deserialize(data: str) -> BaseMessage:
        """Deserialize JSON string to message object."""
        try:
            msg_dict = json.loads(data)
            msg_type = MessageType(msg_dict["message_type"])

            if msg_type == MessageType.BEACON:
                return BeaconMessage.from_dict(msg_dict)
            elif msg_type == MessageType.COMMAND:
                msg_dict["command_type"] = CommandType(msg_dict["command_type"])
                return CommandMessage.from_dict(msg_dict)
            elif msg_type == MessageType.RESPONSE:
                return ResponseMessage.from_dict(msg_dict)
            else:
                return BaseMessage.from_dict(msg_dict)

        except Exception as e:
            raise ValueError(f"Failed to deserialize message: {e}")

