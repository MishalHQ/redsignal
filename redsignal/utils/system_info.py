"""
System information collection utilities for RedSignal platform.
Safely gathers system data for emulation purposes.
"""

import platform
import psutil
import socket
import os
import getpass
from typing import Dict, Any, List
import subprocess
import json


class SystemInfoCollector:
    """Collects various system information safely."""

    def __init__(self):
        self.hostname = socket.gethostname()
        self.username = getpass.getuser()

    def get_basic_info(self) -> Dict[str, Any]:
        """Collect basic system information."""
        try:
            return {
                "hostname": self.hostname,
                "username": self.username,
                "platform": platform.platform(),
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "python_version": platform.python_version(),
                "ip_addresses": self._get_ip_addresses(),
                "mac_addresses": self._get_mac_addresses(),
            }
        except Exception as e:
            return {"error": f"Failed to collect basic info: {str(e)}"}

    def get_process_info(self) -> Dict[str, Any]:
        """Get current process and system process information."""
        try:
            current_process = psutil.Process()
            return {
                "current_pid": current_process.pid,
                "current_ppid": current_process.ppid(),
                "current_name": current_process.name(),
                "current_cmdline": current_process.cmdline(),
                "current_cwd": current_process.cwd(),
                "current_memory": current_process.memory_info()._asdict(),
                "current_cpu_percent": current_process.cpu_percent(),
                "process_count": len(psutil.pids()),
                "running_processes": self._get_running_processes(),
            }
        except Exception as e:
            return {"error": f"Failed to collect process info: {str(e)}"}

    def get_network_info(self) -> Dict[str, Any]:
        """Collect network configuration details."""
        try:
            return {
                "network_interfaces": self._get_network_interfaces(),
                "network_connections": self._get_network_connections(),
                "network_stats": psutil.net_io_counters()._asdict(),
            }
        except Exception as e:
            return {"error": f"Failed to collect network info: {str(e)}"}

    def get_disk_info(self) -> Dict[str, Any]:
        """Get disk usage and partition information."""
        try:
            partitions = []
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    partitions.append(
                        {
                            "device": partition.device,
                            "mountpoint": partition.mountpoint,
                            "fstype": partition.fstype,
                            "total": usage.total,
                            "used": usage.used,
                            "free": usage.free,
                            "percent": (usage.used / usage.total) * 100,
                        }
                    )
                except PermissionError:
                    # Skip inaccessible partitions
                    continue

            return {
                "partitions": partitions,
                "disk_io": psutil.disk_io_counters()._asdict()
                if psutil.disk_io_counters()
                else {},
            }
        except Exception as e:
            return {"error": f"Failed to collect disk info: {str(e)}"}

    def get_environment_info(self) -> Dict[str, Any]:
        """Collect environment variables and path information."""
        try:
            # Only collect non-sensitive environment variables
            safe_env_vars = {}
            sensitive_keys = ["password", "secret", "key", "token", "auth"]

            for key, value in os.environ.items():
                if not any(sensitive in key.lower() for sensitive in sensitive_keys):
                    safe_env_vars[key] = value

            return {
                "environment_variables": safe_env_vars,
                "current_directory": os.getcwd(),
                "home_directory": os.path.expanduser("~"),
                "temp_directory": os.path.tempdir or "/tmp",
                "path_separator": os.pathsep,
                "line_separator": os.linesep,
            }
        except Exception as e:
            return {"error": f"Failed to collect environment info: {str(e)}"}

    def _get_ip_addresses(self) -> List[str]:
        """Get all IP addresses for the system."""
        ip_addresses = []
        try:
            for interface, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.family == socket.AF_INET:
                        ip_addresses.append(addr.address)
        except Exception:
            pass
        return ip_addresses

    def _get_mac_addresses(self) -> List[str]:
        """Get MAC addresses for network interfaces."""
        mac_addresses = []
        try:
            for interface, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.family == psutil.AF_LINK:
                        mac_addresses.append(addr.address)
        except Exception:
            pass
        return mac_addresses

    def _get_running_processes(self) -> List[Dict[str, Any]]:
        """Get list of running processes (limited for performance)."""
        processes = []
        try:
            for proc in psutil.process_iter(["pid", "name", "username"]):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                # Limit to first 50 processes for performance
                if len(processes) >= 50:
                    break
        except Exception:
            pass
        return processes

    def _get_network_interfaces(self) -> Dict[str, Any]:
        """Get network interface information."""
        interfaces = {}
        try:
            for interface, addrs in psutil.net_if_addrs().items():
                interface_info = []
                for addr in addrs:
                    interface_info.append(
                        {
                            "family": str(addr.family),
                            "address": addr.address,
                            "netmask": addr.netmask,
                            "broadcast": addr.broadcast,
                        }
                    )
                interfaces[interface] = interface_info
        except Exception:
            pass
        return interfaces

    def _get_network_connections(self) -> List[Dict[str, Any]]:
        """Get active network connections (limited)."""
        connections = []
        try:
            for conn in psutil.net_connections(kind="inet")[:20]:  # Limit to 20
                connections.append(
                    {
                        "fd": conn.fd,
                        "family": str(conn.family),
                        "type": str(conn.type),
                        "local_address": f"{conn.laddr.ip}:{conn.laddr.port}"
                        if conn.laddr
                        else None,
                        "remote_address": f"{conn.raddr.ip}:{conn.raddr.port}"
                        if conn.raddr
                        else None,
                        "status": conn.status,
                        "pid": conn.pid,
                    }
                )
        except Exception:
            pass
        return connections


def collect_comprehensive_info() -> Dict[str, Any]:
    """Collect all available system information."""
    collector = SystemInfoCollector()

    return {
        "basic_info": collector.get_basic_info(),
        "process_info": collector.get_process_info(),
        "network_info": collector.get_network_info(),
        "disk_info": collector.get_disk_info(),
        "environment_info": collector.get_environment_info(),
        "collection_timestamp": psutil.boot_time(),
    }

