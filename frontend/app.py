"""
Streamlit Dashboard - P1
CSV upload, flexible column mapping, validation,
scheduler integration, and timetable display.
"""

import pandas as pd
import streamlit as st

from algorithm.frontend_scheduler import run_scheduler_for_courses


st.set_page_config(
    page_title="Course Timetable Auto-Scheduler",
    layout="wide",
)


st.title("University Course Scheduler Dashboard")

st.caption(
    "P1 frontend — CSV upload, validation, scheduling, and timetable"
)


# -------------------------------------------------------------------
# Supported CSV column aliases
# -------------------------------------------------------------------

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
    """Map uploaded CSV columns to internal fields."""

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


# -------------------------------------------------------------------
# Page 1 - Upload
# -------------------------------------------------------------------

st.header("1. Upload Course CSV")

uploaded_file = st.file_uploader(
    "Choose a course CSV file",
    type=["csv"],
)


if uploaded_file is None:

    st.info(
        "Upload a CSV file to begin."
    )

else:

    try:

        courses = pd.read_csv(uploaded_file)

        st.success(
            f"CSV uploaded successfully: "
            f"{len(courses)} row(s) found."
        )

        # -----------------------------------------------------------
        # Preview
        # -----------------------------------------------------------

        st.subheader("CSV Preview")

        st.dataframe(
            courses.head(20),
            use_container_width=True,
        )

        # -----------------------------------------------------------
        # Detect columns
        # -----------------------------------------------------------

        column_mapping = detect_columns(
            courses.columns
        )

        st.subheader("Detected Columns")

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
                        else "Not found"
                    ),
                }
            )

        mapping_df = pd.DataFrame(mapping_rows)

        st.dataframe(
            mapping_df,
            use_container_width=True,
            hide_index=True,
        )

        # -----------------------------------------------------------
        # Required fields
        # -----------------------------------------------------------

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
                "The CSV is missing information required "
                "for scheduling: "
                + ", ".join(
                    sorted(missing_fields)
                )
            )

            st.info(
                "You can rename your CSV columns or "
                "use one of the supported column names "
                "shown above."
            )

        else:

            # -------------------------------------------------------
            # Normalize data
            # -------------------------------------------------------

            normalized_courses = pd.DataFrame()

            for internal_name in required_fields:

                source_column = column_mapping[
                    internal_name
                ]

                normalized_courses[
                    internal_name
                ] = courses[source_column]

            # -------------------------------------------------------
            # Clean course codes
            # -------------------------------------------------------

            normalized_courses[
                "course_code"
            ] = (
                normalized_courses[
                    "course_code"
                ]
                .astype(str)
                .str.strip()
                .str.upper()
            )

            # -------------------------------------------------------
            # Validate student counts
            # -------------------------------------------------------

            normalized_courses[
                "students"
            ] = pd.to_numeric(
                normalized_courses[
                    "students"
                ],
                errors="coerce",
            )

            validation_errors = []

            if normalized_courses[
                "course_code"
            ].isna().any():

                validation_errors.append(
                    "One or more courses have "
                    "an empty course code."
                )

            if normalized_courses[
                "course_name"
            ].isna().any():

                validation_errors.append(
                    "One or more courses have "
                    "an empty course name."
                )

            if normalized_courses[
                "instructor"
            ].isna().any():

                validation_errors.append(
                    "One or more courses have "
                    "an empty instructor."
                )

            if normalized_courses[
                "students"
            ].isna().any():

                validation_errors.append(
                    "One or more courses have "
                    "an invalid or empty student count."
                )

            if (
                normalized_courses[
                    "students"
                ]
                < 0
            ).any():

                validation_errors.append(
                    "Student counts cannot be negative."
                )

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

            # -------------------------------------------------------
            # Validation result
            # -------------------------------------------------------

            if validation_errors:

                st.error(
                    "CSV validation failed."
                )

                for error in validation_errors:

                    st.warning(error)

            else:

                st.success(
                    "CSV structure and required values "
                    "are valid."
                )

                # ---------------------------------------------------
                # Course summary
                # ---------------------------------------------------

                st.subheader(
                    "Course Summary"
                )

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

                # ---------------------------------------------------
                # Normalized data
                # ---------------------------------------------------

                st.subheader(
                    "Normalized Course Data"
                )

                st.dataframe(
                    normalized_courses,
                    use_container_width=True,
                    hide_index=True,
                )

                # ===================================================
                # P1 SCHEDULER
                # ===================================================

                st.divider()

                st.header(
                    "2. Generate Schedule"
                )

                st.write(
                    "The validated courses will be matched "
                    "against the PostgreSQL scheduling database "
                    "and processed by the existing scheduler."
                )

                generate_schedule = st.button(
                    "Generate Schedule",
                    type="primary",
                    use_container_width=True,
                )

                if generate_schedule:

                    course_codes = (
                        normalized_courses[
                            "course_code"
                        ]
                        .astype(str)
                        .str.strip()
                        .str.upper()
                        .tolist()
                    )

                    uploaded_enrolments = {
                        str(row["course_code"])
                        .strip()
                        .upper(): int(row["students"])
                        for _, row
                        in normalized_courses.iterrows()
                    }

                    with st.spinner(
                        "Generating timetable..."
                    ):

                        try:

                            result = (
                                run_scheduler_for_courses(
                                    course_codes,
                                    uploaded_enrolments,
                                )
                            )

                            st.session_state[
                                "schedule_result"
                            ] = result

                        except Exception as exc:

                            st.error(
                                "Unable to generate the schedule."
                            )

                            st.exception(exc)

                # ===================================================
                # DISPLAY SCHEDULE RESULT
                # ===================================================

                result = st.session_state.get(
                    "schedule_result"
                )

                if result is not None:

                    st.divider()

                    st.header(
                        "3. Schedule Result"
                    )

                    # ------------------------------------------------
                    # Status
                    # ------------------------------------------------

                    if result["success"]:

                        st.success(
                            "Schedule generated successfully."
                        )

                    else:

                        st.warning(
                            "Schedule generated with conflicts "
                            "or unplaced courses."
                        )

                    # ------------------------------------------------
                    # Metrics
                    # ------------------------------------------------

                    placed_count = len(
                        result["placed"]
                    )

                    unplaced_count = len(
                        result["unplaced"]
                    )

                    verification_count = len(
                        result[
                            "verification_errors"
                        ]
                    )

                    col1, col2, col3, col4 = st.columns(4)

                    with col1:

                        st.metric(
                            "Requested Courses",
                            len(
                                result[
                                    "requested_courses"
                                ]
                            ),
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

                    # ------------------------------------------------
                    # Timetable
                    # ------------------------------------------------

                    if result["placed"]:

                        st.subheader(
                            "Generated Timetable"
                        )

                        timetable_df = pd.DataFrame(
                            result["placed"]
                        )

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
                            for column
                            in display_columns
                            if column
                            in timetable_df.columns
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
                            "No courses were placed "
                            "into the timetable."
                        )

                    # ------------------------------------------------
                    # Unplaced courses
                    # ------------------------------------------------

                    if result["unplaced"]:

                        st.subheader(
                            "Unplaced Courses"
                        )

                        st.dataframe(
                            pd.DataFrame(
                                result[
                                    "unplaced"
                                ]
                            ),
                            use_container_width=True,
                            hide_index=True,
                        )

                    # ------------------------------------------------
                    # Verification errors
                    # ------------------------------------------------

                    if result[
                        "verification_errors"
                    ]:

                        st.subheader(
                            "Verification Errors"
                        )

                        for error in result[
                            "verification_errors"
                        ]:

                            st.error(
                                str(error)
                            )

                    # ------------------------------------------------
                    # Missing database courses
                    # ------------------------------------------------

                    if result[
                        "missing_courses"
                    ]:

                        st.subheader(
                            "Courses Not Found In Database"
                        )

                        for course in result[
                            "missing_courses"
                        ]:

                            st.warning(
                                course
                            )

    except Exception as exc:

        st.error(
            f"Unable to read the CSV: {exc}"
        )
