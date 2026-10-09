"""
University Course Timetable Auto-Scheduler
Streamlit frontend -> n8n production webhook -> Python scheduler

Run:
    streamlit run frontend/app.py
"""

import os
import sys
from pathlib import Path

import pandas as pd
import requests
import streamlit as st


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from frontend.email_timetable import render_email_section


# ============================================================
# N8N PRODUCTION WEBHOOK
# ============================================================

# Override with N8N_SCHEDULE_WEBHOOK_URL in .env / environment if the
# n8n webhook path changes. Default matches n8n/n8n_streamlit_integration_v2.json.
N8N_WEBHOOK_URL = os.getenv(
    "N8N_SCHEDULE_WEBHOOK_URL",
    "http://localhost:5678/webhook/08190fdc-b0cf-4c0f-a7c0-b6c60e7595e2",
)

N8N_TIMEOUT_SECONDS = 180


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Auto-Scheduler",
    page_icon="📅",
    layout="wide",
)


# ============================================================
# HEADER
# ============================================================

st.title("📅 Auto-Scheduler")

st.caption(
    "Upload courses, select courses, generate a timetable "
    "through the n8n orchestration workflow, verify conflicts, "
    "and export the result."
)


# ============================================================
# SESSION STATE
# ============================================================

if "schedule_result" not in st.session_state:
    st.session_state.schedule_result = None

if "selected_courses" not in st.session_state:
    st.session_state.selected_courses = []

if "enrollment_overrides" not in st.session_state:
    st.session_state.enrollment_overrides = {}


# ============================================================
# COLUMN ALIASES
# ============================================================

COLUMN_ALIASES = {
    "course_id": [
        "course_id",
        "course id",
        "id",
    ],
    "course_code": [
        "course_code",
        "course code",
        "code",
        "course",
    ],
    "course_name": [
        "course_name",
        "course name",
        "title",
        "course title",
        "name",
    ],
    "instructor": [
        "instructor",
        "lecturer",
        "lecturer name",
        "teacher",
        "instructor name",
    ],
    "students": [
        "students",
        "student count",
        "number of students",
        "enrollment",
        "enrolment",
    ],
}


REQUIRED_FIELDS = {
    "course_id",
    "course_code",
    "course_name",
    "instructor",
    "students",
}


# ============================================================
# HELPERS
# ============================================================

def normalize_column_name(column):
    return (
        str(column)
        .strip()
        .lower()
        .replace("-", " ")
        .replace("_", " ")
    )


def clean_course_code(value):
    return str(value).strip().upper()


def detect_columns(columns):
    normalized = {
        normalize_column_name(column): column
        for column in columns
    }

    mapping = {}

    for internal_name, aliases in COLUMN_ALIASES.items():

        for alias in aliases:

            normalized_alias = normalize_column_name(alias)

            if normalized_alias in normalized:
                mapping[internal_name] = normalized[
                    normalized_alias
                ]
                break

    return mapping


def validate_and_normalize(courses, mapping):

    missing_fields = (
        REQUIRED_FIELDS
        - set(mapping.keys())
    )

    if missing_fields:
        return None, [
            "Missing required fields: "
            + ", ".join(sorted(missing_fields))
        ]

    normalized = pd.DataFrame()

    for internal_name in REQUIRED_FIELDS:

        source_column = mapping[internal_name]

        normalized[internal_name] = courses[
            source_column
        ]

    normalized["course_code"] = (
        normalized["course_code"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    normalized["course_name"] = (
        normalized["course_name"]
        .astype(str)
        .str.strip()
    )

    normalized["instructor"] = (
        normalized["instructor"]
        .astype(str)
        .str.strip()
    )

    normalized["students"] = pd.to_numeric(
        normalized["students"],
        errors="coerce",
    )

    errors = []

    if normalized["course_code"].isna().any():
        errors.append(
            "One or more courses have an empty course code."
        )

    if normalized["course_name"].isna().any():
        errors.append(
            "One or more courses have an empty course name."
        )

    if normalized["instructor"].isna().any():
        errors.append(
            "One or more courses have an empty instructor."
        )

    if normalized["students"].isna().any():
        errors.append(
            "One or more courses have an invalid student count."
        )

    if (normalized["students"] < 0).any():
        errors.append(
            "Student counts cannot be negative."
        )

    if normalized["course_code"].duplicated().any():
        errors.append(
            "Duplicate course codes were found."
        )

    return normalized, errors


def call_n8n_webhook(
    selected_courses,
    enrollment_overrides,
):
    """
    Send the scheduling request to the n8n production webhook.
    """

    payload = {
        "course_codes": selected_courses,
        "enrollment_overrides": enrollment_overrides,
    }

    response = requests.post(
        N8N_WEBHOOK_URL,
        json=payload,
        timeout=N8N_TIMEOUT_SECONDS,
    )

    response.raise_for_status()

    try:
        return response.json()

    except ValueError:
        return {
            "success": True,
            "raw_response": response.text,
        }
