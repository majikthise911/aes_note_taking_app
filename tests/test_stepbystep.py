"""
Step-by-step test to isolate the crash.
"""
import streamlit as st

st.write("Step 1: Basic Streamlit works ✅")

try:
    st.write("Step 2: Importing DatabaseManager...")
    from database.db_manager import DatabaseManager
    st.write("✅ DatabaseManager imported")

    st.write("Step 3: Creating DatabaseManager instance...")
    db = DatabaseManager()
    st.write("✅ DatabaseManager initialized")

    st.write("Step 4: Getting projects...")
    projects = db.get_all_projects()
    st.write(f"✅ Found {len(projects)} projects")

    if projects:
        st.write(f"   Project: {projects[0].name} (ID: {projects[0].id})")

    st.write("Step 5: Importing XAIClient...")
    from api.xai_client import XAIClient
    st.write("✅ XAIClient imported")

    st.write("Step 6: Attempting XAIClient initialization...")
    try:
        xai = XAIClient()
        st.write("✅ XAIClient initialized")
    except Exception as e:
        st.warning(f"⚠️ XAIClient failed (expected): {e}")

    st.write("Step 7: Importing views...")
    from ui.input_view import render_input_view
    from ui.approval_view import render_approval_view
    from ui.daily_view import render_daily_view
    from ui.categorized_view import render_categorized_view
    st.write("✅ All views imported")

    st.success("🎉 All components loaded successfully!")

except Exception as e:
    st.error(f"❌ Error at current step: {e}")
    import traceback
    st.code(traceback.format_exc())
