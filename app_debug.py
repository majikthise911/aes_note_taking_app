"""
Debug version of the app with extensive error handling.
"""
import streamlit as st
from datetime import datetime

print("=" * 50)
print("STARTING APP DEBUG MODE")
print("=" * 50)

try:
    print("Step 1: Importing config...")
    from config.settings import PAGE_TITLE, PAGE_ICON, LAYOUT
    print("✅ Config imported")

    print("Step 2: Setting page config...")
    st.set_page_config(
        page_title=PAGE_TITLE,
        page_icon=PAGE_ICON,
        layout=LAYOUT,
        initial_sidebar_state="expanded",
    )
    print("✅ Page config set")

    print("Step 3: Importing DatabaseManager...")
    from database.db_manager import DatabaseManager
    print("✅ DatabaseManager imported")

    print("Step 4: Importing XAIClient...")
    from api.xai_client import XAIClient
    print("✅ XAIClient imported")

    print("Step 5: Importing logger...")
    from utils.logger import logger
    print("✅ Logger imported")

    print("Step 6: Importing views...")
    from ui.input_view import render_input_view
    from ui.approval_view import render_approval_view
    from ui.daily_view import render_daily_view
    from ui.categorized_view import render_categorized_view
    print("✅ All views imported")

    # Initialize session state
    print("Step 7: Initializing session state...")
    if "db_manager" not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
        print("✅ DatabaseManager initialized")

    if "xai_client" not in st.session_state:
        try:
            st.session_state.xai_client = XAIClient()
            print("✅ XAI client initialized")
        except Exception as e:
            print(f"⚠️ XAI client failed: {e}")
            st.session_state.xai_client = None

    if "current_user" not in st.session_state:
        st.session_state.current_user = "default_user"

    if "current_project_id" not in st.session_state:
        projects = st.session_state.db_manager.get_all_projects()
        if projects:
            st.session_state.current_project_id = projects[0].id
        else:
            try:
                default_proj = st.session_state.db_manager.get_project_by_name("Default Project")
                if default_proj:
                    st.session_state.current_project_id = default_proj.id
                else:
                    project_id = st.session_state.db_manager.create_project("Default Project")
                    st.session_state.current_project_id = project_id
                print(f"✅ Created/found project ID: {st.session_state.current_project_id}")
            except Exception as e:
                print(f"❌ Project error: {e}")
                st.session_state.current_project_id = None

    print("Step 8: Rendering UI...")

    # Sidebar
    with st.sidebar:
        st.title(f"{PAGE_ICON} {PAGE_TITLE}")
        st.markdown("---")

        st.subheader("Project")
        projects = st.session_state.db_manager.get_all_projects()

        if projects and st.session_state.current_project_id:
            project_names = [p.name for p in projects]
            st.write(f"**Current Project:** {project_names[0]}")
            st.caption(f"Project ID: {st.session_state.current_project_id}")

        st.markdown("---")
        st.write(f"**User:** {st.session_state.current_user}")
        st.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d')}")

    # Main content
    st.header("Debug Mode - App Loaded Successfully!")
    st.success("✅ All components initialized without errors")

    if st.session_state.current_project_id:
        st.info(f"Current Project ID: {st.session_state.current_project_id}")

        # Show some basic stats
        try:
            stats = st.session_state.db_manager.get_statistics(
                project_id=st.session_state.current_project_id
            )
            st.write("**Statistics:**", stats)
        except Exception as e:
            st.warning(f"Could not load stats: {e}")

    else:
        st.error("No project selected")

    st.markdown("---")
    st.write("If you see this message, the app is working! Now try running the normal `app.py`")

    print("✅ APP LOADED SUCCESSFULLY")

except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    st.error(f"Error loading app: {e}")
    st.code(traceback.format_exc())
