"""
Rejected notes view - shows notes that were rejected during approval.
"""
import streamlit as st
from typing import Optional

from database.db_manager import DatabaseManager
from config.settings import NOTES_PER_PAGE
from utils.logger import logger, log_user_action


def render_rejected_view(db_manager: DatabaseManager, current_user: str, project_id: int):
    """
    Render the rejected notes view.

    Args:
        db_manager: Database manager instance
        current_user: Current username
        project_id: Current project ID
    """
    st.header("🗑️ Rejected Notes")
    st.markdown("Review notes that were rejected during approval. You can restore or permanently delete them.")

    # Get rejected notes
    try:
        with st.spinner("Loading rejected notes..."):
            # Query for rejected notes
            notes, total_count = db_manager.get_notes_paginated(
                page=1,
                per_page=100,
                approval_status="rejected",
                project_id=project_id,
            )

        if total_count == 0:
            st.success("✅ No rejected notes! You've kept your notes clean.")
            st.info("💡 **What happens to rejected notes?**\n"
                    "- They're marked as 'rejected' but NOT deleted\n"
                    "- They don't show up in Daily or Category views\n"
                    "- You can review them here and restore if needed\n"
                    "- Use the 'Permanently Delete' button to remove them")
            return

        # Display count
        st.write(f"**Total rejected notes:** {total_count}")
        st.markdown("---")

        # Display each rejected note
        for i, note in enumerate(notes):
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])

                with col1:
                    st.markdown(f"**Note #{note.id}** - *{note.category}*")
                    st.write(note.cleaned_text or note.raw_text)
                    st.caption(f"Date: {note.date} | Time: {note.timestamp}")

                with col2:
                    if st.button("♻️ Restore", key=f"restore_{note.id}", use_container_width=True):
                        try:
                            db_manager.update_note(note_id=note.id, approval_status="pending")
                            st.success(f"✅ Note #{note.id} restored to approval queue")
                            log_user_action(current_user, "restore_note", f"Note ID: {note.id}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to restore: {e}")
                            logger.error(f"Restore error: {e}", exc_info=True)

                with col3:
                    if st.button("🗑️ Delete", key=f"delete_{note.id}", use_container_width=True, type="secondary"):
                        try:
                            db_manager.delete_note(note.id)
                            st.warning(f"🗑️ Note #{note.id} permanently deleted")
                            log_user_action(current_user, "permanently_delete_note", f"Note ID: {note.id}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to delete: {e}")
                            logger.error(f"Delete error: {e}", exc_info=True)

                # Show raw text in expander
                with st.expander("View Original Note"):
                    st.text(note.raw_text)

                st.markdown("---")

        # Bulk actions
        st.markdown("### Bulk Actions")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("♻️ Restore All", type="primary"):
                try:
                    for note in notes:
                        db_manager.update_note(note_id=note.id, approval_status="pending")
                    st.success(f"✅ Restored {len(notes)} notes to approval queue")
                    log_user_action(current_user, "bulk_restore", f"Restored {len(notes)} notes")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to restore all: {e}")
                    logger.error(f"Bulk restore error: {e}", exc_info=True)

        with col2:
            if st.button("🗑️ Delete All Permanently", type="secondary"):
                st.warning("⚠️ This will permanently delete all rejected notes!")
                if st.button("Yes, Delete All (Cannot be undone)", type="secondary"):
                    try:
                        for note in notes:
                            db_manager.delete_note(note.id)
                        st.success(f"🗑️ Permanently deleted {len(notes)} notes")
                        log_user_action(current_user, "bulk_delete", f"Deleted {len(notes)} notes")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to delete all: {e}")
                        logger.error(f"Bulk delete error: {e}", exc_info=True)

    except Exception as e:
        st.error(f"Failed to load rejected notes: {e}")
        logger.error(f"Rejected view error: {e}", exc_info=True)
