"""
run.py

Authoritative scheduling pipeline.

The scheduler can optionally receive a list of course codes
from the Streamlit/n8n integration.

If course_codes is supplied:
    only those courses are scheduled.

If course_codes is None:
    the full database dataset is scheduled.

The Python scheduler remains the source of truth.
"""

import json


from algorithm.db_loader import load_data
from algorithm.graph import build_conflict_graph
from algorithm.dsatur import dsatur_schedule
from algorithm.room_assigner import assign_rooms
from algorithm.verifier import verify_schedule


# ------------------------------------------------------------
# Courses that are intentionally impossible in the test data.
# ------------------------------------------------------------

EXPECTED_UNPLACEABLE = {
    25,
    28,
    23,
}


def _normalise_course_codes(course_codes):
    """
    Convert incoming course codes into a normalized set.

    Example:

        ["csc101", " MTH101 "]

    becomes:

        {"CSC101", "MTH101"}
    """

    if course_codes is None:
        return None

    return {
        str(code)
        .strip()
        .upper()
        for code in course_codes
        if str(code).strip()
    }


def _filter_scheduler_data(
    data,
    course_codes,
    enrollment_overrides,
):
    """
    Restrict scheduler data to the courses selected by
    Streamlit.

    This is deliberately done before building the conflict
    graph so that the scheduler operates only on the requested
    courses.
    """

    requested_codes = _normalise_course_codes(
        course_codes
    )

    # --------------------------------------------------------
    # No filter supplied.
    #
    # This preserves the existing command-line behaviour:
    #
    #     python -m algorithm.run
    #
    # still schedules the entire database.
    # --------------------------------------------------------

    if requested_codes is None:

        selected_courses = list(
            data["courses"]
        )

    else:

        selected_courses = [

            course

            for course in data["courses"]

            if str(
                course.get("code", "")
            ).strip().upper()
            in requested_codes
        ]

    # --------------------------------------------------------
    # Apply enrollment overrides.
    # --------------------------------------------------------

    overrides = {}

    if isinstance(
        enrollment_overrides,
        dict
    ):

        for code, value in (
            enrollment_overrides.items()
        ):

            try:

                overrides[
                    str(code)
                    .strip()
                    .upper()
                ] = int(value)

            except (
                TypeError,
                ValueError
            ):

                # Ignore invalid override values rather
                # than corrupting scheduler data.
                continue

    for course in selected_courses:

        code = str(
            course.get("code", "")
        ).strip().upper()

        if code in overrides:

            course[
                "expected_enrolment"
            ] = overrides[code]

    # --------------------------------------------------------
    # Identify selected course IDs.
    #
    # Co-enrolment and allowed-timeslot tables use course_id.
    # --------------------------------------------------------

    selected_course_ids = {
        course["course_id"]
        for course in selected_courses
    }

    # --------------------------------------------------------
    # Filter co-enrolment relationships.
    #
    # Only relationships between selected courses matter.
    # --------------------------------------------------------

    selected_co_enrolments = [

        row

        for row in data["co_enrolments"]

        if (
            row["course_id_a"]
            in selected_course_ids
            and
            row["course_id_b"]
            in selected_course_ids
        )
    ]

    # --------------------------------------------------------
    # Filter allowed timeslots.
    # --------------------------------------------------------

    selected_allowed_timeslots = [

        row

        for row in data["allowed_timeslots"]

        if row["course_id"]
        in selected_course_ids
    ]

    # --------------------------------------------------------
    # Filter equipment requirements.
    # --------------------------------------------------------

    selected_equipment_reqs = [

        row

        for row in data["equipment_reqs"]

        if row["course_id"]
        in selected_course_ids
    ]

    # --------------------------------------------------------
    # Return filtered scheduling dataset.
    # --------------------------------------------------------

    filtered_data = dict(data)

    filtered_data[
        "courses"
    ] = selected_courses

    filtered_data[
        "co_enrolments"
    ] = selected_co_enrolments

    filtered_data[
        "allowed_timeslots"
    ] = selected_allowed_timeslots

    filtered_data[
        "equipment_reqs"
    ] = selected_equipment_reqs

    return filtered_data


def run_scheduler(
    course_codes=None,
    enrollment_overrides=None,
):
    """
    Run the authoritative scheduling pipeline.

    Parameters
    ----------
    course_codes:
        Optional list of course codes supplied by Streamlit.

        Example:

            [
                "CSC101",
                "MTH101",
                "PHY101"
            ]

        None means schedule the complete database dataset.

    enrollment_overrides:
        Optional dictionary mapping course codes to enrollment
        values.

        Example:

            {
                "CSC101": 30,
                "MTH101": 25
            }
    """

    # ========================================================
    # 1. Load database data
    # ========================================================

    data = load_data()

    # ========================================================
    # 2. Restrict data to the Streamlit selection
    # ========================================================

    data = _filter_scheduler_data(
        data,
        course_codes,
        enrollment_overrides
        or {}
    )

    # ========================================================
    # 3. Build conflict graph
    # ========================================================

    graph = build_conflict_graph(
        data["courses"],
        data["co_enrolments"],
    )

    # ========================================================
    # 4. Assign timeslots using DSATUR
    # ========================================================

    dsatur_result = dsatur_schedule(
        graph,
        data["courses"],
        data["timeslots"],
        data["allowed_timeslots"],
    )

    # ========================================================
    # 5. Assign rooms
    # ========================================================

    room_result = assign_rooms(
        dsatur_result["schedule"],
        data["courses"],
        data["rooms"],
        data["equipment_reqs"],
        data["room_equipment"],
    )

    # ========================================================
    # 6. Verify placed schedule
    # ========================================================

    verification = verify_schedule(
        room_result["placed"],
        data["courses"],
        graph,
        data["timeslots"],
        data["allowed_timeslots"],
        data["rooms"],
        data["equipment_reqs"],
        data["room_equipment"],
    )

    # ========================================================
    # 7. Combine all unplaced courses
    # ========================================================

    all_unplaced = (
        dsatur_result["unplaced"]
        +
        room_result["unplaced"]
    )

    # ========================================================
    # 8. Build clean placed output
    # ========================================================

    placed = []

    for item in room_result["placed"]:

        placed.append(
            {
                "course_id": item[
                    "course_id"
                ],

                "course": item[
                    "code"
                ],

                "title": item[
                    "title"
                ],

                "lecturer": item.get(
                    "lecturer"
                ),

                "day": item[
                    "day_of_week"
                ],

                "time": (
                    f"{item['start_time']} - "
                    f"{item['end_time']}"
                ),

                "timeslot_id": item[
                    "timeslot_id"
                ],

                "timeslot_label": item[
                    "timeslot_label"
                ],

                "room_id": item[
                    "room_id"
                ],

                "room": item[
                    "room_code"
                ],

                "room_capacity": item[
                    "room_capacity"
                ],
            }
        )

    # ========================================================
    # 9. Separate expected and unexpected unplaced courses
    # ========================================================

    expected_unplaced = []

    unexpected_unplaced = []

    for item in all_unplaced:

        course_id = item[
            "course_id"
        ]

        if course_id in EXPECTED_UNPLACEABLE:

            expected_unplaced.append(
                item
            )

        else:

            unexpected_unplaced.append(
                item
            )

    # ========================================================
    # 10. Determine authoritative scheduler status
    # ========================================================

    if verification["errors"]:

        status = "CONFLICT"

        success = False

    elif unexpected_unplaced:

        status = "CONFLICT"

        success = False

    elif all_unplaced:

        status = "SUCCESS_WITH_UNPLACED"

        success = True

    else:

        status = "SUCCESS"

        success = True

    # ========================================================
    # 11. Return final result
    # ========================================================

    return {
        "status": status,

        "success": success,

        "summary": {
            "total_courses": len(
                data["courses"]
            ),

            "placed_courses": len(
                placed
            ),

            "unplaced_courses": len(
                all_unplaced
            ),

            "expected_unplaced": len(
                expected_unplaced
            ),

            "unexpected_unplaced": len(
                unexpected_unplaced
            ),

            "verification_errors": len(
                verification["errors"]
            ),
        },

        "placed": placed,

        "unplaced": all_unplaced,

        "expected_unplaced": (
            expected_unplaced
        ),

        "unexpected_unplaced": (
            unexpected_unplaced
        ),

        "violations_count": (
            len(unexpected_unplaced)
            +
            len(verification["errors"])
        ),

        "verification_errors": (
            verification["errors"]
        ),
    }


def main():

    output = run_scheduler()

    print(
        json.dumps(
            output,
            indent=2,
            default=str,
        )
    )


if __name__ == "__main__":

    main()