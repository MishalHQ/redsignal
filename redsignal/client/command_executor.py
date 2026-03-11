"""
Command execution engine for RedSignal client.
Handles safe execution of commands received from the C2 server.
"""

import os
import time
import random
import hashlib
import subprocess
import platform
import psutil
from pathlib import Path
from typing import Dict, Any, List, Optional
import socket
import json

from ..common.protocol import CommandType
from ..common.logger import get_logger

logger = get_logger(__name__)


class CommandExecutor:
    """Executes commands safely with built-in restrictions."""

    def __init__(self, client_id: str):
        self.client_id = client_id
        self.restricted_paths = [
            "/etc/shadow",
            "/etc/passwd",
            "/root",
            "/boot",
            "C:\\Windows\\System32",
            "C:\\Users\\Administrator",
            "C:\\Windows\\Boot",
            "/sys",
            "/proc/kcore",
        ]
        self.dangerous_commands = [
            "rm -rf",
            "del /f",
            "format",
            "fdisk",
            "mkfs",
            "dd if=",
            "shutdown",
            "reboot",
            "halt",
            "poweroff",
            "sudo rm",
            "sudo dd",
            "chmod 777",
            "chown root",
        ]

    def execute_command(
        self, command_type: CommandType, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a command based on its type."""
        start_time = time.time()

        try:
            logger.info(f"Executing command: {command_type.value}")

            # Route to appropriate handler
            if command_type == CommandType.COLLECT_SYSTEM_INFO:
                result = self._collect_system_info(parameters)
            elif command_type == CommandType.LIST_FILES:
                result = self._list_files(parameters)
            elif command_type == CommandType.SHELL_COMMAND:
                result = self._execute_shell_command(parameters)
            elif command_type == CommandType.SIMULATE_EXFILTRATION:
                result = self._simulate_exfiltration(parameters)
            elif command_type == CommandType.PERSISTENCE_CHECK:
                result = self._check_persistence(parameters)
            elif command_type == CommandType.BEACON:
                result = self._beacon_response(parameters)
            else:
                raise ValueError(f"Unknown command type: {command_type}")

            execution_time = time.time() - start_time
            result["execution_time"] = execution_time

            logger.info(f"Command completed in {execution_time:.2f}s")
            return result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Command execution failed: {e}")
            return {
                "error": str(e),
                "execution_time": execution_time,
                "command_type": command_type.value,
            }

    def _collect_system_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Collect comprehensive system information."""
        info_type = params.get("type", "basic")

        # Basic system information
        basic_info = {
            "hostname": platform.node(),
            "platform": platform.platform(),
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "username": os.getenv("USER") or os.getenv("USERNAME", "unknown"),
            "home_directory": os.path.expanduser("~"),
            "current_directory": os.getcwd(),
            "python_version": platform.python_version(),
            "ip_addresses": self._get_ip_addresses(),
        }

        result = {"basic_info": basic_info}

        if info_type in ["comprehensive", "detailed"]:
            # Extended system information
            try:
                result["system_metrics"] = {
                    "cpu_count": psutil.cpu_count(),
                    "cpu_percent": psutil.cpu_percent(interval=1),
                    "memory_total": psutil.virtual_memory().total,
                    "memory_available": psutil.virtual_memory().available,
                    "memory_percent": psutil.virtual_memory().percent,
                    "disk_usage": self._get_disk_usage(),
                    "boot_time": psutil.boot_time(),
                    "uptime": time.time() - psutil.boot_time(),
                }

                result["network_info"] = {
                    "network_interfaces": self._get_network_interfaces(),
                    "network_connections": len(psutil.net_connections()),
                    "network_stats": dict(psutil.net_io_counters()._asdict()),
                }

                result["process_info"] = {
                    "process_count": len(psutil.pids()),
                    "current_process": {
                        "pid": os.getpid(),
                        "ppid": os.getppid(),
                        "name": psutil.Process().name(),
                        "cmdline": psutil.Process().cmdline(),
                    },
                }

            except Exception as e:
                result["extended_info_error"] = str(e)

        return result

    def _list_files(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List files in a directory safely."""
        target_path = params.get("path", ".")
        max_files = params.get("max_files", 100)
        recursive = params.get("recursive", False)

        try:
            path_obj = Path(target_path).resolve()

            # Security check
            if not self._is_safe_path(path_obj):
                return {
                    "error": f"Access to path {target_path} is restricted for security reasons",
                    "path": str(path_obj),
                }

            if not path_obj.exists():
                return {"error": f"Path does not exist: {target_path}"}

            if not path_obj.is_dir():
                # If it's a file, return file info
                return {
                    "file_info": self._get_file_info(path_obj),
                    "is_file": True,
                }

            files = []
            directories = []
            total_size = 0

            try:
                if recursive:
                    items = path_obj.rglob("*")
                else:
                    items = path_obj.iterdir()

                for item in items:
                    if len(files) + len(directories) >= max_files:
                        break

                    try:
                        file_info = self._get_file_info(item)

                        if item.is_file():
                            files.append(file_info)
                            total_size += file_info.get("size", 0)
                        elif item.is_dir():
                            directories.append(file_info)

                    except (PermissionError, OSError):
                        # Skip files we can't access
                        continue

                return {
                    "path": str(path_obj),
                    "files": files,
                    "directories": directories,
                    "file_count": len(files),
                    "directory_count": len(directories),
                    "total_size": total_size,
                    "recursive": recursive,
                    "truncated": len(files) + len(directories) >= max_files,
                }

            except PermissionError:
                return {"error": f"Permission denied accessing: {target_path}"}

        except Exception as e:
            return {"error": f"Failed to list files: {str(e)}"}

    def _execute_shell_command(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute shell command with safety restrictions."""
        command = params.get("command", "")
        timeout = params.get("timeout", 10)

        if not command:
            return {"error": "No command specified"}

        # Security check - block dangerous commands
        command_lower = command.lower()
        for dangerous in self.dangerous_commands:
            if dangerous in command_lower:
                return {
                    "error": f'Command blocked for security: contains "{dangerous}"',
                    "command": command,
                    "blocked": True,
                }

        # For safety, simulate command execution instead of real execution
        # In a real scenario, you might want controlled execution
        return self._simulate_shell_command(command, timeout)

    def _simulate_shell_command(self, command: str, timeout: int) -> Dict[str, Any]:
        """Simulate shell command execution for safety."""
        # Simulate different command outputs
        simulated_outputs = {
            "whoami": os.getenv("USER") or os.getenv("USERNAME", "testuser"),
            "hostname": platform.node(),
            "pwd": os.getcwd(),
            "date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "uptime": f"up {int((time.time() - psutil.boot_time()) / 3600)} hours",
            "id": "uid=1000(testuser) gid=1000(testuser) groups=1000(testuser)",
            "uname -a": platform.platform(),
            "ps aux": "Simulated process list (truncated for safety)",
            "netstat -an": "Simulated network connections (truncated for safety)",
            "ls": "file1.txt  file2.txt  directory1  directory2",
            "dir": "file1.txt  file2.txt  directory1  directory2",
        }

        # Check for exact matches first
        for sim_cmd, output in simulated_outputs.items():
            if command.strip().lower() == sim_cmd:
                return {
                    "command": command,
                    "stdout": output,
                    "stderr": "",
                    "exit_code": 0,
                    "execution_time": random.uniform(0.1, 0.5),
                    "note": "SIMULATION ONLY - Command was not actually executed",
                }

        # Generic simulation for other commands
        return {
            "command": command,
            "stdout": f"Simulated output for: {command}",
            "stderr": "",
            "exit_code": 0,
            "execution_time": random.uniform(0.1, 1.0),
            "note": "SIMULATION ONLY - Command was not actually executed",
        }

    def _simulate_exfiltration(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate data exfiltration for training purposes."""
        files = params.get("files", [])
        method = params.get("method", "http")
        chunk_size = params.get("chunk_size", 1024)
        destination = params.get("destination", "http://attacker-server.com/upload")

        if not files:
            return {"error": "No files specified for exfiltration"}

        processed_files = []
        total_size = 0

        for file_path in files:
            try:
                path_obj = Path(file_path)

                # Security check
                if not self._is_safe_path(path_obj):
                    processed_files.append(
                        {
                            "file": file_path,
                            "status": "blocked",
                            "reason": "Path restricted for security",
                        }
                    )
                    continue

                # Simulate file processing
                if path_obj.exists() and path_obj.is_file():
                    file_size = path_obj.stat().st_size
                    total_size += file_size

                    # Simulate upload process
                    chunks = (file_size // chunk_size) + 1
                    upload_time = chunks * 0.1  # Simulate network delay

                    processed_files.append(
                        {
                            "file": file_path,
                            "size": file_size,
                            "chunks": chunks,
                            "upload_time": upload_time,
                            "status": "simulated_success",
                            "method": method,
                            "destination": destination,
                        }
                    )
                else:
                    processed_files.append(
                        {
                            "file": file_path,
                            "status": "not_found",
                            "reason": "File does not exist or is not a file",
                        }
                    )

            except Exception as e:
                processed_files.append(
                    {
                        "file": file_path,
                        "status": "error",
                        "reason": str(e),
                    }
                )

        return {
            "method": method,
            "destination": destination,
            "chunk_size": chunk_size,
            "processed_files": len(processed_files),
            "successful_files": len(
                [f for f in processed_files if f["status"] == "simulated_success"]
            ),
            "total_size": total_size,
            "files": processed_files,
            "note": "SIMULATION ONLY - No actual data was exfiltrated",
        }

    def _upload_file_simulation(
        self, file_path: str, destination: str, chunk_size: int
    ) -> Dict[str, Any]:
        """Simulate file upload process."""
        try:
            path_obj = Path(file_path)

            if not path_obj.exists():
                return {"error": "File does not exist", "file": file_path}

            file_size = path_obj.stat().st_size
            file_name = path_obj.name

            # Simulate upload timing
            chunks = (file_size // chunk_size) + 1
            upload_time = chunks * random.uniform(0.05, 0.2)

            # Generate fake hash for simulation
            fake_hash = hashlib.md5(f"{file_path}{time.time()}".encode()).hexdigest()

            return {
                "file_name": file_name,
                "file_size": file_size,
                "destination": destination,
                "upload_time": upload_time,
                "file_hash": fake_hash,
                "status": "simulated_upload_complete",
                "note": "SIMULATION ONLY - No actual file was uploaded",
            }

        except Exception as e:
            return {"error": str(e), "file": file_path}

    def _check_persistence(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Check for persistence mechanisms (simulated)."""
        check_type = params.get("type", "all")

        # Simulate checking various persistence methods
        persistence_checks = {
            "startup_folders": self._check_startup_folders(),
            "registry_keys": self._check_registry_keys(),
            "scheduled_tasks": self._check_scheduled_tasks(),
            "services": self._check_services(),
            "cron_jobs": self._check_cron_jobs(),
        }

        if check_type != "all" and check_type in persistence_checks:
            return {check_type: persistence_checks[check_type]}

        return {
            "persistence_check_type": check_type,
            "results": persistence_checks,
            "note": "SIMULATION ONLY - No actual persistence mechanisms checked",
        }

    def _beacon_response(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate beacon response data."""
        return {
            "client_id": self.client_id,
            "timestamp": time.time(),
            "uptime": time.time() - psutil.boot_time(),
            "status": "active",
            "message": "Beacon response generated",
        }

    def _is_safe_path(self, path_obj) -> bool:
        """Check if path is safe to access."""
        try:
            # Convert to absolute path
            abs_path = path_obj.resolve()

            # Define restricted paths
            restricted_paths = [
                "/etc/shadow",
                "/etc/passwd",
                "/root",
                "C:\\Windows\\System32",
                "C:\\Users\\Administrator",
            ]

            # Check against restricted paths
            for restricted in restricted_paths:
                if str(abs_path).startswith(restricted):
                    return False

            return True

        except Exception:
            return False

    def _get_file_info(self, file_path) -> Dict[str, Any]:
        """Get safe file information."""
        try:
            stat = file_path.stat()
            return {
                "name": file_path.name,
                "path": str(file_path),
                "size": stat.st_size,
                "is_file": file_path.is_file(),
                "is_dir": file_path.is_dir(),
                "modified_time": stat.st_mtime,
                "permissions": (
                    oct(stat.st_mode)[-3:] if hasattr(stat, "st_mode") else "unknown"
                ),
            }
        except Exception as e:
            return {
                "name": file_path.name if hasattr(file_path, "name") else str(file_path),
                "error": str(e),
            }

    def _get_ip_addresses(self) -> List[str]:
        """Get system IP addresses."""
        ip_addresses = []
        try:
            # Get network interfaces
            for interface, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.family == socket.AF_INET:  # IPv4
                        ip_addresses.append(addr.address)
        except Exception as e:
            logger.warning(f"Failed to get IP addresses: {e}")
            # Fallback method
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.connect(("8.8.8.8", 80))
                    ip_addresses.append(s.getsockname()[0])
            except Exception:
                ip_addresses.append("127.0.0.1")

        return ip_addresses

    def _get_disk_usage(self) -> Dict[str, Any]:
        """Get disk usage information."""
        try:
            disk_usage = psutil.disk_usage("/")
            return {
                "total": disk_usage.total,
                "used": disk_usage.used,
                "free": disk_usage.free,
                "percent": (disk_usage.used / disk_usage.total) * 100,
            }
        except Exception:
            # Fallback for Windows
            try:
                disk_usage = psutil.disk_usage("C:\\")
                return {
                    "total": disk_usage.total,
                    "used": disk_usage.used,
                    "free": disk_usage.free,
                    "percent": (disk_usage.used / disk_usage.total) * 100,
                }
            except Exception as e:
                return {"error": str(e)}

    def _get_network_interfaces(self) -> Dict[str, List[str]]:
        """Get network interface information."""
        interfaces = {}
        try:
            for interface, addrs in psutil.net_if_addrs().items():
                interface_addrs = []
                for addr in addrs:
                    if addr.family == socket.AF_INET:  # IPv4
                        interface_addrs.append(addr.address)
                    elif addr.family == socket.AF_INET6:  # IPv6
                        interface_addrs.append(addr.address)

                if interface_addrs:
                    interfaces[interface] = interface_addrs
        except Exception as e:
            interfaces["error"] = str(e)

        return interfaces

    def _check_startup_folders(self) -> Dict[str, Any]:
        """Simulate checking startup folders."""
        import platform

        if platform.system() == "Windows":
            folders = [
                "C:\\Users\\{user}\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup",
                "C:\\ProgramData\\Microsoft\\Windows\\Start Menu\\Programs\\Startup",
            ]
        else:
            folders = [
                "~/.config/autostart",
                "/etc/init.d",
                "~/.bashrc",
                "~/.profile",
            ]

        return {
            "checked_locations": folders,
            "suspicious_files": [],  # Would contain actual findings
            "status": "simulated_check_complete",
        }

    def _check_registry_keys(self) -> Dict[str, Any]:
        """Simulate checking Windows registry keys."""
        registry_keys = [
            "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run",
            "HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\Run",
            "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce",
        ]

        return {
            "checked_keys": registry_keys,
            "suspicious_entries": [],  # Would contain actual findings
            "status": "simulated_check_complete",
            "note": "Registry checks only available on Windows",
        }

    def _check_scheduled_tasks(self) -> Dict[str, Any]:
        """Simulate checking scheduled tasks."""
        return {
            "total_tasks": random.randint(50, 200),
            "suspicious_tasks": [],  # Would contain actual findings
            "status": "simulated_check_complete",
        }

    def _check_services(self) -> Dict[str, Any]:
        """Simulate checking system services."""
        return {
            "total_services": random.randint(100, 300),
            "running_services": random.randint(50, 150),
            "suspicious_services": [],  # Would contain actual findings
            "status": "simulated_check_complete",
        }

    def _check_cron_jobs(self) -> Dict[str, Any]:
        """Simulate checking cron jobs (Unix/Linux)."""
        return {
            "user_crontab": "simulated_check",
            "system_crontab": "simulated_check",
            "suspicious_jobs": [],  # Would contain actual findings
            "status": "simulated_check_complete",
            "note": "Cron checks only available on Unix/Linux systems",
        }

