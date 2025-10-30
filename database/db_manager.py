"""
Database manager for SQLite operations.
"""
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from config.settings import DATABASE_PATH, BACKUP_DIR
from database.models import Note, Project, LogEntry, NOTES_TABLE_SCHEMA, PROJECTS_TABLE_SCHEMA, LOGS_TABLE_SCHEMA
from utils.logger import logger


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

            # Create projects table first
            cursor.executescript(PROJECTS_TABLE_SCHEMA)

            # Check if notes table exists and needs migration
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='notes'"
            )
            notes_table_exists = cursor.fetchone() is not None

            if notes_table_exists:
                # Check if columns need to be added
                cursor.execute("PRAGMA table_info(notes)")
                columns = [col[1] for col in cursor.fetchall()]

                # Add project_id if missing
                if 'project_id' not in columns:
                    cursor.execute("ALTER TABLE notes ADD COLUMN project_id INTEGER")

                    # Create a default project for migration
                    cursor.execute("SELECT id FROM projects WHERE name = 'Default Project'")
                    default_project = cursor.fetchone()
                    if not default_project:
                        cursor.execute("INSERT INTO projects (name) VALUES ('Default Project')")
                        default_project_id = cursor.lastrowid
                    else:
                        default_project_id = default_project[0]

                    # Assign all existing notes to the default project
                    cursor.execute("UPDATE notes SET project_id = ? WHERE project_id IS NULL", (default_project_id,))
                    logger.info(f"Migrated existing notes to Default Project (ID: {default_project_id})")

                # Add confidence_score if missing
                if 'confidence_score' not in columns:
                    cursor.execute("ALTER TABLE notes ADD COLUMN confidence_score REAL")
                    logger.info("Added confidence_score column")

                # Add clarifying_question if missing
                if 'clarifying_question' not in columns:
                    cursor.execute("ALTER TABLE notes ADD COLUMN clarifying_question TEXT")
                    logger.info("Added clarifying_question column")

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

    # ============ Project Operations ============

    def create_project(self, name: str) -> int:
        """
        Create a new project.

        Args:
            name: Project name

        Returns:
            ID of created project

        Raises:
            sqlite3.IntegrityError: If project name already exists
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO projects (name) VALUES (?)",
                (name,),
            )
            conn.commit()
            return cursor.lastrowid

    def get_project_by_id(self, project_id: int) -> Optional[Project]:
        """
        Retrieve a project by ID.

        Args:
            project_id: Project ID

        Returns:
            Project instance or None
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
            row = cursor.fetchone()
            return Project.from_db_row(row) if row else None

    def get_project_by_name(self, name: str) -> Optional[Project]:
        """
        Retrieve a project by name.

        Args:
            name: Project name

        Returns:
            Project instance or None
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects WHERE name = ?", (name,))
            row = cursor.fetchone()
            return Project.from_db_row(row) if row else None

    def get_all_projects(self) -> List[Project]:
        """
        Get all projects ordered by creation date.

        Returns:
            List of Project instances
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects ORDER BY created_at ASC")
            rows = cursor.fetchall()
            return [Project.from_db_row(row) for row in rows]

    def delete_project(self, project_id: int) -> bool:
        """
        Delete a project and all its notes (CASCADE).

        Args:
            project_id: ID of project to delete

        Returns:
            True if deleted, False if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            conn.commit()
            return cursor.rowcount > 0

    # ============ Note Operations ============

    def insert_note(
        self,
        raw_text: str,
        project_id: int,
        cleaned_text: Optional[str] = None,
        category: Optional[str] = None,
        date: Optional[str] = None,
        timestamp: Optional[str] = None,
        approval_status: str = "pending",
        confidence_score: Optional[float] = None,
        clarifying_question: Optional[str] = None,
    ) -> int:
        """
        Insert a new note into the database.

        Args:
            raw_text: Original user input
            project_id: Associated project ID
            cleaned_text: GPT-processed text
            category: Assigned category
            date: Note date (YYYY-MM-DD)
            timestamp: Note time (HH:MM:SS)
            approval_status: Approval status
            confidence_score: AI confidence in categorization (0.0-1.0)
            clarifying_question: Optional question to improve categorization

        Returns:
            ID of inserted note
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO notes (raw_text, project_id, cleaned_text, category, date, timestamp,
                                   approval_status, confidence_score, clarifying_question)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (raw_text, project_id, cleaned_text, category, date, timestamp,
                 approval_status, confidence_score, clarifying_question),
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
        project_id: Optional[int] = None,
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
            project_id: Filter by project ID
            date_from: Filter by start date (YYYY-MM-DD)
            date_to: Filter by end date (YYYY-MM-DD)
            category: Filter by category

        Returns:
            Tuple of (list of notes, total count)
        """
        offset = (page - 1) * per_page
        where_clauses = ["approval_status = ?"]
        params = [approval_status]

        if project_id:
            where_clauses.append("project_id = ?")
            params.append(project_id)
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
        self, category: str, approval_status: str = "approved", project_id: Optional[int] = None
    ) -> List[Note]:
        """
        Get all notes for a specific category.

        Args:
            category: Category name
            approval_status: Filter by approval status
            project_id: Filter by project ID

        Returns:
            List of Note instances
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            if project_id:
                cursor.execute(
                    """
                    SELECT * FROM notes
                    WHERE category = ? AND approval_status = ? AND project_id = ?
                    ORDER BY date DESC, timestamp DESC
                    """,
                    (category, approval_status, project_id),
                )
            else:
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

    def get_pending_notes(
        self, page: Optional[int] = None, per_page: int = 50, project_id: Optional[int] = None
    ) -> Tuple[List[Note], int]:
        """
        Get pending notes awaiting approval.

        Args:
            page: Page number (1-indexed), None for all notes
            per_page: Notes per page (only used if page is provided)
            project_id: Filter by project ID

        Returns:
            Tuple of (list of Note instances, total count)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Build where clause
            where_clause = "approval_status = 'pending'"
            params = []
            if project_id:
                where_clause += " AND project_id = ?"
                params.append(project_id)

            # Get total count
            cursor.execute(f"SELECT COUNT(*) FROM notes WHERE {where_clause}", params)
            total_count = cursor.fetchone()[0]

            # Build query with optional pagination
            query = f"""
                SELECT * FROM notes
                WHERE {where_clause}
                ORDER BY created_at DESC
            """

            if page is not None:
                offset = (page - 1) * per_page
                query += " LIMIT ? OFFSET ?"
                cursor.execute(query, params + [per_page, offset])
            else:
                cursor.execute(query, params)

            rows = cursor.fetchall()
            notes = [Note.from_db_row(row) for row in rows]
            return notes, total_count

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

    def get_statistics(self, project_id: Optional[int] = None) -> dict:
        """
        Get database statistics.

        Args:
            project_id: Filter by project ID

        Returns:
            Dictionary with statistics
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            stats = {}

            # Total notes by status
            if project_id:
                cursor.execute(
                    "SELECT approval_status, COUNT(*) FROM notes WHERE project_id = ? GROUP BY approval_status",
                    (project_id,)
                )
            else:
                cursor.execute(
                    "SELECT approval_status, COUNT(*) FROM notes GROUP BY approval_status"
                )
            stats["by_status"] = dict(cursor.fetchall())

            # Total notes by category
            if project_id:
                cursor.execute(
                    """
                    SELECT category, COUNT(*) FROM notes
                    WHERE approval_status = 'approved' AND project_id = ?
                    GROUP BY category
                    """,
                    (project_id,)
                )
            else:
                cursor.execute(
                    """
                    SELECT category, COUNT(*) FROM notes
                    WHERE approval_status = 'approved'
                    GROUP BY category
                    """
                )
            stats["by_category"] = dict(cursor.fetchall())

            # Notes per day (last 30 days)
            if project_id:
                cursor.execute(
                    """
                    SELECT date, COUNT(*) FROM notes
                    WHERE approval_status = 'approved' AND project_id = ?
                    AND date >= date('now', '-30 days')
                    GROUP BY date
                    ORDER BY date DESC
                    """,
                    (project_id,)
                )
            else:
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
