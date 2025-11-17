"""
Unit tests for database operations.

Run with: pytest tests/test_database.py
"""
import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from database.db_manager import DatabaseManager
from database.models import Note, Project


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    db = DatabaseManager(db_path)
    yield db

    # Cleanup
    db_path.unlink(missing_ok=True)


@pytest.fixture
def test_project(temp_db):
    """Create a test project."""
    project_id = temp_db.create_project("Test Project")
    return project_id


class TestProjectOperations:
    """Test project CRUD operations."""

    def test_create_project(self, temp_db):
        """Test creating a project."""
        project_id = temp_db.create_project("My Test Project")
        assert project_id > 0

        project = temp_db.get_project_by_id(project_id)
        assert project is not None
        assert project.name == "My Test Project"
        assert project.id == project_id

    def test_get_project_by_name(self, temp_db):
        """Test retrieving project by name."""
        temp_db.create_project("Unique Project")
        project = temp_db.get_project_by_name("Unique Project")

        assert project is not None
        assert project.name == "Unique Project"

    def test_get_all_projects(self, temp_db):
        """Test retrieving all projects."""
        temp_db.create_project("Project A")
        temp_db.create_project("Project B")

        projects = temp_db.get_all_projects()
        assert len(projects) >= 2

        project_names = [p.name for p in projects]
        assert "Project A" in project_names
        assert "Project B" in project_names

    def test_delete_project(self, temp_db):
        """Test deleting a project."""
        project_id = temp_db.create_project("To Delete")
        assert temp_db.delete_project(project_id) is True

        project = temp_db.get_project_by_id(project_id)
        assert project is None


class TestNoteOperations:
    """Test note CRUD operations."""

    def test_insert_note(self, temp_db, test_project):
        """Test inserting a note."""
        note_id = temp_db.insert_note(
            raw_text="Raw test note",
            project_id=test_project,
            cleaned_text="Cleaned test note",
            category="General",
            date="2025-01-01",
            timestamp="12:00:00",
            approval_status="pending"
        )

        assert note_id > 0

        note = temp_db.get_note_by_id(note_id)
        assert note is not None
        assert note.raw_text == "Raw test note"
        assert note.cleaned_text == "Cleaned test note"
        assert note.category == "General"
        assert note.approval_status == "pending"

    def test_insert_note_with_confidence(self, temp_db, test_project):
        """Test inserting a note with confidence score."""
        note_id = temp_db.insert_note(
            raw_text="Test note",
            project_id=test_project,
            cleaned_text="Test cleaned",
            category="General",
            date="2025-01-01",
            timestamp="12:00:00",
            confidence_score=0.95,
            clarifying_question="Is this correct?"
        )

        note = temp_db.get_note_by_id(note_id)
        assert note.confidence_score == 0.95
        assert note.clarifying_question == "Is this correct?"

    def test_update_note(self, temp_db, test_project):
        """Test updating a note."""
        note_id = temp_db.insert_note(
            raw_text="Original",
            project_id=test_project,
            cleaned_text="Original cleaned",
            category="General",
            date="2025-01-01",
            timestamp="12:00:00"
        )

        # Update the note
        success = temp_db.update_note(
            note_id=note_id,
            cleaned_text="Updated cleaned",
            category="Schedule",
            approval_status="approved"
        )

        assert success is True

        note = temp_db.get_note_by_id(note_id)
        assert note.cleaned_text == "Updated cleaned"
        assert note.category == "Schedule"
        assert note.approval_status == "approved"

    def test_get_notes_paginated(self, temp_db, test_project):
        """Test paginated note retrieval."""
        # Create multiple notes
        for i in range(15):
            temp_db.insert_note(
                raw_text=f"Note {i}",
                project_id=test_project,
                cleaned_text=f"Cleaned note {i}",
                category="General",
                date="2025-01-01",
                timestamp=f"12:{i:02d}:00",
                approval_status="approved"
            )

        # Get first page (10 notes)
        notes, total = temp_db.get_notes_paginated(
            page=1,
            per_page=10,
            approval_status="approved",
            project_id=test_project
        )

        assert len(notes) == 10
        assert total == 15

        # Get second page (5 notes)
        notes, total = temp_db.get_notes_paginated(
            page=2,
            per_page=10,
            approval_status="approved",
            project_id=test_project
        )

        assert len(notes) == 5
        assert total == 15

    def test_get_pending_notes(self, temp_db, test_project):
        """Test retrieving pending notes."""
        # Create pending notes
        temp_db.insert_note(
            raw_text="Pending 1",
            project_id=test_project,
            category="General",
            date="2025-01-01",
            timestamp="12:00:00",
            approval_status="pending"
        )
        temp_db.insert_note(
            raw_text="Pending 2",
            project_id=test_project,
            category="General",
            date="2025-01-01",
            timestamp="12:01:00",
            approval_status="pending"
        )

        # Create approved note
        temp_db.insert_note(
            raw_text="Approved",
            project_id=test_project,
            category="General",
            date="2025-01-01",
            timestamp="12:02:00",
            approval_status="approved"
        )

        pending, total = temp_db.get_pending_notes(project_id=test_project)
        assert total == 2
        assert len(pending) == 2

    def test_delete_note(self, temp_db, test_project):
        """Test deleting a note."""
        note_id = temp_db.insert_note(
            raw_text="To delete",
            project_id=test_project,
            category="General",
            date="2025-01-01",
            timestamp="12:00:00"
        )

        assert temp_db.delete_note(note_id) is True
        assert temp_db.get_note_by_id(note_id) is None


class TestSearchOperations:
    """Test search functionality."""

    def test_search_notes_basic(self, temp_db, test_project):
        """Test basic search functionality."""
        # Create test notes
        temp_db.insert_note(
            raw_text="Meeting about engineering design",
            project_id=test_project,
            cleaned_text="Discussion on engineering design approach",
            category="General",
            date="2025-01-01",
            timestamp="10:00:00",
            approval_status="approved"
        )
        temp_db.insert_note(
            raw_text="Budget review meeting",
            project_id=test_project,
            cleaned_text="Reviewed budget and pricing",
            category="Pricing",
            date="2025-01-02",
            timestamp="11:00:00",
            approval_status="approved"
        )
        temp_db.insert_note(
            raw_text="Schedule update",
            project_id=test_project,
            cleaned_text="Updated project schedule",
            category="Schedule",
            date="2025-01-03",
            timestamp="12:00:00",
            approval_status="approved"
        )

        # Search for "engineering"
        notes, total = temp_db.search_notes(
            search_query="engineering",
            project_id=test_project,
            approval_status="approved"
        )

        assert total == 1
        assert "engineering" in notes[0].cleaned_text.lower()

    def test_search_notes_in_category(self, temp_db, test_project):
        """Test searching by category name."""
        temp_db.insert_note(
            raw_text="Test note",
            project_id=test_project,
            cleaned_text="Some content",
            category="Pricing",
            date="2025-01-01",
            timestamp="10:00:00",
            approval_status="approved"
        )
        temp_db.insert_note(
            raw_text="Another note",
            project_id=test_project,
            cleaned_text="Other content",
            category="Schedule",
            date="2025-01-02",
            timestamp="11:00:00",
            approval_status="approved"
        )

        # Search for category "Pricing"
        notes, total = temp_db.search_notes(
            search_query="Pricing",
            project_id=test_project,
            approval_status="approved"
        )

        assert total == 1
        assert notes[0].category == "Pricing"

    def test_search_notes_with_filters(self, temp_db, test_project):
        """Test search with date and category filters."""
        temp_db.insert_note(
            raw_text="Engineering note 1",
            project_id=test_project,
            cleaned_text="Engineering content",
            category="General",
            date="2025-01-01",
            timestamp="10:00:00",
            approval_status="approved"
        )
        temp_db.insert_note(
            raw_text="Engineering note 2",
            project_id=test_project,
            cleaned_text="More engineering content",
            category="General",
            date="2025-01-15",
            timestamp="11:00:00",
            approval_status="approved"
        )

        # Search with date filter
        notes, total = temp_db.search_notes(
            search_query="engineering",
            project_id=test_project,
            approval_status="approved",
            date_from="2025-01-10",
            date_to="2025-01-20"
        )

        assert total == 1
        assert notes[0].date == "2025-01-15"

    def test_search_notes_no_results(self, temp_db, test_project):
        """Test search with no matching results."""
        temp_db.insert_note(
            raw_text="Some note",
            project_id=test_project,
            cleaned_text="Some content",
            category="General",
            date="2025-01-01",
            timestamp="10:00:00",
            approval_status="approved"
        )

        notes, total = temp_db.search_notes(
            search_query="nonexistent",
            project_id=test_project,
            approval_status="approved"
        )

        assert total == 0
        assert len(notes) == 0


class TestStatistics:
    """Test statistics functionality."""

    def test_get_statistics(self, temp_db, test_project):
        """Test getting database statistics."""
        # Create notes with different statuses and categories
        temp_db.insert_note(
            raw_text="Note 1",
            project_id=test_project,
            category="General",
            date="2025-01-01",
            timestamp="10:00:00",
            approval_status="approved"
        )
        temp_db.insert_note(
            raw_text="Note 2",
            project_id=test_project,
            category="General",
            date="2025-01-02",
            timestamp="11:00:00",
            approval_status="approved"
        )
        temp_db.insert_note(
            raw_text="Note 3",
            project_id=test_project,
            category="Pricing",
            date="2025-01-03",
            timestamp="12:00:00",
            approval_status="pending"
        )

        stats = temp_db.get_statistics(project_id=test_project)

        assert "by_status" in stats
        assert stats["by_status"]["approved"] == 2
        assert stats["by_status"]["pending"] == 1

        assert "by_category" in stats
        assert stats["by_category"]["General"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
