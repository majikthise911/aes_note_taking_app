"""
Database manager for SQLite operations.
"""
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from config.settings import DATABASE_PATH, BACKUP_DIR
from database.models import Note, LogEntry, NOTES_TABLE_SCHEMA, LOGS_TABLE_SCHEMA


class DatabaseManager:
    """
    Manages all database operations for the notes application.
    """

    def __init__(self, db_path: Path = DATABASE_PATH):
        """
        Initialize database manager.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.initialize_database()

    def initialize_database(self):
        """Create tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.executescript(NOTES_TABLE_SCHEMA)
            cursor.executescript(LOGS_TABLE_SCHEMA)
            conn.commit()

    def create_backup(self) -> Path:
        """
        Create a backup of the database.

        Returns:
            Path to backup file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = BACKUP_DIR / f"notes_backup_{timestamp}.db"
        shutil.copy2(self.db_path, backup_path)
        return backup_path

    # ============ Note Operations ============

    def insert_note(
        self,
        raw_text: str,
        cleaned_text: Optional[str] = None,
        category: Optional[str] = None,
        date: Optional[str] = None,
        timestamp: Optional[str] = None,
        approval_status: str = "pending",
    ) -> int:
        """
        Insert a new note into the database.

        Args:
            raw_text: Original user input
            cleaned_text: GPT-processed text
            category: Assigned category
            date: Note date (YYYY-MM-DD)
            timestamp: Note time (HH:MM:SS)
            approval_status: Approval status

        Returns:
            ID of inserted note
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO notes (raw_text, cleaned_text, category, date, timestamp, approval_status)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (raw_text, cleaned_text, category, date, timestamp, approval_status),
            )
            conn.commit()
            return cursor.lastrowid

    def update_note(
        self,
        note_id: int,
        cleaned_text: Optional[str] = None,
        category: Optional[str] = None,
        approval_status: Optional[str] = None,
    ) -> bool:
        """
        Update an existing note.

        Args:
            note_id: ID of note to update
            cleaned_text: New cleaned text
            category: New category
            approval_status: New approval status

        Returns:
            True if updated, False if not found
        """
        updates = []
        values = []

        if cleaned_text is not None:
            updates.append("cleaned_text = ?")
            values.append(cleaned_text)
        if category is not None:
            updates.append("category = ?")
            values.append(category)
        if approval_status is not None:
            updates.append("approval_status = ?")
            values.append(approval_status)

        if not updates:
            return False

        values.append(note_id)
        query = f"UPDATE notes SET {', '.join(updates)} WHERE id = ?"

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, values)
            conn.commit()
            return cursor.rowcount > 0

    def get_note_by_id(self, note_id: int) -> Optional[Note]:
        """
        Retrieve a note by ID.

        Args:
            note_id: Note ID

        Returns:
            Note instance or None
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
            row = cursor.fetchone()
            return Note.from_db_row(row) if row else None

    def get_notes_paginated(
        self,
        page: int = 1,
        per_page: int = 50,
        approval_status: str = "approved",
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        category: Optional[str] = None,
    ) -> Tuple[List[Note], int]:
        """
        Get paginated notes with filters.

        Args:
            page: Page number (1-indexed)
            per_page: Notes per page
            approval_status: Filter by approval status
            date_from: Filter by start date (YYYY-MM-DD)
            date_to: Filter by end date (YYYY-MM-DD)
            category: Filter by category

        Returns:
            Tuple of (list of notes, total count)
        """
        offset = (page - 1) * per_page
        where_clauses = ["approval_status = ?"]
        params = [approval_status]

        if date_from:
            where_clauses.append("date >= ?")
            params.append(date_from)
        if date_to:
            where_clauses.append("date <= ?")
            params.append(date_to)
        if category:
            where_clauses.append("category = ?")
            params.append(category)

        where_sql = " AND ".join(where_clauses)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Get total count
            cursor.execute(f"SELECT COUNT(*) FROM notes WHERE {where_sql}", params)
            total_count = cursor.fetchone()[0]

            # Get paginated results
            cursor.execute(
                f"""
                SELECT * FROM notes
                WHERE {where_sql}
                ORDER BY date DESC, timestamp DESC
                LIMIT ? OFFSET ?
                """,
                params + [per_page, offset],
            )
            rows = cursor.fetchall()
            notes = [Note.from_db_row(row) for row in rows]

            return notes, total_count

    def get_notes_by_category(
        self, category: str, approval_status: str = "approved"
    ) -> List[Note]:
        """
        Get all notes for a specific category.

        Args:
            category: Category name
            approval_status: Filter by approval status

        Returns:
            List of Note instances
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM notes
                WHERE category = ? AND approval_status = ?
                ORDER BY date DESC, timestamp DESC
                """,
                (category, approval_status),
            )
            rows = cursor.fetchall()
            return [Note.from_db_row(row) for row in rows]

    def get_pending_notes(self) -> List[Note]:
        """
        Get all pending notes awaiting approval.

        Returns:
            List of Note instances
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM notes
                WHERE approval_status = 'pending'
                ORDER BY created_at DESC
                """
            )
            rows = cursor.fetchall()
            return [Note.from_db_row(row) for row in rows]

    def delete_note(self, note_id: int) -> bool:
        """
        Delete a note.

        Args:
            note_id: ID of note to delete

        Returns:
            True if deleted, False if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
            conn.commit()
            return cursor.rowcount > 0

    # ============ Log Operations ============

    def insert_log(
        self,
        level: str,
        message: str,
        user_id: Optional[str] = None,
        action_type: Optional[str] = None,
    ) -> int:
        """
        Insert a log entry.

        Args:
            level: Log level (INFO, WARNING, ERROR, etc.)
            message: Log message
            user_id: User who triggered the action
            action_type: Type of action

        Returns:
            ID of inserted log entry
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO logs (level, message, user_id, action_type)
                VALUES (?, ?, ?, ?)
                """,
                (level, message, user_id, action_type),
            )
            conn.commit()
            return cursor.lastrowid

    def get_logs(
        self, limit: int = 100, level: Optional[str] = None
    ) -> List[LogEntry]:
        """
        Get recent log entries.

        Args:
            limit: Maximum number of logs to retrieve
            level: Filter by log level

        Returns:
            List of LogEntry instances
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if level:
                cursor.execute(
                    """
                    SELECT * FROM logs
                    WHERE level = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (level, limit),
                )
            else:
                cursor.execute(
                    """
                    SELECT * FROM logs
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (limit,),
                )
            rows = cursor.fetchall()
            return [LogEntry.from_db_row(row) for row in rows]

    # ============ Statistics ============

    def get_statistics(self) -> dict:
        """
        Get database statistics.

        Returns:
            Dictionary with statistics
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            stats = {}

            # Total notes by status
            cursor.execute(
                "SELECT approval_status, COUNT(*) FROM notes GROUP BY approval_status"
            )
            stats["by_status"] = dict(cursor.fetchall())

            # Total notes by category
            cursor.execute(
                """
                SELECT category, COUNT(*) FROM notes
                WHERE approval_status = 'approved'
                GROUP BY category
                """
            )
            stats["by_category"] = dict(cursor.fetchall())

            # Notes per day (last 30 days)
            cursor.execute(
                """
                SELECT date, COUNT(*) FROM notes
                WHERE approval_status = 'approved'
                AND date >= date('now', '-30 days')
                GROUP BY date
                ORDER BY date DESC
                """
            )
            stats["notes_per_day"] = dict(cursor.fetchall())

            return stats
