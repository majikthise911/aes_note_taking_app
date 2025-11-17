"""
Categorized view for approved notes organized by project categories.
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional

from database.db_manager import DatabaseManager
from config.categories import get_categories_list
from config.settings import NOTES_PER_PAGE
from utils.logger import logger
import re


def render_categorized_view(db_manager: DatabaseManager, project_id: int):
    """
    Render the categorized view.

    Args:
        db_manager: Database manager instance
        project_id: Current project ID
    """
    st.header("🗂️ View by Category")
    st.markdown("Browse notes organized by project categories.")

    # Search bar
    search_query = st.text_input(
        "🔍 Search notes:",
        placeholder="Search by keyword, phrase, or category...",
        key="cat_search",
        help="Search across note content and categories"
    )

    # Special view toggle for action items
    show_action_items_grouped = st.toggle(
        "📋 Show Action Items Grouped by Technical Category",
        help="Groups action items by their related technical domain (Engineering, Budget, Schedule, etc.)"
    )

    if show_action_items_grouped:
        render_action_items_grouped_view(db_manager, project_id)
        return

    # Filters
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

    categories = ["All Categories"] + get_categories_list()

    with col1:
        selected_category = st.selectbox(
            "Category:",
            options=categories,
            key="cat_filter",
        )

    with col2:
        date_from = st.date_input(
            "From Date:",
            value=datetime.now() - timedelta(days=30),
            max_value=datetime.now(),
            key="cat_date_from",
        )

    with col3:
        date_to = st.date_input(
            "To Date:",
            value=datetime.now(),
            max_value=datetime.now(),
            key="cat_date_to",
        )

    with col4:
        if st.button("Apply", use_container_width=True, type="primary"):
            st.rerun()

    # Convert dates to strings
    date_from_str = date_from.strftime("%Y-%m-%d")
    date_to_str = date_to.strftime("%Y-%m-%d")

    # Pagination setup
    if "cat_page" not in st.session_state:
        st.session_state.cat_page = 1

    # Get notes based on filter (with search if query provided)
    try:
        category_filter = None if selected_category == "All Categories" else selected_category

        if search_query and search_query.strip():
            # Use search method
            notes, total_count = db_manager.search_notes(
                search_query=search_query.strip(),
                page=st.session_state.cat_page,
                per_page=NOTES_PER_PAGE,
                approval_status="approved",
                project_id=project_id,
                date_from=date_from_str,
                date_to=date_to_str,
                category=category_filter,
            )
        else:
            # Use regular pagination
            notes, total_count = db_manager.get_notes_paginated(
                page=st.session_state.cat_page,
                per_page=NOTES_PER_PAGE,
                approval_status="approved",
                project_id=project_id,
                date_from=date_from_str,
                date_to=date_to_str,
                category=category_filter,
            )

        # Display count
        if search_query and search_query.strip():
            st.write(f"**Search results:** {total_count} notes matching '{search_query}'")
        else:
            st.write(f"**Total notes:** {total_count}")

        if total_count == 0:
            st.info("No approved notes found with the selected filters.")
            return

        # Display view selector
        view_type = st.radio(
            "View as:",
            options=["Grouped by Category", "Table View"],
            horizontal=True,
        )

        if view_type == "Grouped by Category":
            # Add export button for grouped view
            if st.button("📥 Export Grouped View to Markdown", use_container_width=False):
                # Get all notes for export
                if search_query and search_query.strip():
                    all_notes, _ = db_manager.search_notes(
                        search_query=search_query.strip(),
                        page=1,
                        per_page=10000,
                        approval_status="approved",
                        project_id=project_id,
                        date_from=date_from_str,
                        date_to=date_to_str,
                        category=category_filter,
                    )
                else:
                    all_notes, _ = db_manager.get_notes_paginated(
                        page=1,
                        per_page=10000,
                        approval_status="approved",
                        project_id=project_id,
                        date_from=date_from_str,
                        date_to=date_to_str,
                        category=category_filter,
                    )
                markdown_export = generate_category_markdown_export(all_notes, category_filter or "All Categories")
                st.download_button(
                    label="Download Markdown",
                    data=markdown_export,
                    file_name=f"notes_by_category_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown",
                )

            render_grouped_view(notes, db_manager)
        else:
            render_table_view(notes, db_manager)

        # Pagination controls
        render_pagination_controls(total_count, NOTES_PER_PAGE)

    except Exception as e:
        st.error(f"Failed to load notes: {e}")
        logger.error(f"Categorized view error: {e}", exc_info=True)


def render_grouped_view(notes: list, db_manager: DatabaseManager):
    """
    Render notes grouped by category with edit and delete options.

    Args:
        notes: List of Note instances
        db_manager: Database manager instance
    """
    # Group notes by category
    notes_by_category = {}
    for note in notes:
        category = note.category or "Uncategorized"
        if category not in notes_by_category:
            notes_by_category[category] = []
        notes_by_category[category].append(note)

    # Display notes grouped by category
    for category, cat_notes in sorted(notes_by_category.items()):
        with st.expander(f"📁 **{category}** ({len(cat_notes)} notes)", expanded=True):
            for note in cat_notes:
                col1, col2, col3 = st.columns([6, 1, 1])

                with col1:
                    date_str = note.date or 'N/A'
                    timestamp_str = note.timestamp or ''
                    if timestamp_str:
                        st.markdown(f"**{date_str} {timestamp_str}**")
                    else:
                        st.markdown(f"**{date_str}**")
                    st.markdown(note.cleaned_text)
                    st.caption(f"Note ID: {note.id}")

                with col2:
                    if st.button("✏️ Edit", key=f"edit_cat_{note.id}", use_container_width=True):
                        st.session_state[f"editing_note_{note.id}"] = True
                        st.rerun()

                with col3:
                    if st.button("🗑️ Delete", key=f"delete_cat_{note.id}", use_container_width=True):
                        if db_manager.delete_note(note.id):
                            st.success(f"Deleted note {note.id}")
                            logger.info(f"Deleted note {note.id} from categorized view")
                            st.rerun()
                        else:
                            st.error("Failed to delete note")

                # Show edit form if editing
                if st.session_state.get(f"editing_note_{note.id}", False):
                    render_edit_form(note, db_manager)

                st.markdown("---")


def render_table_view(notes: list, db_manager: DatabaseManager):
    """
    Render notes in a table format with edit and delete options.

    Args:
        notes: List of Note instances
        db_manager: Database manager instance
    """
    # Convert notes to dataframe
    data = []
    for note in notes:
        data.append(
            {
                "ID": note.id,
                "Date": note.date,
                "Time": note.timestamp,
                "Category": note.category,
                "Note": note.cleaned_text,
            }
        )

    df = pd.DataFrame(data)

    # Display dataframe
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "ID": st.column_config.NumberColumn("ID", width="small"),
            "Date": st.column_config.TextColumn("Date", width="small"),
            "Time": st.column_config.TextColumn("Time", width="small"),
            "Category": st.column_config.TextColumn("Category", width="medium"),
            "Note": st.column_config.TextColumn("Note", width="large"),
        },
    )

    # Export option
    if st.button("📥 Export to CSV", use_container_width=False):
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"notes_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )

    st.markdown("---")
    st.subheader("Edit/Delete Notes")

    # Show edit/delete options for individual notes
    note_ids = [note.id for note in notes]
    selected_note_id = st.selectbox(
        "Select a note to edit or delete:",
        options=note_ids,
        format_func=lambda id: f"Note #{id} - {next((n.cleaned_text[:50] + '...' if len(n.cleaned_text) > 50 else n.cleaned_text) for n in notes if n.id == id)}",
        key="table_note_selector"
    )

    if selected_note_id:
        selected_note = next((n for n in notes if n.id == selected_note_id), None)
        if selected_note:
            col1, col2 = st.columns(2)

            with col1:
                if st.button("✏️ Edit Selected Note", use_container_width=True):
                    st.session_state[f"editing_note_{selected_note_id}"] = True
                    st.rerun()

            with col2:
                if st.button("🗑️ Delete Selected Note", use_container_width=True, type="secondary"):
                    if db_manager.delete_note(selected_note_id):
                        st.success(f"Deleted note {selected_note_id}")
                        logger.info(f"Deleted note {selected_note_id} from table view")
                        st.rerun()
                    else:
                        st.error("Failed to delete note")

            # Show edit form if editing
            if st.session_state.get(f"editing_note_{selected_note_id}", False):
                render_edit_form(selected_note, db_manager)


def render_action_items_grouped_view(db_manager: DatabaseManager, project_id: int):
    """
    Render action items grouped by their related technical category.

    Args:
        db_manager: Database manager instance
        project_id: Current project ID
    """
    st.subheader("📋 Action Items by Technical Category")
    st.markdown("Action items organized by their related technical domain.")

    try:
        # Get all action items
        action_items = db_manager.get_notes_by_category(
            category="Action Items",
            approval_status="approved",
            project_id=project_id
        )

        if not action_items:
            st.info("No approved action items found.")
            return

        # Category keywords for classification
        category_keywords = {
            "Engineering": ["engineer", "structural", "design", "technical", "civil", "electrical"],
            "Schedule": ["schedule", "timeline", "deadline", "meeting", "date", "week", "month"],
            "Budget & Pricing": ["budget", "cost", "pricing", "dollar", "$", "price", "payment"],
            "Contracting": ["contract", "vendor", "supplier", "agreement", "procurement"],
            "Environmental": ["environmental", "biological", "cultural", "permitting", "epa"],
            "Interconnection": ["interconnection", "utility", "grid", "substation"],
            "Land": ["land", "property", "parcel", "lease", "easement"],
            "Geotech": ["geotech", "soil", "foundation", "boring"],
            "General": []  # Catch-all
        }

        # Categorize action items by keywords
        grouped_items = {cat: [] for cat in category_keywords.keys()}

        for note in action_items:
            text = (note.cleaned_text or note.raw_text).lower()
            matched = False

            # Check each category's keywords
            for category, keywords in category_keywords.items():
                if category == "General":
                    continue
                if any(keyword in text for keyword in keywords):
                    grouped_items[category].append(note)
                    matched = True
                    break

            # If no match, add to General
            if not matched:
                grouped_items["General"].append(note)

        # Display grouped action items
        st.write(f"**Total Action Items:** {len(action_items)}")
        st.markdown("---")

        for category, items in grouped_items.items():
            if not items:
                continue

            with st.expander(f"**{category}** ({len(items)} action items)", expanded=True):
                for note in items:
                    col1, col2 = st.columns([5, 1])

                    with col1:
                        st.markdown(f"**{note.date} {note.timestamp}**")
                        st.write(note.cleaned_text or note.raw_text)

                        # Highlight assignee if found
                        text = note.cleaned_text or note.raw_text
                        assignees = re.findall(r'(AES|Pre|JC|[A-Z][a-z]+ [A-Z][a-z]+)\s+(?:to|needs to|must)', text)
                        if assignees:
                            st.caption(f"👤 Assigned to: {', '.join(set(assignees))}")

                    with col2:
                        st.caption(f"Note #{note.id}")

                    st.markdown("---")

    except Exception as e:
        st.error(f"Failed to load grouped action items: {e}")
        logger.error(f"Grouped action items error: {e}", exc_info=True)


def render_pagination_controls(total_count: int, per_page: int):
    """
    Render pagination controls for categorized view.

    Args:
        total_count: Total number of items
        per_page: Items per page
    """
    total_pages = (total_count + per_page - 1) // per_page
    current_page = st.session_state.get("cat_page", 1)

    if total_pages <= 1:
        return

    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])

    with col1:
        if st.button("⏮️ First", disabled=(current_page == 1), key="cat_first"):
            st.session_state.cat_page = 1
            st.rerun()

    with col2:
        if st.button("◀️ Prev", disabled=(current_page == 1), key="cat_prev"):
            st.session_state.cat_page = max(1, current_page - 1)
            st.rerun()

    with col3:
        st.markdown(
            f"<div style='text-align: center; padding-top: 5px;'>Page {current_page} of {total_pages}</div>",
            unsafe_allow_html=True,
        )

    with col4:
        if st.button("Next ▶️", disabled=(current_page >= total_pages), key="cat_next"):
            st.session_state.cat_page = min(total_pages, current_page + 1)
            st.rerun()

    with col5:
        if st.button("Last ⏭️", disabled=(current_page >= total_pages), key="cat_last"):
            st.session_state.cat_page = total_pages
            st.rerun()


def render_edit_form(note, db_manager: DatabaseManager):
    """
    Render an edit form for a note.

    Args:
        note: Note instance to edit
        db_manager: Database manager instance
    """
    with st.form(key=f"edit_form_cat_{note.id}"):
        st.subheader(f"Edit Note #{note.id}")

        # Edit fields
        new_text = st.text_area(
            "Note Text",
            value=note.cleaned_text or note.raw_text,
            height=100,
            key=f"edit_text_cat_{note.id}"
        )

        categories = get_categories_list()
        current_category_index = categories.index(note.category) if note.category in categories else 0
        new_category = st.selectbox(
            "Category",
            options=categories,
            index=current_category_index,
            key=f"edit_category_cat_{note.id}"
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


def generate_category_markdown_export(notes: list, category_filter: str) -> str:
    """
    Generate markdown export of notes grouped by category suitable for OneNote.

    Args:
        notes: List of Note instances
        category_filter: Category filter applied

    Returns:
        Markdown formatted string
    """
    # Header
    markdown = f"# Notes by Category Export\n\n"
    markdown += f"**Category Filter:** {category_filter}\n\n"
    markdown += f"**Total Notes:** {len(notes)}\n\n"
    markdown += f"**Exported:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    markdown += "---\n\n"

    # Group notes by category
    notes_by_category = {}
    for note in notes:
        category = note.category or "Uncategorized"
        if category not in notes_by_category:
            notes_by_category[category] = []
        notes_by_category[category].append(note)

    # Format notes by category
    for category in sorted(notes_by_category.keys()):
        cat_notes = notes_by_category[category]
        markdown += f"## {category}\n\n"
        markdown += f"*{len(cat_notes)} notes*\n\n"

        for note in cat_notes:
            # Build date/time header properly
            date_str = note.date or 'N/A'
            timestamp_str = note.timestamp or ''
            if timestamp_str:
                markdown += f"**{date_str} {timestamp_str.strip()}**\n\n"
            else:
                markdown += f"**{date_str}**\n\n"

            markdown += f"{note.cleaned_text}\n\n"
            markdown += "---\n\n"

    return markdown
