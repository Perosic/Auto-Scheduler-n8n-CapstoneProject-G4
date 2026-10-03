"""
P1 scheduler adapter.

Connects the Streamlit CSV upload to the existing P0 scheduling algorithm.
P0 files are not modified.
"""

from algorithm.db_loader import load_data
from algorithm.graph import build_conflict_graph
from algorithm.dsatur import dsatur_schedule
from algorithm.room_assigner import assign_rooms
from algorithm.verifier import verify_schedule


def run_scheduler_for_courses(course_codes, uploaded_enrolments=None):
    """Run the existing scheduler for courses selected from the P1 CSV."""

    data = load_data()

    requested_codes = {
        str(code).strip().upper()
        for code in course_codes
        if str(code).strip()
    }

    if not requested_codes:
        raise ValueError("No course codes were provided by the CSV.")

    db_courses = data["courses"]

    db_by_code = {
        str(course["code"]).strip().upper(): course
        for course in db_courses
    }

    missing_codes = sorted(
        requested_codes - set(db_by_code.keys())
    )

    if missing_codes:
        raise ValueError(
            "The following courses from the CSV are not available "
            "in the scheduling database: "
            + ", ".join(missing_codes)
        )

    selected_course_ids = {
        db_by_code[code]["course_id"]
        for code in requested_codes
    }

    uploaded_enrolments = uploaded_enrolments or {}

    selected_courses = []

    for code in sorted(requested_codes):
        course = dict(db_by_code[code])

        if code in uploaded_enrolments:
            course["expected_enrolment"] = int(
                uploaded_enrolments[code]
            )

        selected_courses.append(course)

    selected_co_enrolments = [
        row
        for row in data["co_enrolments"]
        if (
            row["course_id_a"] in selected_course_ids
            and row["course_id_b"] in selected_course_ids
        )
    ]

    selected_allowed_timeslots = [
        row
        for row in data["allowed_timeslots"]
        if row["course_id"] in selected_course_ids
    ]

    selected_equipment_reqs = [
        row
        for row in data["equipment_reqs"]
        if row["course_id"] in selected_course_ids
    ]

    rooms = data["rooms"]
    timeslots = data["timeslots"]
    room_equipment = data["room_equipment"]

    graph = build_conflict_graph(
        selected_courses,
        selected_co_enrolments,
    )

    dsatur_result = dsatur_schedule(
        graph,
        selected_courses,
        timeslots,
        selected_allowed_timeslots,
    )

    room_result = assign_rooms(
        dsatur_result["schedule"],
        selected_courses,
        rooms,
        selected_equipment_reqs,
        room_equipment,
    )

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

    all_unplaced = (
        dsatur_result["unplaced"]
        + room_result["unplaced"]
    )

    placed = []

    for item in room_result["placed"]:
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

    success = verification["valid"] and not all_unplaced

    return {
        "status": "SUCCESS" if success else "CONFLICT",
        "success": success,
        "requested_courses": sorted(requested_codes),
        "matched_courses": sorted(requested_codes),
        "missing_courses": missing_codes,
        "placed": placed,
        "unplaced": all_unplaced,
        "violations_count": (
            len(all_unplaced)
            + len(verification["errors"])
        ),
        "verification_errors": verification["errors"],
    }
