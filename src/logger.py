"""Centralized logging system for the RPG game.

Provides consistent logging across all modules with configurable levels,
file output, and colored console output for better debugging.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


class ColoredFormatter(logging.Formatter):
    """Custom formatter with color support for console output."""

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }

    def format(self, record):
        # Add color to levelname
        if record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}{record.levelname}"
                f"{self.COLORS['RESET']}"
            )
        return super().format(record)


class GameLogger:
    """Singleton logger manager for the game."""

    _instance: Optional['GameLogger'] = None
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize logger (only once)."""
        if GameLogger._initialized:
            return

        GameLogger._initialized = True

        # Create logs directory
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)

        # Create root logger
        self.root_logger = logging.getLogger("rpg")
        self.root_logger.setLevel(logging.DEBUG)

        # Prevent duplicate handlers
        if self.root_logger.handlers:
            return

        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)  # Only INFO+ to console
        console_formatter = ColoredFormatter(
            '%(levelname)-8s [%(name)s] %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self.root_logger.addHandler(console_handler)

        # File handler (detailed logs)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.log_dir / f"game_{timestamp}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # All logs to file
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)-8s - [%(name)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.root_logger.addHandler(file_handler)

        # Keep only last 10 log files
        self._cleanup_old_logs()

        self.root_logger.info("=" * 60)
        self.root_logger.info("Game logger initialized")
        self.root_logger.info(f"Log file: {log_file}")
        self.root_logger.info("=" * 60)

    def _cleanup_old_logs(self, keep_count: int = 10):
        """Remove old log files, keeping only the most recent ones."""
        try:
            log_files = sorted(
                self.log_dir.glob("game_*.log"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )

            # Remove old files
            for old_file in log_files[keep_count:]:
                old_file.unlink()

        except Exception as e:
            # Don't crash if cleanup fails
            print(f"Warning: Failed to cleanup old logs: {e}")

    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger for a specific module.

        Args:
            name: Module name (e.g., 'battle', 'world', 'entities')

        Returns:
            Configured logger instance
        """
        return logging.getLogger(f"rpg.{name}")

    def set_level(self, level: str):
        """Change console logging level.

        Args:
            level: 'DEBUG', 'INFO', 'WARNING', 'ERROR', or 'CRITICAL'
        """
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }

        if level.upper() in level_map:
            # Update console handler only
            for handler in self.root_logger.handlers:
                if isinstance(handler, logging.StreamHandler) and \
                   handler.stream == sys.stdout:
                    handler.setLevel(level_map[level.upper()])
                    self.root_logger.info(f"Console log level set to {level.upper()}")


# Global singleton instance
_game_logger = GameLogger()


def get_logger(name: str) -> logging.Logger:
    """Convenient function to get a logger.

    Args:
        name: Module name

    Returns:
        Configured logger instance

    Example:
        >>> from src.logger import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Something happened")
        >>> logger.error("Something broke", exc_info=True)
    """
    return _game_logger.get_logger(name)


def set_log_level(level: str):
    """Change console logging level.

    Args:
        level: 'DEBUG', 'INFO', 'WARNING', 'ERROR', or 'CRITICAL'
    """
    _game_logger.set_level(level)


# Convenience functions for quick logging without creating logger
def debug(message: str, module: str = "game"):
    """Quick debug log."""
    get_logger(module).debug(message)


def info(message: str, module: str = "game"):
    """Quick info log."""
    get_logger(module).info(message)


def warning(message: str, module: str = "game"):
    """Quick warning log."""
    get_logger(module).warning(message)


def error(message: str, module: str = "game", exc_info: bool = False):
    """Quick error log."""
    get_logger(module).error(message, exc_info=exc_info)


def critical(message: str, module: str = "game", exc_info: bool = False):
    """Quick critical log."""
    get_logger(module).critical(message, exc_info=exc_info)
