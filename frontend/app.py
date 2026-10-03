"""
P1 Streamlit Scheduler Dashboard

Features:
- CSV upload
- Flexible column mapping
- CSV validation
- Course selection
- Enrollment overrides
- Scheduler integration
- Friendly scheduler errors
- Timetable display
- Unplaced/conflict display
- Verification results
- CSV export
"""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st


# ============================================================
# PROJECT IMPORT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from algorithm.frontend_scheduler import run_scheduler_for_courses


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="University Course Scheduler",
    page_icon="📅",
    layout="wide",
)


# ============================================================
# HEADER
# ============================================================

st.title("📅 University Course Scheduler")

st.caption(
    "P1 Streamlit Scheduler — upload courses, select courses, "
    "generate a timetable, verify conflicts, and export results."
)


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


# ============================================================
# HELPERS
# ============================================================

def normalize_column_name(column):
    """Normalize a CSV column name for matching."""
    return (
        str(column)
        .strip()
        .lower()
        .replace("-", " ")
        .replace("_", " ")
    )


def detect_columns(columns):
    """Detect internal fields from flexible CSV column names."""

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


def clean_course_code(value):
    """Normalize course codes."""
    return str(value).strip().upper()


# ============================================================
# SESSION STATE
# ============================================================

if "normalized_courses" not in st.session_state:
    st.session_state.normalized_courses = None

if "schedule_result" not in st.session_state:
    st.session_state.schedule_result = None


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

    st.error("❌ Unable to read the CSV file.")

    st.warning(str(exc))

    st.stop()


st.success(
    f"CSV uploaded successfully: "
    f"{len(courses)} row(s) found."
)


# ============================================================
# CSV PREVIEW
# ============================================================

st.subheader("CSV Preview")

st.dataframe(
    courses.head(20),
    use_container_width=True,
    hide_index=True,
)


# ============================================================
# STEP 2 — COLUMN DETECTION
# ============================================================

st.header("2. Detect CSV Columns")

column_mapping = detect_columns(
    courses.columns
)


mapping_rows = []

for internal_name in COLUMN_ALIASES:

    source_column = column_mapping.get(
        internal_name
    )

    mapping_rows.append(
        {
            "Required Field": internal_name,
            "CSV Column": (
                source_column
                if source_column
                else "❌ Not found"
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


required_fields = {
    "course_id",
    "course_code",
    "course_name",
    "instructor",
    "students",
}


missing_fields = (
    required_fields
    - set(column_mapping.keys())
)


if missing_fields:

    st.error(
        "❌ CSV validation failed."
    )

    st.warning(
        "Missing required fields: "
        + ", ".join(
            sorted(missing_fields)
        )
    )

    st.info(
        "Rename your CSV columns using one of the "
        "supported names shown above."
    )

    st.stop()


# ============================================================
# NORMALIZE DATA
# ============================================================

normalized_courses = pd.DataFrame()


for internal_name in required_fields:

    source_column = column_mapping[
        internal_name
    ]

    normalized_courses[
        internal_name
    ] = courses[source_column]


# Normalize course codes

normalized_courses[
    "course_code"
] = normalized_courses[
    "course_code"
].apply(
    clean_course_code
)


# ============================================================
# VALUE VALIDATION
# ============================================================

validation_errors = []


if normalized_courses[
    "course_code"
].isna().any():

    validation_errors.append(
        "One or more courses have an empty course code."
    )


if normalized_courses[
    "course_name"
].isna().any():

    validation_errors.append(
        "One or more courses have an empty course name."
    )


if normalized_courses[
    "instructor"
].isna().any():

    validation_errors.append(
        "One or more courses have an empty instructor."
    )


if normalized_courses[
    "students"
].isna().any():

    validation_errors.append(
        "One or more courses have an empty student count."
    )


# Convert students to numeric

try:

    normalized_courses[
        "students"
    ] = pd.to_numeric(
        normalized_courses["students"]
    )

except Exception:

    validation_errors.append(
        "Student counts must be numeric."
    )


# Duplicate course codes

duplicate_codes = (
    normalized_courses[
        "course_code"
    ]
    .duplicated()
)


if duplicate_codes.any():

    validation_errors.append(
        "Duplicate course codes were found."
    )


# ============================================================
# SHOW VALIDATION ERRORS
# ============================================================

if validation_errors:

    st.error(
        "❌ CSV validation failed."
    )

    for error in validation_errors:

        st.warning(
            error
        )

    st.stop()


st.success(
    "✅ CSV structure and required values are valid."
)


# Save normalized data

st.session_state.normalized_courses = (
    normalized_courses.copy()
)


# ============================================================
# COURSE SUMMARY
# ============================================================

st.subheader("Course Summary")


col1, col2, col3 = st.columns(3)


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


all_course_codes = (
    normalized_courses[
        "course_code"
    ]
    .tolist()
)


selected_courses = st.multiselect(
    "Choose courses to include in the timetable",
    options=all_course_codes,
    default=all_course_codes,
)


if not selected_courses:

    st.warning(
        "Please select at least one course."
    )

    st.stop()


# ============================================================
# SELECTED COURSE DATA
# ============================================================

selected_df = normalized_courses[
    normalized_courses[
        "course_code"
    ].isin(selected_courses)
].copy()


st.write(
    f"Selected **{len(selected_df)}** course(s)."
)


# ============================================================
# STEP 5 — ENROLLMENT OVERRIDES
# ============================================================

st.header("5. Enrollment Overrides")

st.caption(
    "Optional: change the expected enrollment for individual courses "
    "before generating the schedule."
)


enrollment_overrides = {}


for _, row in selected_df.iterrows():

    code = row["course_code"]

    default_students = int(
        row["students"]
    )

    override = st.number_input(
        f"{code} — {row['course_name']}",
        min_value=1,
        value=default_students,
        step=1,
        key=f"enrollment_{code}",
    )

    if override != default_students:

        enrollment_overrides[
            code
        ] = override


# ============================================================
# STEP 6 — GENERATE SCHEDULE
# ============================================================

st.header("6. Generate Schedule")


generate = st.button(
    "🚀 Generate Schedule",
    type="primary",
    use_container_width=True,
)


if generate:

    st.session_state.schedule_result = None

    with st.spinner(
        "Generating timetable and verifying constraints..."
    ):

        try:

            result = run_scheduler_for_courses(
                selected_courses,
                enrollment_overrides,
            )

            st.session_state.schedule_result = result

        except ValueError as exc:

            st.error(
                "❌ Schedule generation failed"
            )

            st.warning(
                str(exc)
            )

            st.info(
                "Please remove invalid course codes from "
                "the CSV or select only courses available "
                "in the scheduling database."
            )

            st.stop()

        except Exception as exc:

            st.error(
                "❌ An unexpected error occurred "
                "while generating the schedule."
            )

            st.exception(exc)

            st.stop()


# ============================================================
# DISPLAY RESULT
# ============================================================

result = st.session_state.schedule_result


if result is None:

    st.info(
        "Select your courses and click "
        "**Generate Schedule**."
    )

    st.stop()


# ============================================================
# RESULT SUMMARY
# ============================================================

st.header("7. Schedule Results")


requested_count = len(
    result.get(
        "requested_courses",
        []
    )
)

placed = result.get(
    "placed",
    []
)

unplaced = result.get(
    "unplaced",
    []
)

verification_errors = result.get(
    "verification_errors",
    []
)


placed_count = len(
    placed
)

unplaced_count = len(
    unplaced
)

verification_count = len(
    verification_errors
)


col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "Requested",
        requested_count,
    )


with col2:

    st.metric(
        "Placed",
        placed_count,
    )


with col3:

    st.metric(
        "Unplaced",
        unplaced_count,
    )


with col4:

    st.metric(
        "Verification Issues",
        verification_count,
    )


# ============================================================
# SUCCESS / CONFLICT STATUS
# ============================================================

if result.get("success"):

    st.success(
        "✅ Schedule generated successfully. "
        "All selected courses were placed and verification passed."
    )

else:

    st.warning(
        "⚠️ Schedule generated with conflicts or unplaced courses."
    )


# ============================================================
# TIMETABLE
# ============================================================

st.header("8. Timetable")


if placed:

    timetable_df = pd.DataFrame(
        placed
    )

    display_columns = [
        column
        for column in [
            "course",
            "title",
            "lecturer",
            "day",
            "time",
            "room",
            "room_capacity",
            "timeslot_label",
        ]
        if column in timetable_df.columns
    ]

    st.dataframe(
        timetable_df[
            display_columns
        ],
        use_container_width=True,
        hide_index=True,
    )

else:

    st.info(
        "No courses were placed."
    )


# ============================================================
# UNPLACED COURSES
# ============================================================

st.header("9. Unplaced Courses")


if unplaced:

    unplaced_df = pd.DataFrame(
        unplaced
    )

    st.error(
        f"{len(unplaced)} course(s) could not be placed."
    )

    st.dataframe(
        unplaced_df,
        use_container_width=True,
        hide_index=True,
    )

else:

    st.success(
        "✅ No unplaced courses."
    )


# ============================================================
# VERIFICATION
# ============================================================

st.header("10. Verification")


if verification_errors:

    st.error(
        "Verification found issues."
    )

    for error in verification_errors:

        st.warning(
            str(error)
        )

else:

    st.success(
        "✅ Independent schedule verification passed."
    )


# ============================================================
# EXPORT
# ============================================================

st.header("11. Export")


if placed:

    export_df = pd.DataFrame(
        placed
    )

    csv_data = export_df.to_csv(
        index=False
    )

    st.download_button(
        label="⬇️ Download Timetable CSV",
        data=csv_data,
        file_name="generated_timetable.csv",
        mime="text/csv",
        use_container_width=True,
    )