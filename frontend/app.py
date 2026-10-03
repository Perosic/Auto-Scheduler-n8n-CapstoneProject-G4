"""
University Course Timetable Auto-Scheduler
P1 Streamlit Frontend

Workflow:
1. Upload CSV
2. Detect and validate columns
3. Select courses
4. Override enrollment
5. Generate schedule
6. View visual timetable
7. View detailed timetable
8. Filter results
9. Review conflicts/unplaced courses
10. Export timetable
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import streamlit as st

from algorithm.frontend_scheduler import run_scheduler_for_courses


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="University Course Scheduler",
    page_icon="📅",
    layout="wide",
)


# ============================================================
# HEADER
# ============================================================

st.title("📅 University Course Timetable Scheduler")

st.caption(
    "Upload courses, select what to schedule, generate a timetable, "
    "review conflicts, and export the result."
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
    """Normalize a CSV column name."""

    return (
        str(column)
        .strip()
        .lower()
        .replace("-", " ")
        .replace("_", " ")
    )


def detect_columns(columns):
    """Detect CSV columns using supported aliases."""

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
    """Validate uploaded CSV and return normalized data."""

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

        source_column = mapping[
            internal_name
        ]

        normalized[
            internal_name
        ] = courses[
            source_column
        ]

    # --------------------------------------------------------
    # Clean values
    # --------------------------------------------------------

    normalized[
        "course_code"
    ] = (
        normalized[
            "course_code"
        ]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    normalized[
        "course_name"
    ] = (
        normalized[
            "course_name"
        ]
        .astype(str)
        .str.strip()
    )

    normalized[
        "instructor"
    ] = (
        normalized[
            "instructor"
        ]
        .astype(str)
        .str.strip()
    )

    normalized[
        "students"
    ] = pd.to_numeric(
        normalized[
            "students"
        ],
        errors="coerce",
    )

    errors = []

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    if normalized[
        "course_code"
    ].isna().any():

        errors.append(
            "One or more courses have an empty course code."
        )

    if normalized[
        "course_name"
    ].isna().any():

        errors.append(
            "One or more courses have an empty course name."
        )

    if normalized[
        "instructor"
    ].isna().any():

        errors.append(
            "One or more courses have an empty instructor."
        )

    if normalized[
        "students"
    ].isna().any():

        errors.append(
            "One or more courses have an invalid student count."
        )

    if (
        normalized[
            "students"
        ] < 0
    ).any():

        errors.append(
            "Student counts cannot be negative."
        )

    if normalized[
        "course_code"
    ].duplicated().any():

        errors.append(
            "Duplicate course codes were found."
        )

    return normalized, errors


def clear_results():

    st.session_state.schedule_result = None
    st.session_state.selected_courses = []
    st.session_state.enrollment_overrides = {}


def time_sort_key(time_value):
    """Sort timetable times using the starting time."""

    try:

        start = str(
            time_value
        ).split("-")[0].strip()

        return pd.to_datetime(
            start,
            format="%H:%M:%S",
            errors="coerce",
        )

    except Exception:

        return pd.NaT


def build_timetable_grid(timetable_df):
    """
    Build a visual weekly timetable.

    Each row represents a time.
    Each column represents a day.
    """

    if timetable_df.empty:
        return pd.DataFrame()

    days_order = [
        "Mon",
        "Tue",
        "Wed",
        "Thu",
        "Fri",
        "Sat",
        "Sun",
    ]

    available_days = [
        day
        for day in days_order
        if day in timetable_df["day"].values
    ]

    if not available_days:
        available_days = sorted(
            timetable_df[
                "day"
            ].dropna().unique()
        )

    time_values = (
        timetable_df[
            "time"
        ]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    time_values = sorted(
        time_values,
        key=lambda value: (
            time_sort_key(value)
            if not pd.isna(
                time_sort_key(value)
            )
            else pd.Timestamp.max
        ),
    )

    grid = pd.DataFrame(
        "",
        index=time_values,
        columns=available_days,
    )

    for _, row in timetable_df.iterrows():

        day = row.get("day")
        time = row.get("time")

        if (
            day not in grid.columns
            or time not in grid.index
        ):
            continue

        course = row.get(
            "course",
            "",
        )

        title = row.get(
            "title",
            "",
        )

        room = row.get(
            "room",
            "",
        )

        lecturer = row.get(
            "lecturer",
            "",
        )

        grid.loc[
            time,
            day
        ] = (
            f"📚 {course}\n"
            f"{title}\n"
            f"🏫 {room}\n"
            f"👤 {lecturer}"
        )

    grid.index.name = "Time"

    return grid


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("Scheduler")

    st.write(
        "Upload a CSV and generate a university timetable."
    )

    st.divider()

    if st.button(
        "🗑️ Clear Schedule",
        use_container_width=True,
    ):

        clear_results()

        st.rerun()


# ============================================================
# STEP 1 — CSV UPLOAD
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

    courses = pd.read_csv(
        uploaded_file
    )

except Exception as exc:

    st.error(
        f"Unable to read the CSV: {exc}"
    )

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
                "Not found",
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
        "CSV validation failed."
    )

    for error in validation_errors:

        st.warning(error)

    st.info(
        "Rename your CSV columns using one of the "
        "supported aliases shown above."
    )

    st.stop()


st.success(
    "CSV structure and course data are valid."
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
    ].tolist()
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
# STEP 6 — GENERATE
# ============================================================

st.header("6. Generate Schedule")

st.write(
    "The selected courses will be matched against "
    "the scheduling database and processed by the "
    "DSATUR scheduler and room assignment system."
)


generate = st.button(
    "🚀 Generate Schedule",
    type="primary",
    use_container_width=True,
)


if generate:

    st.session_state.schedule_result = None

    with st.spinner(
        "Generating timetable..."
    ):

        try:

            result = run_scheduler_for_courses(
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

        except Exception as exc:

            st.error(
                "Schedule generation failed."
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
# RESULT DATA
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


# ============================================================
# SUMMARY METRICS
# ============================================================

rooms_used = len(
    {
        item.get("room")
        for item in placed
        if item.get("room")
    }
)

col1, col2, col3, col4, col5 = st.columns(5)

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
        "Rooms Used",
        rooms_used,
    )

with col5:

    st.metric(
        "Verification Issues",
        len(verification_errors),
    )


# ============================================================
# STEP 8 — VISUAL WEEKLY TIMETABLE
# ============================================================

st.header("8. Weekly Timetable")

if placed:

    timetable_df = pd.DataFrame(
        placed
    )

    visual_grid = build_timetable_grid(
        timetable_df
    )

    if not visual_grid.empty:

        st.caption(
            "Weekly view — each cell shows course, room, and lecturer."
        )

        st.dataframe(
            visual_grid,
            use_container_width=True,
            height=450,
        )

    else:

        st.info(
            "Unable to build the weekly timetable view."
        )

else:

    st.info(
        "No courses were placed into the timetable."
    )


# ============================================================
# STEP 9 — DETAILED TIMETABLE
# ============================================================

st.header("9. Detailed Timetable")

if placed:

    display_columns = [
        "course",
        "title",
        "lecturer",
        "day",
        "time",
        "room",
        "room_capacity",
    ]

    available_columns = [
        column
        for column in display_columns
        if column in timetable_df.columns
    ]


    # --------------------------------------------------------
    # FILTERS
    # --------------------------------------------------------

    st.subheader("🔎 Filters")

    filter_col1, filter_col2 = (
        st.columns(2)
    )

    filter_col3, filter_col4 = (
        st.columns(2)
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


    with filter_col4:

        courses_filter = sorted(
            timetable_df[
                "course"
            ]
            .dropna()
            .unique()
            .tolist()
        )

        selected_filter_courses = st.multiselect(
            "Course",
            courses_filter,
            default=courses_filter,
        )


    # --------------------------------------------------------
    # APPLY FILTERS
    # --------------------------------------------------------

    filtered_df = timetable_df.copy()


    if selected_days:

        filtered_df = filtered_df[
            filtered_df[
                "day"
            ].isin(
                selected_days
            )
        ]


    if selected_rooms:

        filtered_df = filtered_df[
            filtered_df[
                "room"
            ].isin(
                selected_rooms
            )
        ]


    if selected_lecturers:

        filtered_df = filtered_df[
            filtered_df[
                "lecturer"
            ].isin(
                selected_lecturers
            )
        ]


    if selected_filter_courses:

        filtered_df = filtered_df[
            filtered_df[
                "course"
            ].isin(
                selected_filter_courses
            )
        ]


    st.dataframe(
        filtered_df[
            available_columns
        ],
        use_container_width=True,
        hide_index=True,
    )


    st.caption(
        f"Showing {len(filtered_df)} of "
        f"{len(timetable_df)} scheduled course(s)."
    )


    # --------------------------------------------------------
    # DOWNLOAD
    # --------------------------------------------------------

    st.subheader("📥 Export")


    csv_data = filtered_df[
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


# ============================================================
# STEP 10 — UNPLACED COURSES
# ============================================================

if unplaced:

    st.divider()

    st.header("10. Unplaced Courses")

    st.warning(
        f"{len(unplaced)} course(s) could not be placed."
    )

    try:

        unplaced_df = pd.DataFrame(
            unplaced
        )

        st.dataframe(
            unplaced_df,
            use_container_width=True,
            hide_index=True,
        )

    except Exception:

        for course in unplaced:

            st.warning(
                str(course)
            )


# ============================================================
# STEP 11 — MISSING COURSES
# ============================================================

if missing_courses:

    st.divider()

    st.header("11. Courses Not Found")

    for course in missing_courses:

        st.warning(
            str(course)
        )


# ============================================================
# STEP 12 — VERIFICATION
# ============================================================

st.divider()

st.header("12. Verification")


if verification_errors:

    st.error(
        f"{len(verification_errors)} verification "
        "issue(s) detected."
    )

    for error in verification_errors:

        st.error(
            str(error)
        )

else:

    st.success(
        "✅ No verification errors reported."
    )


# ============================================================
# REQUEST SUMMARY
# ============================================================

with st.expander(
    "Scheduling Request Details"
):

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