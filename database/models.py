"""
Data models and database schemas.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Project:
    """
    Represents a project.

    Attributes:
        id: Unique identifier
        name: Project name
        created_at: Database creation timestamp
    """

    id: Optional[int] = None
    name: str = ""
    created_at: Optional[str] = None

    @classmethod
    def from_db_row(cls, row: tuple) -> "Project":
        """
        Create Project instance from database row.

        Args:
            row: Database row tuple

        Returns:
            Project instance
        """
        return cls(
            id=row[0],
            name=row[1],
            created_at=row[2],
        )


@dataclass
class Note:
    """
    Represents a project note.

    Attributes:
        id: Unique identifier
        project_id: Associated project ID
        raw_text: Original user input
        cleaned_text: GPT-processed text
        category: Assigned category
        date: Note date (YYYY-MM-DD)
        timestamp: Note time (HH:MM:SS)
        approval_status: One of 'pending', 'approved', 'rejected'
        confidence_score: AI confidence in categorization (0.0-1.0)
        clarifying_question: Optional question to improve categorization
        created_at: Database creation timestamp
    """

    id: Optional[int] = None
    project_id: Optional[int] = None
    raw_text: str = ""
    cleaned_text: Optional[str] = None
    category: Optional[str] = None
    date: Optional[str] = None
    timestamp: Optional[str] = None
    approval_status: str = "pending"
    confidence_score: Optional[float] = None
    clarifying_question: Optional[str] = None
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
        # Handle both old and new schema
        if len(row) >= 11:
            return cls(
                id=row[0],
                project_id=row[1],
                raw_text=row[2],
                cleaned_text=row[3],
                category=row[4],
                date=row[5],
                timestamp=row[6],
                approval_status=row[7],
                confidence_score=row[8],
                clarifying_question=row[9],
                created_at=row[10],
            )
        else:
            # Old schema without confidence fields
            return cls(
                id=row[0],
                project_id=row[1],
                raw_text=row[2],
                cleaned_text=row[3],
                category=row[4],
                date=row[5],
                timestamp=row[6],
                approval_status=row[7],
                confidence_score=None,
                clarifying_question=None,
                created_at=row[8] if len(row) > 8 else None,
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
PROJECTS_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_project_name ON projects(name);
"""

NOTES_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    raw_text TEXT NOT NULL,
    cleaned_text TEXT,
    category TEXT,
    date TEXT,
    timestamp TEXT,
    approval_status TEXT CHECK(approval_status IN ('pending', 'approved', 'rejected')) DEFAULT 'pending',
    confidence_score REAL,
    clarifying_question TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_project_id ON notes(project_id);
CREATE INDEX IF NOT EXISTS idx_date ON notes(date);
CREATE INDEX IF NOT EXISTS idx_category ON notes(category);
CREATE INDEX IF NOT EXISTS idx_approval_status ON notes(approval_status);
CREATE INDEX IF NOT EXISTS idx_confidence_score ON notes(confidence_score);
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
