import json

from algorithm.db_loader import load_data
from algorithm.graph import build_conflict_graph
from algorithm.dsatur import dsatur_schedule
from algorithm.room_assigner import assign_rooms
from algorithm.verifier import verify_schedule


def main():
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

    output = {
        "valid": verification["valid"],
        "verification_errors": verification["errors"],
        "scheduled": room_result["placed"],
        "unplaced": all_unplaced
    }

    print(
        json.dumps(
            output,
            indent=2,
            default=str
        )
    )


if __name__ == "__main__":
    main()