# Database Persistence Guide

## How Your Data is Stored

### SQLite Database File
```
aes_note_taking_app/
├── data/
│   ├── notes.db           ← ALL your data lives here
│   └── backups/
│       ├── notes_backup_20251030_120000.db
│       └── notes_backup_20251030_150000.db
```

## What is SQLite?

**SQLite** is a file-based database that:
- Stores everything in a single file (`notes.db`)
- Requires no server or setup
- Is fast, reliable, and lightweight
- Used by millions of apps (browsers, phones, etc.)

## How Data Persists

### When You Create a Note:
```python
1. User types note in Streamlit UI
2. AI processes note
3. db_manager.insert_note(...) is called
4. SQLite writes to data/notes.db file
5. Transaction commits (saves permanently)
6. Data survives app restart!
```

### Key Point: The `.commit()` Makes It Permanent
```python
with sqlite3.connect(self.db_path) as conn:
    cursor = conn.cursor()
    cursor.execute("INSERT INTO notes ...")
    conn.commit()  # ← Without this, data is lost!
```

## Database Schema

### Current Tables:

**1. projects**
```sql
CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
Stores: Default Project, Project A, Project B, etc.

**2. notes**
```sql
CREATE TABLE notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,                    -- Links to projects table
    raw_text TEXT NOT NULL,                -- Your original note
    cleaned_text TEXT,                      -- AI-cleaned version
    category TEXT,                          -- Budget, Engineering, etc.
    date TEXT,                             -- YYYY-MM-DD
    timestamp TEXT,                        -- HH:MM:SS
    approval_status TEXT,                  -- pending/approved/rejected
    confidence_score REAL,                 -- 0.0 to 1.0 (NEW!)
    clarifying_question TEXT,              -- Optional question (NEW!)
    created_at TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);
```

**3. logs**
```sql
CREATE TABLE logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    level TEXT,                            -- INFO, WARNING, ERROR
    message TEXT,
    user_id TEXT,
    action_type TEXT
);
```

## Data Relationships

```
Project "Solar Farm A"
├── Note #1: "Reviewed bid at 61.2 cents/W"
├── Note #2: "Engineering meeting scheduled"
└── Note #3: "Safety inspection passed"

Project "Wind Project B"
├── Note #4: "Budget approved"
└── Note #5: "Site visit completed"
```

Each note is linked to a project via `project_id`.

## Migration System

When the app starts, it checks if the database needs updates:

```python
# Check if notes table exists
if notes_table_exists:
    # Check what columns exist
    columns = get_columns()

    # Add missing columns (backwards compatible!)
    if 'project_id' not in columns:
        ALTER TABLE notes ADD COLUMN project_id INTEGER

    if 'confidence_score' not in columns:
        ALTER TABLE notes ADD COLUMN confidence_score REAL

    if 'clarifying_question' not in columns:
        ALTER TABLE notes ADD COLUMN clarifying_question TEXT
```

This means:
- Old databases get upgraded automatically
- No data loss
- Seamless updates

## Local vs Cloud Storage

### **Local Development (Your Computer)**
```
✅ Data persists forever
✅ Survives app restarts
✅ Survives computer reboots
✅ File is on your disk
```

Location: `~/code/aes_note_taking_app/data/notes.db`

### **Streamlit Cloud**
```
⚠️ Temporary storage
❌ Data lost on app reboot
❌ File system resets
```

**Solution for Production:**
- Connect to PostgreSQL, MySQL, or MongoDB
- Use Streamlit Cloud's secrets management
- Or use cloud storage (S3, Google Cloud Storage)

## Backup System

The app includes automatic backups:

```python
# Create backup
backup_path = db_manager.create_backup()
# Creates: notes_backup_20251030_143022.db
```

**Manual Backup:**
```bash
# Just copy the file!
cp data/notes.db data/notes_backup.db
```

**Restore Backup:**
```bash
# Replace current with backup
cp data/notes_backup.db data/notes.db
```

## Database Operations

### **CRUD Operations:**

**Create (INSERT)**
```python
note_id = db.insert_note(
    raw_text="My note",
    project_id=1,
    category="Engineering",
    confidence_score=0.85
)
```

**Read (SELECT)**
```python
# Get all notes for project
notes = db.get_notes_paginated(project_id=1)

# Get by category
notes = db.get_notes_by_category("Budget", project_id=1)

# Get pending notes
pending = db.get_pending_notes(project_id=1)
```

**Update (UPDATE)**
```python
db.update_note(
    note_id=123,
    cleaned_text="Updated text",
    approval_status="approved"
)
```

**Delete (DELETE)**
```python
db.delete_note(note_id=123)
db.delete_project(project_id=1)  # Deletes project + all notes!
```

## Indexes for Performance

The database has indexes on frequently queried columns:

```sql
CREATE INDEX idx_project_id ON notes(project_id);
CREATE INDEX idx_date ON notes(date);
CREATE INDEX idx_category ON notes(category);
CREATE INDEX idx_approval_status ON notes(approval_status);
CREATE INDEX idx_confidence_score ON notes(confidence_score);
```

These make queries fast, even with thousands of notes!

## Viewing Your Data

### Option 1: SQLite Browser (GUI)
```bash
# Install
brew install --cask db-browser-for-sqlite  # macOS
# Or download from: https://sqlitebrowser.org/

# Open
db-browser-for-sqlite data/notes.db
```

### Option 2: SQLite CLI
```bash
# Open database
sqlite3 data/notes.db

# Run queries
SELECT * FROM projects;
SELECT COUNT(*) FROM notes WHERE approval_status='approved';
SELECT category, COUNT(*) FROM notes GROUP BY category;

# Exit
.quit
```

### Option 3: Python Script
```python
import sqlite3
import pandas as pd

conn = sqlite3.connect('data/notes.db')
df = pd.read_sql_query("SELECT * FROM notes", conn)
print(df)
conn.close()
```

## Common Questions

**Q: Will my data survive if I close the app?**
A: Yes! It's saved to a file on disk.

**Q: What if I lose data/notes.db?**
A: Check `data/backups/` for recent backups.

**Q: Can I share my database with teammates?**
A: Yes, just share the `notes.db` file. Or use a cloud database.

**Q: How big can the database get?**
A: SQLite handles databases up to 281 TB! You're fine.

**Q: Is it secure?**
A: The file is on your computer. Encrypt the file or use proper database security for production.

## Pro Tips

1. **Regular Backups**: Use the "Create Backup" button in the sidebar
2. **Version Control**: Don't commit `notes.db` to git (it's in `.gitignore`)
3. **Cloud Deployment**: Use PostgreSQL or MySQL for Streamlit Cloud
4. **Analytics**: Export data to CSV from the "By Category" view
5. **Migrations**: The app handles schema changes automatically!

## Transaction Safety

SQLite uses **ACID** transactions:
- **Atomic**: All-or-nothing (no partial saves)
- **Consistent**: Database stays valid
- **Isolated**: Concurrent operations don't interfere
- **Durable**: Once committed, data persists

This means your data is safe even if the app crashes mid-operation!
