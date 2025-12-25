"""Structured logging for Unibase Framework.

This module provides a centralized logging system with consistent formatting
and configurable log levels across all framework components.
"""
import logging
import sys
from typing import Optional
from functools import lru_cache


class UnibaseLogger:
    """Centralized logger for the framework with consistent formatting."""

    def __init__(self, name: str, level: int = logging.INFO):
        """Initialize logger with given name and level.

        Args:
            name: Logger name (will be prefixed with 'unibase.')
            level: Logging level (default: INFO)
        """
        self.logger = logging.getLogger(f"unibase.{name}")
        self.logger.setLevel(level)

        # Only add handler if none exists (avoid duplicate handlers)
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(level)

            # Consistent formatting across all loggers
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def debug(self, msg: str, **kwargs):
        """Log debug message.

        Args:
            msg: Message to log
            **kwargs: Additional context as extra fields
        """
        self.logger.debug(msg, extra=kwargs)

    def info(self, msg: str, **kwargs):
        """Log info message.

        Args:
            msg: Message to log
            **kwargs: Additional context as extra fields
        """
        self.logger.info(msg, extra=kwargs)

    def warning(self, msg: str, exc_info: bool = False, **kwargs):
        """Log warning message.

        Args:
            msg: Message to log
            exc_info: If True, include exception traceback
            **kwargs: Additional context as extra fields
        """
        self.logger.warning(msg, exc_info=exc_info, extra=kwargs)

    def error(self, msg: str, exc_info: bool = False, **kwargs):
        """Log error message.

        Args:
            msg: Message to log
            exc_info: If True, include exception traceback
            **kwargs: Additional context as extra fields
        """
        self.logger.error(msg, exc_info=exc_info, extra=kwargs)

    def critical(self, msg: str, **kwargs):
        """Log critical message.

        Args:
            msg: Message to log
            **kwargs: Additional context as extra fields
        """
        self.logger.critical(msg, extra=kwargs)


@lru_cache(maxsize=None)
def get_logger(name: str, level: int = logging.INFO) -> UnibaseLogger:
    """Get or create a logger for a module.

    This function is cached to ensure the same logger instance is returned
    for the same module name across the application.

    Args:
        name: Module name (e.g., 'memory.manager', 'registry', 'a2a.server')
        level: Logging level (default: INFO)

    Returns:
        UnibaseLogger instance for the given module

    Example:
        >>> logger = get_logger('memory.manager')
        >>> logger.info("Memory manager initialized")
        >>> logger.error("Failed to save memory", exc_info=True)
    """
    return UnibaseLogger(name, level)


def set_log_level(level: int):
    """Set log level for all Unibase loggers.

    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO)
    """
    logging.getLogger("unibase").setLevel(level)
