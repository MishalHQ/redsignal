"""
Centralized logging configuration for RedSignal platform.
Provides consistent logging across server and client components.
"""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional
import colorama
from rich.logging import RichHandler

colorama.init()


class RedSignalLogger:
    """Custom logger with file rotation and colored console output."""

    def __init__(self, name: str, log_file: Optional[str] = None, level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))

        # Prevent duplicate handlers
        if self.logger.handlers:
            return

        # Console handler with rich formatting
        console_handler = RichHandler(
            rich_tracebacks=True,
            show_time=True,
            show_path=False
        )
        console_handler.setLevel(logging.INFO)

        # File handler with rotation if log_file specified
        if log_file:
            self._setup_file_handler(log_file)

        self.logger.addHandler(console_handler)

    def _setup_file_handler(self, log_file: str):
        """Configure rotating file handler."""
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)

        self.logger.addHandler(file_handler)

    def get_logger(self):
        return self.logger


def get_logger(name: str, log_file: Optional[str] = None, level: str = "INFO") -> logging.Logger:
    """Factory function to get configured logger instance."""
    return RedSignalLogger(name, log_file, level).get_logger()

