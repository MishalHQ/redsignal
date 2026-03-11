"""
Command handling and dispatch system for RedSignal C2 server.
Manages command queuing, execution tracking, and response collection.
"""

import time
import uuid
from typing import Dict, Any, List, Optional, Deque
from collections import deque
from dataclasses import dataclass, asdict
from enum import Enum

from ..common.protocol import CommandMessage, ResponseMessage, CommandType
from ..common.logger import get_logger

logger = get_logger(__name__)


class CommandStatus(Enum):
    """Status of a command in the system."""

    QUEUED = "queued"
    DISPATCHED = "dispatched"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class CommandRecord:
    """Record of a command and its execution status."""

    command_id: str
    client_id: str
    command_type: str
    parameters: Dict[str, Any]
    status: CommandStatus
    created_time: float
    dispatched_time: Optional[float] = None
    completed_time: Optional[float] = None
    timeout: int = 30
    response_data: Optional[Any] = None
    error_message: Optional[str] = None
    execution_time: Optional[float] = None


class CommandHandler:
    """Handles command queuing, dispatch, and response tracking."""

    def __init__(self):
        self.command_queue: Dict[str, Deque[CommandMessage]] = {}  # client_id -> commands
        self.command_history: Dict[str, CommandRecord] = {}  # command_id -> record
        self.max_history = 1000  # Maximum commands to keep in history

    def queue_command(self, command: CommandMessage) -> str:
        """Queue a command for a specific client."""
        try:
            client_id = command.client_id

            # Initialize queue for client if needed
            if client_id not in self.command_queue:
                self.command_queue[client_id] = deque()

            # Add to queue
            self.command_queue[client_id].append(command)

            # Create command record
            record = CommandRecord(
                command_id=command.message_id,
                client_id=client_id,
                command_type=command.command_type.value,
                parameters=command.parameters,
                status=CommandStatus.QUEUED,
                created_time=command.timestamp,
                timeout=command.timeout,
            )

            self.command_history[command.message_id] = record

            logger.info(
                f"Queued command {command.command_type.value} for client {client_id}"
            )
            return command.message_id

        except Exception as e:
            logger.error(f"Failed to queue command: {e}")
            raise

    def get_pending_commands(self, client_id: str) -> List[Dict[str, Any]]:
        """Get all pending commands for a client."""
        if client_id not in self.command_queue:
            return []

        commands = []
        queue = self.command_queue[client_id]

        while queue:
            command = queue.popleft()
            commands.append(command.to_dict())

        return commands

    def mark_command_dispatched(self, command_id: str):
        """Mark a command as dispatched to client."""
        if command_id in self.command_history:
            record = self.command_history[command_id]
            record.status = CommandStatus.DISPATCHED
            record.dispatched_time = time.time()
            logger.debug(f"Command {command_id} marked as dispatched")

    def store_response(self, response: ResponseMessage):
        """Store command response and update status."""
        try:
            command_id = response.command_id

            if command_id not in self.command_history:
                logger.warning(f"Received response for unknown command: {command_id}")
                return

            record = self.command_history[command_id]
            record.completed_time = response.timestamp
            record.response_data = response.data
            record.execution_time = response.execution_time

            if response.success:
                record.status = CommandStatus.COMPLETED
            else:
                record.status = CommandStatus.FAILED
                record.error_message = response.error_message

            logger.info(
                f"Stored response for command {command_id}: {record.status.value}"
            )

        except Exception as e:
            logger.error(f"Failed to store response: {e}")

    def get_command_status(self, command_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific command."""
        if command_id in self.command_history:
            record = self.command_history[command_id]
            return asdict(record)
        return None

    def get_recent_commands(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent commands sorted by creation time."""
        commands = list(self.command_history.values())
        commands.sort(key=lambda x: x.created_time, reverse=True)

        return [asdict(cmd) for cmd in commands[:limit]]

    def get_all_commands(self) -> List[Dict[str, Any]]:
        """Get all commands in history."""
        return [asdict(cmd) for cmd in self.command_history.values()]

    def get_client_commands(self, client_id: str) -> List[Dict[str, Any]]:
        """Get all commands for a specific client."""
        client_commands = [
            cmd for cmd in self.command_history.values() if cmd.client_id == client_id
        ]
        client_commands.sort(key=lambda x: x.created_time, reverse=True)

        return [asdict(cmd) for cmd in client_commands]

    def cleanup_old_commands(self):
        """Remove old commands to prevent memory bloat."""
        if len(self.command_history) <= self.max_history:
            return

        # Sort by creation time and keep only recent ones
        commands = list(self.command_history.values())
        commands.sort(key=lambda x: x.created_time, reverse=True)

        # Keep only the most recent commands
        to_keep = commands[: self.max_history]

        # Clear and rebuild history
        self.command_history.clear()
        for cmd in to_keep:
            self.command_history[cmd.command_id] = cmd

        logger.info(f"Cleaned up command history, kept {len(to_keep)} commands")

    def get_statistics(self) -> Dict[str, Any]:
        """Get command execution statistics."""
        total_commands = len(self.command_history)

        status_counts = {}
        for status in CommandStatus:
            status_counts[status.value] = len(
                [cmd for cmd in self.command_history.values() if cmd.status == status]
            )

        # Calculate average execution time for completed commands
        completed_commands = [
            cmd
            for cmd in self.command_history.values()
            if cmd.status == CommandStatus.COMPLETED and cmd.execution_time
        ]

        avg_execution_time = 0
        if completed_commands:
            avg_execution_time = sum(
                cmd.execution_time for cmd in completed_commands
            ) / len(completed_commands)

        return {
            "total_commands": total_commands,
            "status_breakdown": status_counts,
            "average_execution_time": avg_execution_time,
            "queued_by_client": {
                client_id: len(queue)
                for client_id, queue in self.command_queue.items()
            },
        }

