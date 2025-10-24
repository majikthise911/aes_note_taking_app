"""
Data models and database schemas.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Note:
    """
    Represents a project note.

    Attributes:
        id: Unique identifier
        raw_text: Original user input
        cleaned_text: GPT-processed text
        category: Assigned category
        date: Note date (YYYY-MM-DD)
        timestamp: Note time (HH:MM:SS)
        approval_status: One of 'pending', 'approved', 'rejected'
        created_at: Database creation timestamp
    """

    id: Optional[int] = None
    raw_text: str = ""
    cleaned_text: Optional[str] = None
    category: Optional[str] = None
    date: Optional[str] = None
    timestamp: Optional[str] = None
    approval_status: str = "pending"
    created_at: Optional[str] = None

    @classmethod
    def from_db_row(cls, row: tuple) -> "Note":
        """
        Create Note instance from database row.

        Args:
            row: Database row tuple

        Returns:
            Note instance
        """
        return cls(
            id=row[0],
            raw_text=row[1],
            cleaned_text=row[2],
            category=row[3],
            date=row[4],
            timestamp=row[5],
            approval_status=row[6],
            created_at=row[7],
        )


@dataclass
class LogEntry:
    """
    Represents a log entry for monitoring and debugging.

    Attributes:
        id: Unique identifier
        timestamp: Log timestamp
        level: Log level (INFO, WARNING, ERROR, etc.)
        message: Log message
        user_id: User who triggered the action
        action_type: Type of action (api_call, db_operation, user_action)
    """

    id: Optional[int] = None
    timestamp: Optional[str] = None
    level: str = "INFO"
    message: str = ""
    user_id: Optional[str] = None
    action_type: Optional[str] = None

    @classmethod
    def from_db_row(cls, row: tuple) -> "LogEntry":
        """
        Create LogEntry instance from database row.

        Args:
            row: Database row tuple

        Returns:
            LogEntry instance
        """
        return cls(
            id=row[0],
            timestamp=row[1],
            level=row[2],
            message=row[3],
            user_id=row[4],
            action_type=row[5],
        )


# Database schemas
NOTES_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_text TEXT NOT NULL,
    cleaned_text TEXT,
    category TEXT,
    date TEXT,
    timestamp TEXT,
    approval_status TEXT CHECK(approval_status IN ('pending', 'approved', 'rejected')) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_date ON notes(date);
CREATE INDEX IF NOT EXISTS idx_category ON notes(category);
CREATE INDEX IF NOT EXISTS idx_approval_status ON notes(approval_status);
"""

LOGS_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    level TEXT,
    message TEXT,
    user_id TEXT,
    action_type TEXT
);

CREATE INDEX IF NOT EXISTS idx_log_timestamp ON logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_log_level ON logs(level);
"""
