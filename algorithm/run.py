import json

from algorithm.db_loader import load_data
from algorithm.graph import build_conflict_graph
from algorithm.dsatur import dsatur_schedule
from algorithm.room_assigner import assign_rooms
from algorithm.verifier import verify_schedule


def run_scheduler():
    data = load_data()

    graph = build_conflict_graph(
        data["courses"],
        data["co_enrolments"]
    )

    dsatur_result = dsatur_schedule(
        graph,
        data["courses"],
        data["timeslots"],
        data["allowed_timeslots"]
    )

    room_result = assign_rooms(
        dsatur_result["schedule"],
        data["courses"],
        data["rooms"],
        data["equipment_reqs"],
        data["room_equipment"]
    )

    verification = verify_schedule(
        room_result["placed"],
        data["courses"],
        graph,
        data["timeslots"],
        data["allowed_timeslots"],
        data["rooms"],
        data["equipment_reqs"],
        data["room_equipment"]
    )

    all_unplaced = (
        dsatur_result["unplaced"]
        + room_result["unplaced"]
    )

    placed = []

    for item in room_result["placed"]:
        placed.append({
            "course_id": item["course_id"],
            "course": item["code"],
            "title": item["title"],
            "day": item["day_of_week"],
            "time": f"{item['start_time']} - {item['end_time']}",
            "timeslot_id": item["timeslot_id"],
            "timeslot_label": item["timeslot_label"],
            "room_id": item["room_id"],
            "room": item["room_code"],
            "room_capacity": item["room_capacity"]
        })

    success = verification["valid"] and not all_unplaced

    return {
        "status": "SUCCESS" if success else "CONFLICT",
        "success": success,
        "placed": placed,
        "unplaced": all_unplaced,
        "violations_count": len(verification["errors"]),
        "verification_errors": verification["errors"]
    }


def main():
    output = run_scheduler()

    print(
        json.dumps(
            output,
            indent=2,
            default=str
        )
    )


if __name__ == "__main__":
    main()
