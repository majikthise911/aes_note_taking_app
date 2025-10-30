"""
Daily chronological view for approved notes.
"""
import streamlit as st
from datetime import datetime, timedelta
from typing import Optional

from database.db_manager import DatabaseManager
from config.settings import NOTES_PER_PAGE
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

    # Get notes
    try:
        notes, total_count = db_manager.get_notes_paginated(
            page=st.session_state.daily_page,
            per_page=NOTES_PER_PAGE,
            approval_status="approved",
            project_id=project_id,
            date_from=date_from_str,
            date_to=date_to_str,
        )

        # Display count
        st.write(f"**Total notes:** {total_count}")

        if total_count == 0:
            st.info("No approved notes found in the selected date range.")
            return

        # Display notes
        render_notes_list(notes)

        # Pagination controls
        render_pagination(total_count, NOTES_PER_PAGE, "daily_page")

    except Exception as e:
        st.error(f"Failed to load notes: {e}")
        logger.error(f"Daily view error: {e}", exc_info=True)


def render_notes_list(notes: list):
    """
    Render a list of notes.

    Args:
        notes: List of Note instances
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
                col1, col2 = st.columns([4, 1])

                with col1:
                    st.markdown(f"**{note.timestamp or 'N/A'}** - {note.cleaned_text}")

                with col2:
                    st.caption(f"Category: {note.category}")

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
