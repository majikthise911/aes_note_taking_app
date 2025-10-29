"""
Note approval view for reviewing and approving processed notes.
"""
import streamlit as st
from typing import Optional

from database.db_manager import DatabaseManager
from database.models import Note
from config.categories import get_categories_list
from config.settings import NOTES_PER_PAGE
from utils.logger import logger, log_user_action


def render_approval_view(db_manager: DatabaseManager, username: str):
    """
    Render the note approval view.

    Args:
        db_manager: Database manager instance
        username: Current username
    """
    st.header("✅ Approve Notes")
    st.markdown("Review notes processed by AI and approve, edit, or reject them.")

    # Pagination setup
    if "approval_page" not in st.session_state:
        st.session_state.approval_page = 1

    # Get pending notes with pagination
    try:
        pending_notes, total_count = db_manager.get_pending_notes(
            page=st.session_state.approval_page,
            per_page=NOTES_PER_PAGE,
        )

        if total_count == 0:
            st.info("🎉 No notes pending approval! All caught up.")
            return

        # Display count and page info
        total_pages = (total_count + NOTES_PER_PAGE - 1) // NOTES_PER_PAGE
        st.write(
            f"**{total_count} note(s) pending approval** "
            f"(Page {st.session_state.approval_page} of {total_pages})"
        )

        # Display each pending note on current page
        for i, note in enumerate(pending_notes):
            render_note_approval_card(db_manager, note, i, username)

        # Pagination controls
        if total_pages > 1:
            render_pagination_controls(total_count, NOTES_PER_PAGE)

    except Exception as e:
        st.error(f"Failed to load pending notes: {e}")
        logger.error(f"Approval view error: {e}", exc_info=True)


def render_note_approval_card(
    db_manager: DatabaseManager, note: Note, index: int, username: str
):
    """
    Render an individual note approval card.

    Args:
        db_manager: Database manager
        note: Note to display
        index: Index for unique key generation
        username: Current username
    """
    with st.container():
        st.markdown(f"### Note #{note.id}")

        # Show comparison
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📄 Original")
            st.text_area(
                "Raw text:",
                value=note.raw_text,
                height=150,
                disabled=True,
                key=f"raw_{note.id}_{index}",
            )

        with col2:
            st.subheader("✨ Cleaned")
            cleaned_text = st.text_area(
                "Cleaned text:",
                value=note.cleaned_text or note.raw_text,
                height=150,
                key=f"cleaned_{note.id}_{index}",
                help="Edit if needed",
            )

        # Category and metadata
        col3, col4, col5 = st.columns(3)

        with col3:
            categories = get_categories_list()
            # Safely get category index, default to "General" (index 0) if invalid
            try:
                current_category_index = (
                    categories.index(note.category)
                    if note.category and note.category in categories
                    else 0
                )
            except ValueError:
                logger.warning(
                    f"Note #{note.id} has invalid category '{note.category}'. "
                    f"Defaulting to 'General'."
                )
                current_category_index = 0

            selected_category = st.selectbox(
                "Category:",
                options=categories,
                index=current_category_index,
                key=f"category_{note.id}_{index}",
            )

        with col4:
            st.text_input(
                "Date:",
                value=note.date or "",
                disabled=True,
                key=f"date_{note.id}_{index}",
            )

        with col5:
            st.text_input(
                "Time:",
                value=note.timestamp or "",
                disabled=True,
                key=f"time_{note.id}_{index}",
            )

        # Action buttons
        col_approve, col_reject, col_delete = st.columns([1, 1, 1])

        with col_approve:
            if st.button(
                "✅ Approve",
                key=f"approve_{note.id}_{index}",
                use_container_width=True,
                type="primary",
            ):
                approve_note(db_manager, note.id, cleaned_text, selected_category, username)

        with col_reject:
            if st.button(
                "❌ Reject",
                key=f"reject_{note.id}_{index}",
                use_container_width=True,
            ):
                reject_note(db_manager, note.id, username)

        with col_delete:
            if st.button(
                "🗑️ Delete",
                key=f"delete_{note.id}_{index}",
                use_container_width=True,
            ):
                delete_note(db_manager, note.id, username)

        st.markdown("---")


def approve_note(
    db_manager: DatabaseManager,
    note_id: int,
    cleaned_text: str,
    category: str,
    username: str,
):
    """
    Approve a note.

    Args:
        db_manager: Database manager
        note_id: Note ID
        cleaned_text: Updated cleaned text
        category: Updated category
        username: Current username
    """
    try:
        success = db_manager.update_note(
            note_id=note_id,
            cleaned_text=cleaned_text,
            category=category,
            approval_status="approved",
        )

        if success:
            st.success(f"✅ Note #{note_id} approved!")
            log_user_action(username, "approve_note", f"Note ID: {note_id}")
            st.rerun()
        else:
            st.error(f"Failed to approve note #{note_id}")

    except Exception as e:
        st.error(f"Error approving note: {e}")
        logger.error(f"Approval error: {e}", exc_info=True)


def reject_note(db_manager: DatabaseManager, note_id: int, username: str):
    """
    Reject a note.

    Args:
        db_manager: Database manager
        note_id: Note ID
        username: Current username
    """
    try:
        success = db_manager.update_note(
            note_id=note_id, approval_status="rejected"
        )

        if success:
            st.warning(f"❌ Note #{note_id} rejected")
            log_user_action(username, "reject_note", f"Note ID: {note_id}")
            st.rerun()
        else:
            st.error(f"Failed to reject note #{note_id}")

    except Exception as e:
        st.error(f"Error rejecting note: {e}")
        logger.error(f"Rejection error: {e}", exc_info=True)


def delete_note(db_manager: DatabaseManager, note_id: int, username: str):
    """
    Delete a note.

    Args:
        db_manager: Database manager
        note_id: Note ID
        username: Current username
    """
    try:
        success = db_manager.delete_note(note_id)

        if success:
            st.info(f"🗑️ Note #{note_id} deleted")
            log_user_action(username, "delete_note", f"Note ID: {note_id}")
            st.rerun()
        else:
            st.error(f"Failed to delete note #{note_id}")

    except Exception as e:
        st.error(f"Error deleting note: {e}")
        logger.error(f"Deletion error: {e}", exc_info=True)


def render_pagination_controls(total_count: int, per_page: int):
    """
    Render pagination controls for approval view.

    Args:
        total_count: Total number of items
        per_page: Items per page
    """
    total_pages = (total_count + per_page - 1) // per_page
    current_page = st.session_state.get("approval_page", 1)

    if total_pages <= 1:
        return

    st.markdown("---")
    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])

    with col1:
        if st.button(
            "⏮️ First", disabled=(current_page == 1), key="approval_first"
        ):
            st.session_state.approval_page = 1
            st.rerun()

    with col2:
        if st.button(
            "◀️ Prev", disabled=(current_page == 1), key="approval_prev"
        ):
            st.session_state.approval_page = max(1, current_page - 1)
            st.rerun()

    with col3:
        st.markdown(
            f"<div style='text-align: center; padding-top: 5px;'>Page {current_page} of {total_pages}</div>",
            unsafe_allow_html=True,
        )

    with col4:
        if st.button(
            "Next ▶️", disabled=(current_page >= total_pages), key="approval_next"
        ):
            st.session_state.approval_page = min(total_pages, current_page + 1)
            st.rerun()

    with col5:
        if st.button(
            "Last ⏭️", disabled=(current_page >= total_pages), key="approval_last"
        ):
            st.session_state.approval_page = total_pages
            st.rerun()
