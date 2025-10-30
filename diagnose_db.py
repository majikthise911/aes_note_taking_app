"""
Diagnostic script to check and fix database issues.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path("data/notes.db")

def diagnose_database():
    """Diagnose database issues."""
    print(f"Checking database at: {DB_PATH}")
    print("=" * 50)

    if not DB_PATH.exists():
        print("❌ Database file does not exist!")
        print("   The app will create it on first run.")
        return

    print("✅ Database file exists")

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"\n📊 Tables found: {', '.join(tables)}")

        # Check projects table
        if 'projects' in tables:
            cursor.execute("SELECT COUNT(*) FROM projects")
            project_count = cursor.fetchone()[0]
            print(f"\n✅ Projects table exists with {project_count} project(s)")

            if project_count > 0:
                cursor.execute("SELECT id, name FROM projects")
                projects = cursor.fetchall()
                print("   Projects:")
                for pid, name in projects:
                    print(f"   - ID: {pid}, Name: {name}")
        else:
            print("\n❌ Projects table missing!")

        # Check notes table structure
        if 'notes' in tables:
            cursor.execute("PRAGMA table_info(notes)")
            columns = [(row[1], row[2]) for row in cursor.fetchall()]
            print(f"\n✅ Notes table exists")
            print("   Columns:")
            for col_name, col_type in columns:
                print(f"   - {col_name} ({col_type})")

            # Check if project_id column exists
            col_names = [col[0] for col in columns]
            if 'project_id' not in col_names:
                print("\n⚠️  WARNING: notes table missing project_id column!")
                print("   This will be added on next app run.")

            # Check notes count
            cursor.execute("SELECT COUNT(*) FROM notes")
            notes_count = cursor.fetchone()[0]
            print(f"\n📝 Total notes: {notes_count}")

            if 'project_id' in col_names:
                cursor.execute("SELECT COUNT(*) FROM notes WHERE project_id IS NULL")
                null_project_notes = cursor.fetchone()[0]
                if null_project_notes > 0:
                    print(f"⚠️  {null_project_notes} notes have NULL project_id (will be migrated)")
        else:
            print("\n❌ Notes table missing!")

        conn.close()
        print("\n" + "=" * 50)
        print("✅ Database diagnosis complete!")

    except Exception as e:
        print(f"\n❌ Error checking database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    diagnose_database()
