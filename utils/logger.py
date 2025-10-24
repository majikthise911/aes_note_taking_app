"""
Logging configuration and utilities.
"""
import logging
from pathlib import Path
from typing import Optional

from config.settings import LOG_LEVEL, LOG_FILE, LOG_FORMAT


def setup_logger(
    name: str = "notes_app",
    log_file: Path = LOG_FILE,
    level: str = LOG_LEVEL,
) -> logging.Logger:
    """
    Set up application logger.

    Args:
        name: Logger name
        log_file: Path to log file
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(LOG_FORMAT)
    file_handler.setFormatter(file_formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter("%(levelname)s - %(message)s")
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# Global logger instance
logger = setup_logger()


def log_api_call(
    endpoint: str,
    status: str,
    duration: Optional[float] = None,
    error: Optional[str] = None,
):
    """
    Log an API call.

    Args:
        endpoint: API endpoint
        status: Call status (success/failure)
        duration: Call duration in seconds
        error: Error message if failed
    """
    message = f"API Call: {endpoint} - Status: {status}"
    if duration:
        message += f" - Duration: {duration:.2f}s"
    if error:
        message += f" - Error: {error}"

    if status == "success":
        logger.info(message)
    else:
        logger.error(message)


def log_db_operation(
    operation: str, table: str, status: str, error: Optional[str] = None
):
    """
    Log a database operation.

    Args:
        operation: Operation type (INSERT, UPDATE, SELECT, etc.)
        table: Table name
        status: Operation status
        error: Error message if failed
    """
    message = f"DB Operation: {operation} on {table} - Status: {status}"
    if error:
        message += f" - Error: {error}"

    if status == "success":
        logger.debug(message)
    else:
        logger.error(message)


def log_user_action(username: str, action: str, details: Optional[str] = None):
    """
    Log a user action.

    Args:
        username: Username
        action: Action performed
        details: Additional details
    """
    message = f"User Action: {username} - {action}"
    if details:
        message += f" - {details}"

    logger.info(message)
