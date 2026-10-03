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


def assign_rooms(
    schedule,
    courses,
    rooms,
    equipment_reqs,
    room_equipment
):
    """
    Assign a room to every course that already has a timeslot.

    Rules:
    1. Room capacity must satisfy the course requirement.
    2. Required equipment must exist in the room.
    3. Courses requiring a lab must use a lab room.
    4. A room cannot be used by two courses in the same timeslot.
    5. If no suitable room exists, the course becomes unplaced.
    """

    course_lookup = {
        course["course_id"]: course
        for course in courses
    }

    course_equipment = _build_course_equipment_map(
        equipment_reqs
    )

    room_equipment_map = _build_room_equipment_map(
        room_equipment
    )

    # Track room use per timeslot.
    # Example:
    # {
    #     1: {2, 4},
    #     2: {1}
    # }
    room_usage = {}

    placed = []
    unplaced = []

    for item in schedule:

        course_id = item["course_id"]
        timeslot_id = item["timeslot_id"]

        course = course_lookup.get(course_id)

        if course is None:
            unplaced.append({
                "course_id": course_id,
                "reason_code": "OTHER",
                "detail": "Course data could not be found"
            })
            continue

        expected_enrolment = course.get(
            "expected_enrolment"
        ) or 0

        min_capacity = course.get(
            "min_capacity"
        ) or 0

        required_capacity = max(
            expected_enrolment,
            min_capacity
        )

        requires_lab = bool(
            course.get("requires_lab")
        )

        required_equipment = course_equipment.get(
            course_id,
            set()
        )

        used_rooms = room_usage.setdefault(
            timeslot_id,
            set()
        )

        # --------------------------------------------------
        # Find all rooms large enough first.
        # This lets us distinguish capacity failures from
        # equipment/resource failures.
        # --------------------------------------------------

        capacity_candidates = [
            room
            for room in rooms
            if room["capacity"] >= required_capacity
        ]

        if not capacity_candidates:
            largest_capacity = max(
                (room["capacity"] for room in rooms),
                default=0
            )

            unplaced.append({
                "course_id": course_id,
                "code": course["code"],
                "title": course["title"],
                "reason_code": "ROOM_CAPACITY",
                "detail": (
                    f"Requires capacity {required_capacity}; "
                    f"largest available room capacity is "
                    f"{largest_capacity}"
                )
            })
            continue

        # --------------------------------------------------
        # Apply lab/equipment requirements.
        # --------------------------------------------------

        resource_candidates = []

        for room in capacity_candidates:

            if requires_lab and not room.get(
                "is_lab",
                False
            ):
                continue

            available_equipment = (
                room_equipment_map.get(
                    room["room_id"],
                    set()
                )
            )

            if not required_equipment.issubset(
                available_equipment
            ):
                continue

            resource_candidates.append(room)

        if not resource_candidates:
            unplaced.append({
                "course_id": course_id,
                "code": course["code"],
                "title": course["title"],
                "reason_code": "ROOM_EQUIPMENT",
                "detail": (
                    "No room satisfies the required "
                    "lab/equipment constraints"
                )
            })
            continue

        # --------------------------------------------------
        # Choose a room that is free in this timeslot.
        # Prefer the smallest suitable room.
        # --------------------------------------------------

        free_candidates = [
            room
            for room in resource_candidates
            if room["room_id"] not in used_rooms
        ]

        if not free_candidates:
            unplaced.append({
                "course_id": course_id,
                "code": course["code"],
                "title": course["title"],
                "reason_code": "OTHER",
                "detail": (
                    "Suitable rooms exist but are already "
                    "occupied in this timeslot"
                )
            })
            continue

        selected_room = min(
            free_candidates,
            key=lambda room: (
                room["capacity"],
                room["room_id"]
            )
        )

        used_rooms.add(
            selected_room["room_id"]
        )

        placed.append({
            **item,
            "lecturer": course.get("lecturer"),
            "room_id": selected_room["room_id"],
            "room_code": selected_room["code"],
            "room_capacity": selected_room["capacity"]
        })

    return {
        "placed": placed,
        "unplaced": unplaced
    }