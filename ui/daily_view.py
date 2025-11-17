"""
Daily chronological view for approved notes.
"""
import streamlit as st
from datetime import datetime, timedelta
from typing import Optional

from database.db_manager import DatabaseManager
from config.settings import NOTES_PER_PAGE
from config.categories import get_categories_list
from utils.logger import logger


def render_daily_view(db_manager: DatabaseManager, project_id: int):
    """
    Render the daily chronological view.

    Args:
        db_manager: Database manager instance
        project_id: Current project ID
    """
    st.header("📅 Daily View")
    st.markdown("View all approved notes in chronological order by date.")

    # Search bar
    search_query = st.text_input(
        "🔍 Search notes:",
        placeholder="Search by keyword, phrase, or category...",
        key="daily_search",
        help="Search across note content and categories"
    )

    # Filters
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        date_from = st.date_input(
            "From Date:",
            value=datetime.now() - timedelta(days=30),
            max_value=datetime.now(),
            key="daily_date_from",
        )

    with col2:
        date_to = st.date_input(
            "To Date:",
            value=datetime.now(),
            max_value=datetime.now(),
            key="daily_date_to",
        )

    with col3:
        if st.button("Apply Filters", use_container_width=True, type="primary"):
            st.rerun()

    # Convert dates to strings
    date_from_str = date_from.strftime("%Y-%m-%d")
    date_to_str = date_to.strftime("%Y-%m-%d")

    # Pagination setup
    if "daily_page" not in st.session_state:
        st.session_state.daily_page = 1

    # Get notes (with search if query provided)
    try:
        if search_query and search_query.strip():
            # Use search method
            notes, total_count = db_manager.search_notes(
                search_query=search_query.strip(),
                page=st.session_state.daily_page,
                per_page=NOTES_PER_PAGE,
                approval_status="approved",
                project_id=project_id,
                date_from=date_from_str,
                date_to=date_to_str,
            )
        else:
            # Use regular pagination
            notes, total_count = db_manager.get_notes_paginated(
                page=st.session_state.daily_page,
                per_page=NOTES_PER_PAGE,
                approval_status="approved",
                project_id=project_id,
                date_from=date_from_str,
                date_to=date_to_str,
            )

        # Display count and export button
        col_count, col_export = st.columns([3, 1])
        with col_count:
            if search_query and search_query.strip():
                st.write(f"**Search results:** {total_count} notes matching '{search_query}'")
            else:
                st.write(f"**Total notes:** {total_count}")
        with col_export:
            if total_count > 0:
                # Get all notes for export (not just current page)
                if search_query and search_query.strip():
                    all_notes, _ = db_manager.search_notes(
                        search_query=search_query.strip(),
                        page=1,
                        per_page=10000,
                        approval_status="approved",
                        project_id=project_id,
                        date_from=date_from_str,
                        date_to=date_to_str,
                    )
                else:
                    all_notes, _ = db_manager.get_notes_paginated(
                        page=1,
                        per_page=10000,  # Large number to get all notes
                        approval_status="approved",
                        project_id=project_id,
                        date_from=date_from_str,
                        date_to=date_to_str,
                    )
                markdown_export = generate_daily_markdown_export(all_notes, date_from_str, date_to_str)
                st.download_button(
                    label="📥 Export to Markdown",
                    data=markdown_export,
                    file_name=f"daily_notes_{date_from_str}_to_{date_to_str}.md",
                    mime="text/markdown",
                    use_container_width=True,
                )

        if total_count == 0:
            st.info("No approved notes found in the selected date range.")
            return

        # Display notes
        render_notes_list(notes, db_manager)

        # Pagination controls
        render_pagination(total_count, NOTES_PER_PAGE, "daily_page")

    except Exception as e:
        st.error(f"Failed to load notes: {e}")
        logger.error(f"Daily view error: {e}", exc_info=True)


def render_notes_list(notes: list, db_manager: DatabaseManager):
    """
    Render a list of notes with edit and delete options.

    Args:
        notes: List of Note instances
        db_manager: Database manager instance
    """
    # Group notes by date
    notes_by_date = {}
    for note in notes:
        date = note.date or "Unknown Date"
        if date not in notes_by_date:
            notes_by_date[date] = []
        notes_by_date[date].append(note)

    # Display notes grouped by date
    for date, date_notes in notes_by_date.items():
        with st.expander(f"📅 **{date}** ({len(date_notes)} notes)", expanded=True):
            for note in date_notes:
                col1, col2, col3 = st.columns([6, 1, 1])

                with col1:
                    timestamp_str = note.timestamp or 'N/A'
                    st.markdown(f"**{timestamp_str}**")
                    st.markdown(note.cleaned_text)
                    st.caption(f"Category: {note.category} | ID: {note.id}")

                with col2:
                    if st.button("✏️ Edit", key=f"edit_daily_{note.id}", use_container_width=True):
                        st.session_state[f"editing_note_{note.id}"] = True
                        st.rerun()

                with col3:
                    if st.button("🗑️ Delete", key=f"delete_daily_{note.id}", use_container_width=True):
                        if db_manager.delete_note(note.id):
                            st.success(f"Deleted note {note.id}")
                            logger.info(f"Deleted note {note.id} from daily view")
                            st.rerun()
                        else:
                            st.error("Failed to delete note")

                # Show edit form if editing
                if st.session_state.get(f"editing_note_{note.id}", False):
                    render_edit_form(note, db_manager)

                st.markdown("---")


def render_pagination(total_count: int, per_page: int, session_key: str):
    """
    Render pagination controls.

    Args:
        total_count: Total number of items
        per_page: Items per page
        session_key: Session state key for current page
    """
    total_pages = (total_count + per_page - 1) // per_page
    current_page = st.session_state.get(session_key, 1)

    if total_pages <= 1:
        return

    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])

    with col1:
        if st.button("⏮️ First", disabled=(current_page == 1), key=f"{session_key}_first"):
            st.session_state[session_key] = 1
            st.rerun()

    with col2:
        if st.button("◀️ Prev", disabled=(current_page == 1), key=f"{session_key}_prev"):
            st.session_state[session_key] = max(1, current_page - 1)
            st.rerun()

    with col3:
        st.markdown(
            f"<div style='text-align: center; padding-top: 5px;'>Page {current_page} of {total_pages}</div>",
            unsafe_allow_html=True,
        )

    with col4:
        if st.button("Next ▶️", disabled=(current_page >= total_pages), key=f"{session_key}_next"):
            st.session_state[session_key] = min(total_pages, current_page + 1)
            st.rerun()

    with col5:
        if st.button("Last ⏭️", disabled=(current_page >= total_pages), key=f"{session_key}_last"):
            st.session_state[session_key] = total_pages
            st.rerun()


def render_edit_form(note, db_manager: DatabaseManager):
    """
    Render an edit form for a note.

    Args:
        note: Note instance to edit
        db_manager: Database manager instance
    """
    with st.form(key=f"edit_form_{note.id}"):
        st.subheader(f"Edit Note #{note.id}")

        # Edit fields
        new_text = st.text_area(
            "Note Text",
            value=note.cleaned_text or note.raw_text,
            height=100,
            key=f"edit_text_{note.id}"
        )

        categories = get_categories_list()
        current_category_index = categories.index(note.category) if note.category in categories else 0
        new_category = st.selectbox(
            "Category",
            options=categories,
            index=current_category_index,
            key=f"edit_category_{note.id}"
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("💾 Save Changes", use_container_width=True):
                if db_manager.update_note(
                    note_id=note.id,
                    cleaned_text=new_text,
                    category=new_category
                ):
                    st.success("Note updated successfully!")
                    logger.info(f"Updated note {note.id}")
                    # Clear editing state
                    del st.session_state[f"editing_note_{note.id}"]
                    st.rerun()
                else:
                    st.error("Failed to update note")

        with col2:
            if st.form_submit_button("❌ Cancel", use_container_width=True):
                # Clear editing state
                del st.session_state[f"editing_note_{note.id}"]
                st.rerun()


def generate_daily_markdown_export(notes: list, date_from: str, date_to: str) -> str:
    """
    Generate markdown export of daily notes suitable for OneNote.

    Args:
        notes: List of Note instances
        date_from: Start date string
        date_to: End date string

    Returns:
        Markdown formatted string
    """
    # Header
    markdown = f"# Daily Notes Export\n\n"
    markdown += f"**Date Range:** {date_from} to {date_to}\n\n"
    markdown += f"**Total Notes:** {len(notes)}\n\n"
    markdown += f"**Exported:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    markdown += "---\n\n"

    # Group notes by date
    notes_by_date = {}
    for note in notes:
        date = note.date or "Unknown Date"
        if date not in notes_by_date:
            notes_by_date[date] = []
        notes_by_date[date].append(note)

    # Format notes by date
    for date in sorted(notes_by_date.keys(), reverse=True):
        date_notes = notes_by_date[date]
        markdown += f"## {date}\n\n"
        markdown += f"*{len(date_notes)} notes*\n\n"

        for note in date_notes:
            timestamp_str = (note.timestamp or 'N/A').strip()
            markdown += f"### {timestamp_str}\n\n"
            markdown += f"**Category:** {note.category}\n\n"
            markdown += f"{note.cleaned_text}\n\n"
            markdown += "---\n\n"

    return markdown
