"""
File utilities for RedSignal platform.
Provides safe file operations and analysis capabilities.
"""

import os
import hashlib
import mimetypes
from pathlib import Path
from typing import Dict, Any, List, Optional, Iterator
import zipfile
import tarfile

from ..common.logger import get_logger

logger = get_logger(__name__)


class SafeFileHandler:
    """Handles file operations safely for security testing."""

    def __init__(self):
        self.max_file_size = 100 * 1024 * 1024  # 100MB limit
        self.allowed_extensions = {
            ".txt",
            ".log",
            ".json",
            ".xml",
            ".csv",
            ".py",
            ".js",
            ".html",
            ".css",
            ".md",
            ".yml",
            ".yaml",
            ".ini",
            ".conf",
            ".cfg",
        }

    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze a file safely and return metadata."""
        try:
            path_obj = Path(file_path)

            if not path_obj.exists():
                return {"error": "File does not exist"}

            if not path_obj.is_file():
                return {"error": "Path is not a file"}

            # Get basic file info
            stat_info = path_obj.stat()

            # Check file size
            if stat_info.st_size > self.max_file_size:
                return {"error": f"File too large: {stat_info.st_size} bytes"}

            # Calculate file hashes
            hashes = self._calculate_hashes(path_obj)

            # Get MIME type
            mime_type, encoding = mimetypes.guess_type(str(path_obj))

            # Analyze file content (if safe)
            content_analysis = {}
            if path_obj.suffix.lower() in self.allowed_extensions:
                content_analysis = self._analyze_content(path_obj)

            return {
                "file_path": str(path_obj),
                "file_name": path_obj.name,
                "file_size": stat_info.st_size,
                "file_extension": path_obj.suffix,
                "mime_type": mime_type,
                "encoding": encoding,
                "created_time": stat_info.st_ctime,
                "modified_time": stat_info.st_mtime,
                "accessed_time": stat_info.st_atime,
                "permissions": oct(stat_info.st_mode)[-3:],
                "hashes": hashes,
                "content_analysis": content_analysis,
            }

        except Exception as e:
            logger.error(f"File analysis failed: {e}")
            return {"error": f"Analysis failed: {str(e)}"}

    def _calculate_hashes(self, file_path: Path) -> Dict[str, str]:
        """Calculate multiple hashes for a file."""
        hashes = {}

        try:
            with open(file_path, "rb") as f:
                content = f.read()

                hashes["md5"] = hashlib.md5(content).hexdigest()
                hashes["sha1"] = hashlib.sha1(content).hexdigest()
                hashes["sha256"] = hashlib.sha256(content).hexdigest()

        except Exception as e:
            logger.warning(f"Hash calculation failed: {e}")
            hashes["error"] = str(e)

        return hashes

    def _analyze_content(self, file_path: Path) -> Dict[str, Any]:
        """Analyze file content safely."""
        analysis = {}

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(10000)  # Read first 10KB only

                analysis["line_count"] = content.count("\n")
                analysis["char_count"] = len(content)
                analysis["word_count"] = len(content.split())

                # Look for interesting patterns
                analysis["contains_urls"] = "http" in content.lower()
                analysis["contains_emails"] = "@" in content and "." in content
                analysis["contains_ips"] = self._contains_ip_pattern(content)
                analysis["contains_base64"] = self._contains_base64_pattern(content)

        except Exception as e:
            analysis["error"] = str(e)

        return analysis

    def _contains_ip_pattern(self, content: str) -> bool:
        """Check if content contains IP address patterns."""
        import re

        ip_pattern = r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"
        return bool(re.search(ip_pattern, content))

    def _contains_base64_pattern(self, content: str) -> bool:
        """Check if content contains base64 patterns."""
        import re

        base64_pattern = r"[A-Za-z0-9+/]{20,}={0,2}"
        return bool(re.search(base64_pattern, content))

    def list_directory_safe(self, directory: str, max_files: int = 100) -> Dict[str, Any]:
        """List directory contents safely."""
        try:
            dir_path = Path(directory)

            if not dir_path.exists():
                return {"error": "Directory does not exist"}

            if not dir_path.is_dir():
                return {"error": "Path is not a directory"}

            files = []
            dirs = []

            for item in dir_path.iterdir():
                if len(files) + len(dirs) >= max_files:
                    break

                try:
                    if item.is_file():
                        files.append(
                            {
                                "name": item.name,
                                "size": item.stat().st_size,
                                "modified": item.stat().st_mtime,
                                "extension": item.suffix,
                            }
                        )
                    elif item.is_dir():
                        dirs.append(
                            {
                                "name": item.name,
                                "modified": item.stat().st_mtime,
                            }
                        )
                except PermissionError:
                    continue

            return {
                "directory": str(dir_path),
                "file_count": len(files),
                "dir_count": len(dirs),
                "files": files,
                "directories": dirs,
                "truncated": len(files) + len(dirs) >= max_files,
            }

        except Exception as e:
            return {"error": f"Directory listing failed: {str(e)}"}


def create_file_handler() -> SafeFileHandler:
    """Factory function to create file handler."""
    return SafeFileHandler()

