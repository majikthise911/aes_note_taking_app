"""
Input validation utilities.
"""
import re
from datetime import datetime
from typing import Optional

from config.categories import validate_category


def validate_note_text(text: str, min_length: int = 5, max_length: int = 10000) -> tuple[bool, Optional[str]]:
    """
    Validate note text input.

    Args:
        text: Note text to validate
        min_length: Minimum allowed length
        max_length: Maximum allowed length

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not text or not text.strip():
        return False, "Note text cannot be empty"

    if len(text) < min_length:
        return False, f"Note text must be at least {min_length} characters"

    if len(text) > max_length:
        return False, f"Note text cannot exceed {max_length} characters"

    return True, None


def validate_date_format(date_str: str) -> tuple[bool, Optional[str]]:
    """
    Validate date string format (YYYY-MM-DD).

    Args:
        date_str: Date string to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not date_str:
        return False, "Date cannot be empty"

    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True, None
    except ValueError:
        return False, "Date must be in YYYY-MM-DD format"


def validate_timestamp_format(timestamp_str: str) -> tuple[bool, Optional[str]]:
    """
    Validate timestamp string format (HH:MM:SS).

    Args:
        timestamp_str: Timestamp string to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not timestamp_str:
        return False, "Timestamp cannot be empty"

    try:
        datetime.strptime(timestamp_str, "%H:%M:%S")
        return True, None
    except ValueError:
        return False, "Timestamp must be in HH:MM:SS format"


def validate_category_name(category: str) -> tuple[bool, Optional[str]]:
    """
    Validate category against predefined list.

    Args:
        category: Category name to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not category:
        return False, "Category cannot be empty"

    if not validate_category(category):
        return False, f"'{category}' is not a valid category"

    return True, None


def validate_approval_status(status: str) -> tuple[bool, Optional[str]]:
    """
    Validate approval status.

    Args:
        status: Approval status to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    valid_statuses = ["pending", "approved", "rejected"]

    if status not in valid_statuses:
        return False, f"Status must be one of: {', '.join(valid_statuses)}"

    return True, None


def sanitize_input(text: str) -> str:
    """
    Sanitize user input to prevent issues.

    Args:
        text: Text to sanitize

    Returns:
        Sanitized text
    """
    # Remove leading/trailing whitespace
    text = text.strip()

    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text)

    return text
