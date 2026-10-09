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


# ============================================================
# STEP 1 — UPLOAD CSV
# ============================================================

st.header("1. Upload Course CSV")

uploaded_file = st.file_uploader(
    "Choose a course CSV file",
    type=["csv"],
)

if uploaded_file is None:

    st.info(
        "Upload a CSV file to begin."
    )

    st.stop()


# ============================================================
# READ CSV
# ============================================================

try:

    courses = pd.read_csv(uploaded_file)

except Exception as exc:

    st.error(
        "❌ Unable to read the CSV file."
    )

    st.exception(exc)

    st.stop()


st.success(
    f"CSV uploaded successfully — "
    f"{len(courses)} row(s)."
)


# ============================================================
# CSV PREVIEW
# ============================================================

with st.expander(
    "CSV Preview",
    expanded=True,
):

    st.dataframe(
        courses.head(20),
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# STEP 2 — COLUMN DETECTION
# ============================================================

st.header("2. Column Mapping")

column_mapping = detect_columns(
    courses.columns
)

mapping_rows = []

for internal_name in COLUMN_ALIASES:

    mapping_rows.append(
        {
            "Required Field": internal_name,
            "CSV Column": column_mapping.get(
                internal_name,
                "❌ Not found",
            ),
        }
    )


mapping_df = pd.DataFrame(
    mapping_rows
)

st.dataframe(
    mapping_df,
    use_container_width=True,
    hide_index=True,
)


# ============================================================
# STEP 3 — VALIDATION
# ============================================================

st.header("3. Validate Courses")

normalized_courses, validation_errors = (
    validate_and_normalize(
        courses,
        column_mapping,
    )
)


if validation_errors:

    st.error(
        "❌ CSV validation failed."
    )

    for error in validation_errors:
        st.warning(error)

    st.info(
        "Rename your CSV columns using one of "
        "the supported aliases shown above."
    )

    st.stop()


st.success(
    "✅ CSV structure and required values are valid."
)


# ============================================================
# COURSE SUMMARY
# ============================================================

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(
        "Courses",
        len(normalized_courses),
    )

with col2:

    st.metric(
        "Course Codes",
        normalized_courses[
            "course_code"
        ].nunique(),
    )

with col3:

    st.metric(
        "Instructors",
        normalized_courses[
            "instructor"
        ].nunique(),
    )

with col4:

    st.metric(
        "Students",
        int(
            normalized_courses[
                "students"
            ].sum()
        ),
    )


# ============================================================
# NORMALIZED DATA
# ============================================================

with st.expander(
    "View normalized course data"
):

    st.dataframe(
        normalized_courses,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# STEP 4 — COURSE SELECTION
# ============================================================

st.header("4. Select Courses")

st.write(
    "Choose the courses you want to include "
    "in this timetable."
)

course_codes = (
    normalized_courses[
        "course_code"
    ]
    .tolist()
)


course_labels = {}

for _, row in normalized_courses.iterrows():

    course_labels[
        row["course_code"]
    ] = (
        f'{row["course_code"]} — '
        f'{row["course_name"]}'
    )


selected_courses = st.multiselect(
    "Courses to schedule",
    options=course_codes,
    default=course_codes,
    format_func=lambda code: course_labels.get(
        code,
        code,
    ),
)


if not selected_courses:

    st.warning(
        "Select at least one course."
    )

    st.stop()


st.success(
    f"{len(selected_courses)} course(s) selected."
)


# ============================================================
# STEP 5 — ENROLLMENT OVERRIDES
# ============================================================

st.header("5. Enrollment")

st.caption(
    "You can override the enrollment before scheduling."
)


enrollment_overrides = {}


for course_code in selected_courses:

    row = normalized_courses[
        normalized_courses[
            "course_code"
        ] == course_code
    ].iloc[0]

    default_students = int(
        row["students"]
    )

    enrollment_overrides[
        course_code
    ] = st.number_input(
        f"{course_code} — {row['course_name']}",
        min_value=0,
        value=default_students,
        step=1,
        key=f"students_{course_code}",
    )


# ============================================================
# STEP 6 — GENERATE THROUGH N8N
# ============================================================

st.header("6. Generate Schedule")

st.write(
    "The selected courses will be sent through "
    "the n8n production workflow. n8n then calls "
    "the authoritative Python scheduling engine."
)


generate = st.button(
    "🚀 Generate Schedule",
    type="primary",
    use_container_width=True,
)


if generate:

    st.session_state.schedule_result = None

    with st.spinner(
        "Sending scheduling request through n8n..."
    ):

        try:

            result = call_n8n_webhook(
                selected_courses,
                enrollment_overrides,
            )

            st.session_state.schedule_result = result

            st.session_state.selected_courses = (
                selected_courses
            )

            st.session_state.enrollment_overrides = (
                enrollment_overrides
            )

        except requests.exceptions.Timeout:

            st.error(
                "❌ n8n timed out while generating the schedule."
            )

            st.info(
                "Check the n8n execution log and the "
                "Python Scheduler node."
            )

        except requests.exceptions.ConnectionError:

            st.error(
                "❌ Could not connect to n8n."
            )

            st.info(
                "Make sure n8n is running at "
                "http://localhost:5678."
            )

        except requests.exceptions.HTTPError as exc:

            st.error(
                "❌ n8n returned an HTTP error."
            )

            if exc.response is not None:

                st.code(
                    exc.response.text,
                    language="json",
                )

        except Exception as exc:

            st.error(
                "❌ Schedule generation failed."
            )

            st.exception(exc)


# ============================================================
# RESULTS
# ============================================================

result = st.session_state.schedule_result


if result is None:

    st.info(
        "Select your courses and click "
        "'Generate Schedule' to create a timetable."
    )

    st.stop()


# ============================================================
# STEP 7 — STATUS
# ============================================================

st.divider()

st.header("7. Schedule Result")


if result.get("success"):

    st.success(
        "✅ Schedule generated successfully."
    )

else:

    st.warning(
        "⚠️ Schedule generated with conflicts "
        "or unplaced courses."
    )


# ============================================================
# METRICS
# ============================================================

placed = result.get(
    "placed",
    [],
)

unplaced = result.get(
    "unplaced",
    [],
)

verification_errors = result.get(
    "verification_errors",
    [],
)

missing_courses = result.get(
    "missing_courses",
    [],
)


requested_courses = result.get(
    "requested_courses",
    selected_courses,
)


col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(
        "Requested",
        len(requested_courses),
    )

with col2:

    st.metric(
        "Placed",
        len(placed),
    )

with col3:

    st.metric(
        "Unplaced",
        len(unplaced),
    )

with col4:

    st.metric(
        "Verification Issues",
        len(verification_errors),
    )


# ============================================================
# N8N STATUS / MESSAGE
# ============================================================

if result.get("message"):

    st.info(
        str(result["message"])
    )


# ============================================================
# STEP 8 — TIMETABLE
# ============================================================

st.header("8. Timetable")


if placed:

    timetable_df = pd.DataFrame(
        placed
    )

    display_columns = [
        "course",
        "title",
        "lecturer",
        "day",
        "time",
        "room",
        "room_capacity",
        "timeslot_label",
    ]

    available_columns = [
        column
        for column in display_columns
        if column in timetable_df.columns
    ]

    st.dataframe(
        timetable_df[
            available_columns
        ],
        use_container_width=True,
        hide_index=True,
    )

else:

    st.info(
        "No courses were placed into the timetable."
    )


# ============================================================
# FILTERS
# ============================================================

if placed:

    st.subheader("Filter Timetable")

    filter_col1, filter_col2, filter_col3 = (
        st.columns(3)
    )

    with filter_col1:

        days = sorted(
            timetable_df[
                "day"
            ]
            .dropna()
            .unique()
            .tolist()
        )

        selected_days = st.multiselect(
            "Day",
            days,
            default=days,
        )

    with filter_col2:

        rooms = sorted(
            timetable_df[
                "room"
            ]
            .dropna()
            .unique()
            .tolist()
        )

        selected_rooms = st.multiselect(
            "Room",
            rooms,
            default=rooms,
        )

    with filter_col3:

        lecturers = sorted(
            timetable_df[
                "lecturer"
            ]
            .dropna()
            .unique()
            .tolist()
        )

        selected_lecturers = st.multiselect(
            "Lecturer",
            lecturers,
            default=lecturers,
        )

    filtered_df = timetable_df.copy()

    if selected_days:

        filtered_df = filtered_df[
            filtered_df[
                "day"
            ].isin(selected_days)
        ]

    if selected_rooms:

        filtered_df = filtered_df[
            filtered_df[
                "room"
            ].isin(selected_rooms)
        ]

    if selected_lecturers:

        filtered_df = filtered_df[
            filtered_df[
                "lecturer"
            ].isin(selected_lecturers)
        ]

    st.dataframe(
        filtered_df[
            available_columns
        ],
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# EXPORT
# ============================================================

st.header("9. Export")

if placed:

    csv_data = timetable_df[
        available_columns
    ].to_csv(
        index=False
    )

    st.download_button(
        "⬇️ Download Timetable CSV",
        data=csv_data,
        file_name="generated_timetable.csv",
        mime="text/csv",
        use_container_width=True,
    )

    render_email_section(placed)


# ============================================================
# UNPLACED COURSES
# ============================================================

if unplaced:

    st.divider()

    st.header("Unplaced Courses")

    st.dataframe(
        pd.DataFrame(unplaced),
        use_container_width=True,
        hide_index=True,
    )


if missing_courses:

    st.header("Missing Courses")

    st.warning(
        "These course codes were in the CSV but not found "
        "in the scheduling database."
    )

    st.dataframe(
        pd.DataFrame(missing_courses),
        use_container_width=True,
        hide_index=True,
    )


if verification_errors:

    st.header("Verification Issues")

    for error in verification_errors:

        st.error(str(error))


# ============================================================
# CONFLICT / AI REPORT
# ============================================================

if result.get("conflict_report") or result.get("ai_report"):

    st.header("Conflict Report")

    report = result.get("conflict_report") or result.get("ai_report")

    st.markdown(str(report))


# ============================================================
# DEBUG / REQUEST SUMMARY
# ============================================================

with st.expander(
    "Scheduling Request Details"
):

    st.write(
        "n8n Production Webhook:"
    )

    st.code(
        N8N_WEBHOOK_URL
    )

    st.write(
        "Selected courses:"
    )

    st.write(
        selected_courses
    )

    st.write(
        "Enrollment overrides:"
    )

    st.json(
        enrollment_overrides
    )
