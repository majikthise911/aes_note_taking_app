"""
Project Notes Manager - Main Streamlit Application

A web-based note-taking application for project managers with automatic
note cleanup and categorization via xAI's Grok API.
"""
import streamlit as st
from datetime import datetime

from config.settings import PAGE_TITLE, PAGE_ICON, LAYOUT
from database.db_manager import DatabaseManager
from api.xai_client import XAIClient
from utils.logger import logger, log_user_action
from ui.input_view import render_input_view
from ui.approval_view import render_approval_view
from ui.daily_view import render_daily_view
from ui.categorized_view import render_categorized_view


# Page configuration
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout=LAYOUT,
    initial_sidebar_state="expanded",
)


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if "db_manager" not in st.session_state:
        st.session_state.db_manager = DatabaseManager()

    if "xai_client" not in st.session_state:
        try:
            st.session_state.xai_client = XAIClient()
        except ValueError as e:
            st.error(f"Failed to initialize xAI client: {e}")
            st.info("Please configure XAI_API_KEY in your .env file")
            st.session_state.xai_client = None

    if "current_user" not in st.session_state:
        st.session_state.current_user = "default_user"


def render_sidebar():
    """Render sidebar with app information and statistics."""
    with st.sidebar:
        st.title(f"{PAGE_ICON} {PAGE_TITLE}")
        st.markdown("---")

        # User info
        st.write(f"**User:** {st.session_state.current_user}")
        st.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d')}")

        st.markdown("---")

        # Statistics
        st.subheader("Statistics")
        try:
            stats = st.session_state.db_manager.get_statistics()

            # Notes by status
            if "by_status" in stats:
                st.write("**Notes by Status:**")
                for status, count in stats["by_status"].items():
                    st.write(f"- {status.capitalize()}: {count}")

            # Total categories with notes
            if "by_category" in stats:
                total_categories = len(stats["by_category"])
                st.write(f"**Categories Used:** {total_categories}")

        except Exception as e:
            st.error(f"Failed to load statistics: {e}")
            logger.error(f"Statistics error: {e}")

        st.markdown("---")

        # Quick actions
        st.subheader("Quick Actions")
        if st.button("Create Backup", use_container_width=True):
            try:
                backup_path = st.session_state.db_manager.create_backup()
                st.success(f"Backup created: {backup_path.name}")
                log_user_action(
                    st.session_state.current_user, "create_backup", str(backup_path)
                )
            except Exception as e:
                st.error(f"Backup failed: {e}")
                logger.error(f"Backup error: {e}")


def main():
    """Main application entry point."""
    initialize_session_state()
    render_sidebar()

    # Main content area with tabs
    tabs = st.tabs(["📝 New Note", "✅ Approve Notes", "📅 Daily View", "🗂️ By Category"])

    with tabs[0]:
        render_input_view(
            st.session_state.xai_client,
            st.session_state.db_manager,
            st.session_state.current_user,
        )

    with tabs[1]:
        render_approval_view(
            st.session_state.db_manager, st.session_state.current_user
        )

    with tabs[2]:
        render_daily_view(st.session_state.db_manager)

    with tabs[3]:
        render_categorized_view(st.session_state.db_manager)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Application error: {e}")
        logger.error(f"Application error: {e}", exc_info=True)
