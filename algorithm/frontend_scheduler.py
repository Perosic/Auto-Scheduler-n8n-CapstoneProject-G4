"""
P1 frontend scheduler adapter.

Connects the Streamlit CSV frontend to the existing P0 scheduler.

Important behavior:
- Valid database courses are scheduled normally.
- Unknown CSV course codes are reported separately.
- Unknown courses NEVER enter the P0 scheduler.
- One invalid CSV course must NOT prevent valid courses from scheduling.
"""

from algorithm.db_loader import load_data
from algorithm.graph import build_conflict_graph
from algorithm.dsatur import dsatur_schedule
from algorithm.room_assigner import assign_rooms
from algorithm.verifier import verify_schedule


def _normalize_code(value):
    """Normalize a course code for reliable matching."""
    if value is None:
        return ""

    return str(value).strip().upper()


def _build_course_lookup(courses):
    """Build normalized course-code -> course lookup."""
    return {
        _normalize_code(course.get("code")): course
        for course in courses
        if _normalize_code(course.get("code"))
    }


def _build_selected_courses(
    requested_codes,
    db_by_code,
    uploaded_enrolments,
):
    """
    Build only courses that actually exist in the scheduling database.

    Unknown CSV courses are deliberately excluded.
    """

    selected_courses = []

    for code in sorted(requested_codes):

        course = db_by_code.get(code)

        if course is None:
            continue

        selected_course = dict(course)

        if code in uploaded_enrolments:
            try:
                selected_course["expected_enrolment"] = int(
                    uploaded_enrolments[code]
                )
            except (TypeError, ValueError):
                # Keep database value if CSV override is invalid.
                pass

        selected_courses.append(selected_course)

    return selected_courses


def _make_missing_course_record(code):
    """Create a UI-friendly record for a missing course."""
    return {
        "course_id": None,
        "code": code,
        "title": "Course not found in scheduling database",
        "reason_code": "COURSE_NOT_FOUND",
        "detail": (
            "The course code from the CSV does not exist "
            "in the scheduling database."
        ),
    }


def run_scheduler_for_courses(
    course_codes,
    uploaded_enrolments=None,
):
    """
    Run the existing scheduler for courses selected from the P1 CSV.

    Parameters
    ----------
    course_codes:
        List of course codes from the uploaded CSV.

    uploaded_enrolments:
        Optional dictionary:

        {
            "CSC101": 55,
            "CSC201": 45
        }

    Returns
    -------
    dict
        Scheduling result for the Streamlit frontend.
    """

    # =========================================================
    # 1. Load P0 scheduling data
    # =========================================================

    data = load_data()

    # =========================================================
    # 2. Normalize CSV course codes
    # =========================================================

    requested_codes = {
        _normalize_code(code)
        for code in (course_codes or [])
        if _normalize_code(code)
    }

    if not requested_codes:
        return {
            "status": "ERROR",
            "success": False,
            "requested_courses": [],
            "matched_courses": [],
            "missing_courses": [],
            "placed": [],
            "unplaced": [],
            "violations_count": 1,
            "verification_errors": [
                "No course codes were provided by the CSV."
            ],
        }

    # =========================================================
    # 3. Build database lookup
    # =========================================================

    db_courses = data.get("courses", [])

    db_by_code = _build_course_lookup(db_courses)

    # =========================================================
    # 4. Separate valid and invalid CSV courses
    #
    # IMPORTANT:
    # Missing courses are NOT raised as exceptions.
    # They are reported and scheduling continues.
    # =========================================================

    missing_codes = sorted(
        requested_codes - set(db_by_code.keys())
    )

    matched_codes = sorted(
        requested_codes & set(db_by_code.keys())
    )

    # =========================================================
    # 5. Build missing-course records
    # =========================================================

    missing_course_records = [
        _make_missing_course_record(code)
        for code in missing_codes
    ]

    # =========================================================
    # 6. Normalize enrollment overrides
    # =========================================================

    uploaded_enrolments = uploaded_enrolments or {}

    normalized_enrolments = {}

    for code, value in uploaded_enrolments.items():

        normalized_code = _normalize_code(code)

        if not normalized_code:
            continue

        try:
            normalized_enrolments[normalized_code] = int(value)
        except (TypeError, ValueError):
            continue

    # =========================================================
    # 7. Build ONLY valid selected courses
    # =========================================================

    selected_courses = _build_selected_courses(
        requested_codes,
        db_by_code,
        normalized_enrolments,
    )

    selected_course_ids = {
        course["course_id"]
        for course in selected_courses
    }

    # =========================================================
    # 8. If every CSV course is invalid
    #
    # Do not call DSATUR with an empty graph.
    # =========================================================

    if not selected_courses:

        return {
            "status": "CONFLICT",
            "success": False,
            "requested_courses": sorted(requested_codes),
            "matched_courses": [],
            "missing_courses": missing_codes,
            "placed": [],
            "unplaced": missing_course_records,
            "violations_count": len(missing_codes),
            "verification_errors": [],
        }

    # =========================================================
    # 9. Filter P0 constraints to selected courses
    # =========================================================

    selected_co_enrolments = [
        row
        for row in data.get("co_enrolments", [])
        if (
            row["course_id_a"] in selected_course_ids
            and row["course_id_b"] in selected_course_ids
        )
    ]

    selected_allowed_timeslots = [
        row
        for row in data.get("allowed_timeslots", [])
        if row["course_id"] in selected_course_ids
    ]

    selected_equipment_reqs = [
        row
        for row in data.get("equipment_reqs", [])
        if row["course_id"] in selected_course_ids
    ]

    rooms = data.get("rooms", [])

    timeslots = data.get("timeslots", [])

    room_equipment = data.get(
        "room_equipment",
        [],
    )

    # =========================================================
    # 10. Build conflict graph
    # =========================================================

    graph = build_conflict_graph(
        selected_courses,
        selected_co_enrolments,
    )

    # =========================================================
    # 11. Run DSATUR
    # =========================================================

    dsatur_result = dsatur_schedule(
        graph,
        selected_courses,
        timeslots,
        selected_allowed_timeslots,
    )

    # =========================================================
    # 12. Assign rooms
    #
    # IMPORTANT:
    # This uses the original P0 assign_rooms() signature.
    # =========================================================

    room_result = assign_rooms(
        dsatur_result["schedule"],
        selected_courses,
        rooms,
        selected_equipment_reqs,
        room_equipment,
    )

    # =========================================================
    # 13. Verify the placed schedule
    # =========================================================

    verification = verify_schedule(
        room_result["placed"],
        selected_courses,
        graph,
        timeslots,
        selected_allowed_timeslots,
        rooms,
        selected_equipment_reqs,
        room_equipment,
    )

    # =========================================================
    # 14. Combine scheduler/room unplaced courses
    # =========================================================

    all_unplaced = []

    all_unplaced.extend(
        dsatur_result.get("unplaced", [])
    )

    all_unplaced.extend(
        room_result.get("unplaced", [])
    )

    # =========================================================
    # 15. Convert placed records to frontend format
    # =========================================================

    placed = []

    for item in room_result.get("placed", []):

        placed.append(
            {
                "course_id": item["course_id"],
                "course": item["code"],
                "title": item["title"],
                "lecturer": item.get("lecturer"),
                "day": item["day_of_week"],
                "time": (
                    f"{item['start_time']} - "
                    f"{item['end_time']}"
                ),
                "timeslot_id": item["timeslot_id"],
                "timeslot_label": item["timeslot_label"],
                "room_id": item["room_id"],
                "room": item["room_code"],
                "room_capacity": item["room_capacity"],
            }
        )

    # =========================================================
    # 16. Add missing CSV courses to unplaced display
    #
    # These are NOT scheduling failures. They are input/data
    # matching issues.
    # =========================================================

    display_unplaced = list(all_unplaced)

    display_unplaced.extend(
        missing_course_records
    )

    # =========================================================
    # 17. Verification errors
    # =========================================================

    verification_errors = list(
        verification.get("errors", [])
    )

    # =========================================================
    # 18. Determine overall status
    #
    # Missing courses make the request incomplete, but they
    # do NOT invalidate successfully scheduled valid courses.
    # =========================================================

    scheduling_success = (
        verification.get("valid", False)
        and not all_unplaced
    )

    fully_successful = (
        scheduling_success
        and not missing_codes
    )

    if fully_successful:
        status = "SUCCESS"

    elif placed:
        status = "PARTIAL"

    else:
        status = "CONFLICT"

    # =========================================================
    # 19. Return frontend result
    # =========================================================

    return {
        "status": status,

        # True means the complete request was successfully
        # scheduled with no missing courses.
        "success": fully_successful,

        # All codes supplied by the CSV.
        "requested_courses": sorted(
            requested_codes
        ),

        # Only codes that actually exist in the DB.
        "matched_courses": matched_codes,

        # Codes that were present in CSV but not DB.
        "missing_courses": missing_codes,

        # Successfully room-assigned courses.
        "placed": placed,

        # Actual scheduling failures + missing CSV courses.
        "unplaced": display_unplaced,

        # Missing input courses count as a user-facing issue.
        "violations_count": (
            len(display_unplaced)
            + len(verification_errors)
        ),

        "verification_errors": verification_errors,
    }