def _build_allowed_timeslot_map(allowed_timeslots):
    allowed_map = {}

    for row in allowed_timeslots:
        allowed_map.setdefault(
            row["course_id"],
            set()
        ).add(row["timeslot_id"])

    return allowed_map


def _build_course_equipment_map(equipment_reqs):
    equipment_map = {}

    for row in equipment_reqs:
        equipment_map.setdefault(
            row["course_id"],
            set()
        ).add(row["equipment_name"])

    return equipment_map


def _build_room_equipment_map(room_equipment):
    equipment_map = {}

    for row in room_equipment:
        equipment_map.setdefault(
            row["room_id"],
            set()
        ).add(row["equipment_name"])

    return equipment_map


def verify_schedule(
    schedule,
    courses,
    graph,
    timeslots,
    allowed_timeslots,
    rooms=None,
    equipment_reqs=None,
    room_equipment=None
):
    """
    Independently verify the generated timetable.

    Checks:
    1. Every scheduled course exists.
    2. A course is not scheduled more than once.
    3. Every assigned timeslot exists.
    4. Explicit allowed-timeslot restrictions are respected.
    5. Conflicting courses do not share a timeslot.
    6. Every assigned room exists.
    7. Room capacity satisfies course requirements.
    8. Lab requirements are respected.
    9. Required room equipment is available.
    10. A room is not double-booked in the same timeslot.
    """

    errors = []

    rooms = rooms or []
    equipment_reqs = equipment_reqs or []
    room_equipment = room_equipment or []

    course_lookup = {
        course["course_id"]: course
        for course in courses
    }

    room_lookup = {
        room["room_id"]: room
        for room in rooms
    }

    valid_timeslot_ids = {
        timeslot["timeslot_id"]
        for timeslot in timeslots
    }

    allowed_map = _build_allowed_timeslot_map(
        allowed_timeslots
    )

    course_equipment = _build_course_equipment_map(
        equipment_reqs
    )

    room_equipment_map = _build_room_equipment_map(
        room_equipment
    )

    assigned_courses = set()
    assignments_by_timeslot = {}
    room_usage = {}

    for item in schedule:

        course_id = item["course_id"]
        timeslot_id = item["timeslot_id"]

        if course_id not in course_lookup:
            errors.append(
                f"Unknown course_id: {course_id}"
            )
            continue

        course = course_lookup[course_id]

        if course_id in assigned_courses:
            errors.append(
                f"Course {course_id} is scheduled more than once"
            )

        assigned_courses.add(course_id)

        if timeslot_id not in valid_timeslot_ids:
            errors.append(
                f"Course {course_id} uses invalid timeslot "
                f"{timeslot_id}"
            )
            continue

        if course_id in allowed_map:
            if timeslot_id not in allowed_map[course_id]:
                errors.append(
                    f"Course {course_id} is assigned to timeslot "
                    f"{timeslot_id}, but it is not allowed there"
                )

        assignments_by_timeslot.setdefault(
            timeslot_id,
            []
        ).append(course_id)

        # ---------------------------------------------
        # Room verification
        # ---------------------------------------------

        if rooms:

            room_id = item.get("room_id")

            if room_id is None:
                errors.append(
                    f"Course {course_id} has no room assignment"
                )
                continue

            if room_id not in room_lookup:
                errors.append(
                    f"Course {course_id} uses unknown room "
                    f"{room_id}"
                )
                continue

            room = room_lookup[room_id]

            expected_enrolment = (
                course.get("expected_enrolment") or 0
            )

            min_capacity = (
                course.get("min_capacity") or 0
            )

            required_capacity = max(
                expected_enrolment,
                min_capacity
            )

            if room["capacity"] < required_capacity:
                errors.append(
                    f"Course {course_id} requires capacity "
                    f"{required_capacity}, but room {room_id} "
                    f"has capacity {room['capacity']}"
                )

            if (
                course.get("requires_lab")
                and not room.get("is_lab", False)
            ):
                errors.append(
                    f"Course {course_id} requires a lab, "
                    f"but room {room_id} is not a lab"
                )

            required_equipment = course_equipment.get(
                course_id,
                set()
            )

            available_equipment = room_equipment_map.get(
                room_id,
                set()
            )

            missing_equipment = (
                required_equipment
                - available_equipment
            )

            if missing_equipment:
                errors.append(
                    f"Course {course_id} is missing equipment "
                    f"in room {room_id}: "
                    f"{sorted(missing_equipment)}"
                )

            usage_key = (
                timeslot_id,
                room_id
            )

            if usage_key in room_usage:
                other_course = room_usage[usage_key]

                errors.append(
                    f"Room {room_id} is double-booked in "
                    f"timeslot {timeslot_id} by courses "
                    f"{other_course} and {course_id}"
                )
            else:
                room_usage[usage_key] = course_id

    # ---------------------------------------------
    # Graph conflicts
    # ---------------------------------------------

    for timeslot_id, course_ids in (
        assignments_by_timeslot.items()
    ):

        for i in range(len(course_ids)):

            course_a = course_ids[i]

            for j in range(i + 1, len(course_ids)):

                course_b = course_ids[j]

                if course_b in graph.get(
                    course_a,
                    set()
                ):
                    errors.append(
                        f"Conflict: courses {course_a} and "
                        f"{course_b} share timeslot "
                        f"{timeslot_id}"
                    )

    return {
        "valid": len(errors) == 0,
        "errors": errors
    }