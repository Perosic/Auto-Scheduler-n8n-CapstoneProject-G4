import json

from algorithm.db_loader import load_data
from algorithm.graph import build_conflict_graph
from algorithm.dsatur import dsatur_schedule
from algorithm.verifier import verify_schedule


def main():
    # ---------------------------------------------------------
    # 1. Load database data
    # ---------------------------------------------------------

    data = load_data()

    # ---------------------------------------------------------
    # 2. Build conflict graph
    # ---------------------------------------------------------

    graph = build_conflict_graph(
        data["courses"],
        data["co_enrolments"]
    )

    # ---------------------------------------------------------
    # 3. Generate timetable
    # ---------------------------------------------------------

    result = dsatur_schedule(
        graph,
        data["courses"],
        data["timeslots"],
        data["allowed_timeslots"]
    )

    # ---------------------------------------------------------
    # 4. Verify generated timetable
    # ---------------------------------------------------------

    verification = verify_schedule(
        result["schedule"],
        data["courses"],
        graph,
        data["timeslots"],
        data["allowed_timeslots"]
    )

    # ---------------------------------------------------------
    # 5. Build final output
    # ---------------------------------------------------------

    output = {
        "valid": verification["valid"],
        "verification_errors": verification["errors"],
        "scheduled": result["schedule"],
        "unplaced": result["unplaced"]
    }

    # ---------------------------------------------------------
    # 6. Output JSON
    # ---------------------------------------------------------

    print(json.dumps(output, indent=2, default=str))


if __name__ == "__main__":
    main()