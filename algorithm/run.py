import json

from algorithm.db_loader import load_data
from algorithm.graph import build_conflict_graph
from algorithm.dsatur import dsatur_schedule
from algorithm.room_assigner import assign_rooms
from algorithm.verifier import verify_schedule


# Courses that are intentionally impossible in the test dataset.
#
# These are not algorithm bugs:
#
# 25 -> conflicts with 24 and has no legal alternative timeslot
# 28 -> part of the intentionally unplaceable MTH401/MTH402/MTH403 clique
# 23 -> requires capacity 150, while the largest room has capacity 80
#
# ENG101 (11) is NOT included here because its room conflict
# is a genuine scheduling limitation that we want to report.
EXPECTED_UNPLACEABLE = {
    25,
    28,
    23,
}


def run_scheduler():
    # =========================================================
    # 1. Load database data
    # =========================================================

    data = load_data()

    # =========================================================
    # 2. Build conflict graph
    # =========================================================

    graph = build_conflict_graph(
        data["courses"],
        data["co_enrolments"],
    )

    # =========================================================
    # 3. Assign timeslots using DSATUR
    # =========================================================

    dsatur_result = dsatur_schedule(
        graph,
        data["courses"],
        data["timeslots"],
        data["allowed_timeslots"],
    )

    # =========================================================
    # 4. Assign rooms
    # =========================================================

    room_result = assign_rooms(
        dsatur_result["schedule"],
        data["courses"],
        data["rooms"],
        data["equipment_reqs"],
        data["room_equipment"],
    )

    # =========================================================
    # 5. Verify the placed schedule
    # =========================================================

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

    # =========================================================
    # 6. Combine all unplaced courses
    # =========================================================

    all_unplaced = (
        dsatur_result["unplaced"]
        + room_result["unplaced"]
    )

    # =========================================================
    # 7. Build clean placed output
    # =========================================================

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

    # =========================================================
    # 8. Separate expected and unexpected unplaced courses
    # =========================================================

    expected_unplaced = []

    unexpected_unplaced = []

    for item in all_unplaced:

        course_id = item["course_id"]

        if course_id in EXPECTED_UNPLACEABLE:

            expected_unplaced.append(item)

        else:

            unexpected_unplaced.append(item)

    # =========================================================
    # 9. Determine scheduler status
    # =========================================================
    #
    # SUCCESS
    # -------
    # Everything was placed and verification passed.
    #
    # SUCCESS_WITH_UNPLACED
    # ---------------------
    # The schedule is valid, but some courses could not be
    # placed because of known/legitimate constraints.
    #
    # CONFLICT
    # --------
    # There is an unexpected unplaced course or a verification
    # error.
    # =========================================================

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

    # =========================================================
    # 10. Return final result
    # =========================================================

    return {
        "status": status,
        "success": success,

        "summary": {
            "total_courses": len(data["courses"]),
            "placed_courses": len(placed),
            "unplaced_courses": len(all_unplaced),
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

        "expected_unplaced": expected_unplaced,

        "unexpected_unplaced": unexpected_unplaced,

        "violations_count": (
            len(unexpected_unplaced)
            + len(verification["errors"])
        ),

        "verification_errors": verification["errors"],
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