"""
Streamlit Dashboard (P1)
Person E – CSV upload + calendar / schedule view

This is intentionally minimal so the P0 n8n-native HTML path remains the core demo.
"""
import streamlit as st

st.set_page_config(page_title="Course Timetable Auto-Scheduler", layout="wide")

st.title("University Course Scheduler Dashboard")
st.caption("P1 front-end · Core timetable is produced by the n8n HTML path (P0)")

st.info(
    "CSV upload and interactive calendar view will be implemented here. "
    "Until then, use the n8n-native HTML timetable as the primary demo surface."
)

# Placeholder for future CSV upload
uploaded = st.file_uploader("Upload course CSV (coming soon)", type=["csv"], disabled=True)

if uploaded:
    st.write("File received – processing not yet implemented.")
