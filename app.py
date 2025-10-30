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
from ui.rejected_view import render_rejected_view


# Page configuration
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout=LAYOUT,
    initial_sidebar_state="expanded",
)


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    try:
        if "db_manager" not in st.session_state:
            st.session_state.db_manager = DatabaseManager()
            logger.info("DatabaseManager initialized")

        if "xai_client" not in st.session_state:
            try:
                st.session_state.xai_client = XAIClient()
                logger.info("XAI client initialized")
            except Exception as e:
                logger.warning(f"XAI client initialization failed: {e}")
                st.session_state.xai_client = None
                st.session_state.xai_client_error = str(e)

        if "current_user" not in st.session_state:
            st.session_state.current_user = "default_user"

        if "current_project_id" not in st.session_state:
            # Try to get the first project, or create a default one
            projects = st.session_state.db_manager.get_all_projects()
            logger.info(f"Found {len(projects)} projects")

            if projects:
                st.session_state.current_project_id = projects[0].id
                logger.info(f"Using existing project ID: {projects[0].id}")
            else:
                # Create a default project
                try:
                    # Check if Default Project already exists
                    default_proj = st.session_state.db_manager.get_project_by_name("Default Project")
                    if default_proj:
                        st.session_state.current_project_id = default_proj.id
                        logger.info(f"Found Default Project with ID: {default_proj.id}")
                    else:
                        project_id = st.session_state.db_manager.create_project("Default Project")
                        st.session_state.current_project_id = project_id
                        logger.info(f"Created Default Project with ID: {project_id}")
                except Exception as e:
                    logger.error(f"Failed to create/get default project: {e}", exc_info=True)
                    st.session_state.current_project_id = None
    except Exception as e:
        logger.error(f"Error in initialize_session_state: {e}", exc_info=True)
        raise


def render_sidebar():
    """Render sidebar with app information and statistics."""
    with st.sidebar:
        st.title(f"{PAGE_ICON} {PAGE_TITLE}")
        st.markdown("---")

        # Project Management
        st.subheader("Project")

        try:
            projects = st.session_state.db_manager.get_all_projects()

            if projects:
                # Create a simple list of project names for display
                project_names = [p.name for p in projects]
                project_ids = [p.id for p in projects]

                # Find current project index
                try:
                    current_index = project_ids.index(st.session_state.current_project_id)
                except (ValueError, AttributeError):
                    current_index = 0
                    st.session_state.current_project_id = project_ids[0]

                selected_index = st.selectbox(
                    "Select Project",
                    range(len(project_names)),
                    format_func=lambda i: project_names[i],
                    index=current_index,
                    key="project_selector"
                )
                st.session_state.current_project_id = project_ids[selected_index]
            else:
                st.warning("No projects found. Please create a project below.")
        except Exception as e:
            st.error(f"Error loading projects: {e}")
            logger.error(f"Project loading error: {e}", exc_info=True)

        # Add new project
        with st.expander("Add New Project"):
            new_project_name = st.text_input("Project Name", key="new_project_name")
            if st.button("Create Project", use_container_width=True):
                if new_project_name.strip():
                    try:
                        project_id = st.session_state.db_manager.create_project(new_project_name.strip())
                        st.session_state.current_project_id = project_id
                        st.success(f"Created project: {new_project_name}")
                        log_user_action(
                            st.session_state.current_user, "create_project", new_project_name
                        )
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to create project: {e}")
                        logger.error(f"Project creation error: {e}")
                else:
                    st.warning("Please enter a project name")

        st.markdown("---")

        # User info
        st.write(f"**User:** {st.session_state.current_user}")
        st.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d')}")

        st.markdown("---")

        # Statistics (filtered by current project)
        st.subheader("Statistics")
        try:
            stats = st.session_state.db_manager.get_statistics(
                project_id=st.session_state.current_project_id
            )

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
    try:
        logger.info("Starting main function")
        initialize_session_state()
        logger.info("Session state initialized")

        render_sidebar()
        logger.info("Sidebar rendered")

        # Check if a project is selected
        if not st.session_state.get("current_project_id"):
            st.error("No project selected. Please create a project in the sidebar.")
            st.info("Click on 'Add New Project' in the sidebar to get started.")
            return

        # Main content area with tabs
        tabs = st.tabs(["📝 New Note", "✅ Approve Notes", "📅 Daily View", "🗂️ By Category", "🗑️ Rejected"])

        with tabs[0]:
            render_input_view(
                st.session_state.xai_client,
                st.session_state.db_manager,
                st.session_state.current_user,
                st.session_state.current_project_id,
            )

        with tabs[1]:
            render_approval_view(
                st.session_state.db_manager,
                st.session_state.current_user,
                st.session_state.current_project_id,
            )

        with tabs[2]:
            render_daily_view(
                st.session_state.db_manager,
                st.session_state.current_project_id,
            )

        with tabs[3]:
            render_categorized_view(
                st.session_state.db_manager,
                st.session_state.current_project_id,
            )

        with tabs[4]:
            render_rejected_view(
                st.session_state.db_manager,
                st.session_state.current_user,
                st.session_state.current_project_id,
            )

        logger.info("Main function completed successfully")
    except Exception as e:
        logger.error(f"Error in main function: {e}", exc_info=True)
        st.error(f"An error occurred: {e}")
        st.error("Check the logs/app.log file for more details.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Application error: {e}")
        logger.error(f"Application error: {e}", exc_info=True)
