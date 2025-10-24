"""
Note input view for entering new notes.
"""
import streamlit as st
from datetime import datetime
from typing import Optional

from api.xai_client import XAIClient
from database.db_manager import DatabaseManager
from utils.validators import validate_note_text, sanitize_input
from utils.logger import logger, log_user_action, log_api_call


def render_input_view(
    xai_client: Optional[XAIClient], db_manager: DatabaseManager, username: str
):
    """
    Render the note input view.

    Args:
        xai_client: xAI API client instance
        db_manager: Database manager instance
        username: Current username
    """
    st.header("📝 Create New Note")
    st.markdown("Enter your project notes below. They will be cleaned and categorized automatically.")

    # Check if API client is available
    if xai_client is None:
        st.error("⚠️ xAI API client not configured. Please check your API key in .env file.")
        st.info("You can still enter notes manually, but they won't be automatically processed.")

    # Note input form
    with st.form("note_input_form", clear_on_submit=True):
        raw_notes = st.text_area(
            "Enter your notes:",
            height=200,
            placeholder="Example: Reviewed Primoris bid. Cost at 61.2 cents/W. Need to follow up with engineering team about structural design by EOW.",
            help="Enter one or more project notes. They will be automatically cleaned and categorized.",
        )

        col1, col2 = st.columns([1, 4])
        with col1:
            submit_button = st.form_submit_button("Submit Notes", use_container_width=True, type="primary")
        with col2:
            st.caption("Notes will be processed and sent to approval queue")

    # Process submission
    if submit_button:
        # Validate input
        is_valid, error_msg = validate_note_text(raw_notes)
        if not is_valid:
            st.error(f"❌ {error_msg}")
            return

        # Sanitize input
        raw_notes = sanitize_input(raw_notes)

        # Process with API if available
        if xai_client:
            process_with_api(xai_client, db_manager, raw_notes, username)
        else:
            # Manual entry without API
            save_manual_note(db_manager, raw_notes, username)


def process_with_api(
    xai_client: XAIClient, db_manager: DatabaseManager, raw_notes: str, username: str
):
    """
    Process notes through the API.

    Args:
        xai_client: xAI API client
        db_manager: Database manager
        raw_notes: Raw note text
        username: Current username
    """
    with st.spinner("🤖 Processing notes with AI..."):
        start_time = datetime.now()

        try:
            # Call API
            cleaned_notes = xai_client.process_notes(raw_notes)
            duration = (datetime.now() - start_time).total_seconds()

            log_api_call("xai_process_notes", "success", duration)
            log_user_action(username, "submit_notes", f"Processed {len(cleaned_notes)} notes")

            # Save to database
            saved_count = 0
            for note in cleaned_notes:
                try:
                    note_id = db_manager.insert_note(
                        raw_text=raw_notes,
                        cleaned_text=note["cleaned_text"],
                        category=note["category"],
                        date=note["date"],
                        timestamp=note["timestamp"],
                        approval_status="pending",
                    )
                    saved_count += 1
                    logger.info(f"Note {note_id} created and pending approval")

                except Exception as e:
                    logger.error(f"Failed to save note: {e}")
                    st.error(f"Failed to save a note: {e}")

            # Show success
            if saved_count > 0:
                st.success(
                    f"✅ Successfully processed {saved_count} note(s)! "
                    f"Go to the 'Approve Notes' tab to review and approve them."
                )

                # Show preview of processed notes
                with st.expander("📋 Preview Processed Notes", expanded=False):
                    for i, note in enumerate(cleaned_notes, 1):
                        st.markdown(f"**Note {i}:**")
                        st.info(f"**Category:** {note['category']}")
                        st.write(note["cleaned_text"])
                        st.markdown("---")

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            log_api_call("xai_process_notes", "failure", duration, str(e))
            st.error(f"❌ Failed to process notes: {e}")
            logger.error(f"API processing error: {e}", exc_info=True)

            # Offer manual entry as fallback
            st.info("💡 You can manually enter notes without API processing using the manual entry option below.")
            if st.button("Save as Manual Note"):
                save_manual_note(db_manager, raw_notes, username)


def save_manual_note(db_manager: DatabaseManager, raw_notes: str, username: str):
    """
    Save a note manually without API processing.

    Args:
        db_manager: Database manager
        raw_notes: Raw note text
        username: Current username
    """
    try:
        current_date = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%H:%M:%S")

        note_id = db_manager.insert_note(
            raw_text=raw_notes,
            cleaned_text=raw_notes,  # Use raw text as cleaned text
            category="General",  # Default category
            date=current_date,
            timestamp=current_time,
            approval_status="pending",
        )

        st.success(
            f"✅ Note saved manually (ID: {note_id})! "
            f"Go to 'Approve Notes' to categorize and approve it."
        )
        log_user_action(username, "manual_note_entry", f"Note ID: {note_id}")

    except Exception as e:
        st.error(f"❌ Failed to save note: {e}")
        logger.error(f"Manual note save error: {e}", exc_info=True)
