"""
dsatur.py

DSATUR-based course timeslot scheduler.

A course can be assigned to a timeslot when:

1. The timeslot is allowed for that course.
2. None of its conflicting courses already use that timeslot.

Courses with no explicit allowed-timeslot rows may use any
available timeslot.

The scheduler does NOT assign rooms. Room assignment is handled
separately by room_assigner.py.
"""


def _build_allowed_timeslot_map(
    allowed_timeslots,
    all_timeslot_ids,
):
    """
    Build:

        course_id -> set(timeslot_id)

    for courses that have explicit restrictions.

    Courses absent from this map are unrestricted.
    """

    allowed_map = {}

    for row in allowed_timeslots:
        course_id = row["course_id"]
        timeslot_id = row["timeslot_id"]

        allowed_map.setdefault(
            course_id,
            set()
        ).add(timeslot_id)

    all_slots = set(all_timeslot_ids)

    return allowed_map, all_slots


def dsatur_schedule(
    graph,
    courses,
    timeslots,
    allowed_timeslots,
):
    """
    Schedule courses using DSATUR.

    Returns:

        {
            "schedule": [...],
            "unplaced": [...]
        }
    """

    # =========================================================
    # 1. Validate timeslots
    # =========================================================

    all_timeslot_ids = [
        timeslot["timeslot_id"]
        for timeslot in timeslots
    ]

    if not all_timeslot_ids:
        raise ValueError(
            "No timeslots are available."
        )

    # =========================================================
    # 2. Allowed timeslots
    # =========================================================

    explicit_allowed, all_slots = (
        _build_allowed_timeslot_map(
            allowed_timeslots,
            all_timeslot_ids,
        )
    )

    # =========================================================
    # 3. Course lookup
    # =========================================================

    course_lookup = {
        course["course_id"]: course
        for course in courses
    }

    # =========================================================
    # 4. Ensure every course exists in graph
    #
    # This is important.
    #
    # If a course has no conflicts, it must still be
    # scheduled.
    # =========================================================

    complete_graph = {
        course_id: set(graph.get(course_id, set()))
        for course_id in course_lookup
    }

    # =========================================================
    # 5. Validate graph
    # =========================================================

    for course_id, neighbors in complete_graph.items():

        for neighbor in neighbors:

            if neighbor not in course_lookup:
                raise ValueError(
                    "Conflict graph contains unknown "
                    f"neighbor course_id: {neighbor}"
                )

    # =========================================================
    # 6. Storage
    # =========================================================

    assigned = {}

    unplaced_ids = set()

    remaining = set(
        course_lookup.keys()
    )

    # =========================================================
    # 7. Helper functions
    # =========================================================

    def get_allowed_slots(course_id):

        if course_id in explicit_allowed:
            return set(
                explicit_allowed[course_id]
            )

        return set(all_slots)

    def get_conflicting_slots(course_id):

        return {
            assigned[neighbor]
            for neighbor in complete_graph[course_id]
            if neighbor in assigned
        }

    def get_candidates(course_id):

        allowed = get_allowed_slots(
            course_id
        )

        conflicting = get_conflicting_slots(
            course_id
        )

        return allowed - conflicting

    # =========================================================
    # 8. DSATUR loop
    # =========================================================

    while remaining:

        def priority(course_id):

            # Timeslots already used by neighbours.
            neighbor_timeslots = {
                assigned[neighbor]
                for neighbor in complete_graph[course_id]
                if neighbor in assigned
            }

            saturation = len(
                neighbor_timeslots
            )

            degree = len(
                complete_graph[course_id]
            )

            legal_slots = len(
                get_candidates(course_id)
            )

            # Priority:
            #
            # 1. highest saturation
            # 2. highest degree
            # 3. fewest legal slots
            # 4. lowest course ID
            #
            # The final negative course_id gives
            # deterministic behaviour.

            return (
                saturation,
                degree,
                -legal_slots,
                -course_id,
            )

        selected_course = max(
            remaining,
            key=priority,
        )

        candidates = get_candidates(
            selected_course
        )

        # =====================================================
        # 9. Assign
        # =====================================================

        if candidates:

            # Deterministic:
            # choose the earliest available timeslot.
            selected_timeslot = min(
                candidates
            )

            assigned[
                selected_course
            ] = selected_timeslot

        else:

            unplaced_ids.add(
                selected_course
            )

        remaining.remove(
            selected_course
        )

    # =========================================================
    # 10. Timeslot lookup
    # =========================================================

    timeslot_lookup = {
        timeslot["timeslot_id"]: timeslot
        for timeslot in timeslots
    }

    # =========================================================
    # 11. Build schedule
    # =========================================================

    schedule = []

    for course_id, timeslot_id in sorted(
        assigned.items()
    ):

        course = course_lookup[
            course_id
        ]

        timeslot = timeslot_lookup[
            timeslot_id
        ]

        schedule.append(
            {
                "course_id": course_id,
                "code": course["code"],
                "title": course["title"],
                "timeslot_id": timeslot_id,
                "timeslot_label": timeslot["label"],
                "day_of_week": timeslot["day_of_week"],
                "start_time": timeslot["start_time"],
                "end_time": timeslot["end_time"],
            }
        )

    # =========================================================
    # 12. Build unplaced
    # =========================================================

    unplaced = []

    for course_id in sorted(
        unplaced_ids
    ):

        course = course_lookup[
            course_id
        ]

        unplaced.append(
            {
                "course_id": course_id,
                "code": course["code"],
                "title": course["title"],
                "reason_code": "NO_LEGAL_TIMESLOT",
                "detail": (
                    "No legal timeslot available "
                    "after applying conflict and "
                    "allowed-timeslot constraints."
                ),
            }
        )

    # =========================================================
    # 13. Return
    # =========================================================

    return {
        "schedule": schedule,
        "unplaced": unplaced,
    }


# =============================================================
# Standalone test
# =============================================================

if __name__ == "__main__":

    test_graph = {
        1: {2},
        2: {1, 3},
        3: {2},
    }

    test_courses = [
        {
            "course_id": 1,
            "code": "TEST101",
            "title": "Test Course 1",
        },
        {
            "course_id": 2,
            "code": "TEST102",
            "title": "Test Course 2",
        },
        {
            "course_id": 3,
            "code": "TEST103",
            "title": "Test Course 3",
        },
    ]

    test_timeslots = [
        {
            "timeslot_id": 1,
            "label": "Mon-09:00",
            "day_of_week": "Mon",
            "start_time": "09:00:00",
            "end_time": "10:00:00",
        },
        {
            "timeslot_id": 2,
            "label": "Mon-10:00",
            "day_of_week": "Mon",
            "start_time": "10:00:00",
            "end_time": "11:00:00",
        },
    ]

    test_allowed_timeslots = []

    result = dsatur_schedule(
        test_graph,
        test_courses,
        test_timeslots,
        test_allowed_timeslots,
    )

    print("\nSchedule:")

    for item in result["schedule"]:
        print(item)

    print("\nUnplaced:")

    for item in result["unplaced"]:
        print(item)