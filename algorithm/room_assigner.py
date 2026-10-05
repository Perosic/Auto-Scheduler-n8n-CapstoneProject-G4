"""
room_assigner.py

Assign rooms to courses that already have timeslots.

Rules:
1. Room capacity must satisfy course requirements.
2. Required equipment must exist in the room.
3. Lab courses must use lab rooms.
4. A room cannot host two courses in the same timeslot.
5. Prefer the smallest suitable room to avoid wasting capacity.
6. If no suitable room is available, return the course as unplaced.
"""


def _build_course_equipment_map(equipment_reqs):
    """
    Build:

        course_id -> set(equipment_name)
    """

    equipment_map = {}

    for row in equipment_reqs:

        course_id = row["course_id"]
        equipment_name = row["equipment_name"]

        equipment_map.setdefault(
            course_id,
            set(),
        ).add(
            equipment_name
        )

    return equipment_map


def _build_room_equipment_map(room_equipment):
    """
    Build:

        room_id -> set(equipment_name)
    """

    equipment_map = {}

    for row in room_equipment:

        room_id = row["room_id"]
        equipment_name = row["equipment_name"]

        equipment_map.setdefault(
            room_id,
            set(),
        ).add(
            equipment_name
        )

    return equipment_map


def assign_rooms(
    schedule,
    courses,
    rooms,
    equipment_reqs,
    room_equipment,
):
    """
    Assign rooms to an existing timeslot schedule.

    Returns:

        {
            "placed": [...],
            "unplaced": [...]
        }
    """

    # =========================================================
    # 1. Lookups
    # =========================================================

    course_lookup = {
        course["course_id"]: course
        for course in courses
    }

    course_equipment = (
        _build_course_equipment_map(
            equipment_reqs
        )
    )

    room_equipment_map = (
        _build_room_equipment_map(
            room_equipment
        )
    )

    # =========================================================
    # 2. Track room usage
    #
    # timeslot_id -> set(room_id)
    # =========================================================

    room_usage = {}

    placed = []
    unplaced = []

    # =========================================================
    # 3. Process every scheduled course
    # =========================================================

    for item in schedule:

        course_id = item["course_id"]
        timeslot_id = item["timeslot_id"]

        course = course_lookup.get(
            course_id
        )

        # -----------------------------------------------------
        # Unknown course
        # -----------------------------------------------------

        if course is None:

            unplaced.append(
                {
                    "course_id": course_id,
                    "reason_code": "OTHER",
                    "detail": (
                        "Course data could not "
                        "be found."
                    ),
                }
            )

            continue

        # =====================================================
        # 4. Determine capacity requirement
        # =====================================================

        expected_enrolment = (
            course.get(
                "expected_enrolment"
            )
            or 0
        )

        min_capacity = (
            course.get(
                "min_capacity"
            )
            or 0
        )

        required_capacity = max(
            expected_enrolment,
            min_capacity,
        )

        # =====================================================
        # 5. Determine lab requirement
        # =====================================================

        requires_lab = bool(
            course.get(
                "requires_lab"
            )
        )

        # =====================================================
        # 6. Required equipment
        # =====================================================

        required_equipment = (
            course_equipment.get(
                course_id,
                set(),
            )
        )

        # =====================================================
        # 7. Rooms already occupied in this timeslot
        # =====================================================

        used_rooms = room_usage.setdefault(
            timeslot_id,
            set(),
        )

        # =====================================================
        # 8. Filter rooms by capacity
        # =====================================================

        capacity_candidates = [
            room
            for room in rooms
            if room["capacity"]
            >= required_capacity
        ]

        if not capacity_candidates:

            largest_capacity = max(
                (
                    room["capacity"]
                    for room in rooms
                ),
                default=0,
            )

            unplaced.append(
                {
                    "course_id": course_id,
                    "code": course["code"],
                    "title": course["title"],
                    "reason_code": "ROOM_CAPACITY",
                    "detail": (
                        f"Requires capacity "
                        f"{required_capacity}; "
                        f"largest available room "
                        f"capacity is "
                        f"{largest_capacity}."
                    ),
                }
            )

            continue

        # =====================================================
        # 9. Filter by lab/equipment requirements
        # =====================================================

        resource_candidates = []

        for room in capacity_candidates:

            # -------------------------------------------------
            # Lab requirement
            # -------------------------------------------------

            if requires_lab and not room.get(
                "is_lab",
                False,
            ):
                continue

            # -------------------------------------------------
            # Equipment requirement
            # -------------------------------------------------

            available_equipment = (
                room_equipment_map.get(
                    room["room_id"],
                    set(),
                )
            )

            if not required_equipment.issubset(
                available_equipment
            ):
                continue

            resource_candidates.append(
                room
            )

        # =====================================================
        # 10. No room satisfies resource requirements
        # =====================================================

        if not resource_candidates:

            if requires_lab:

                reason_code = "ROOM_EQUIPMENT"

                detail = (
                    "No available room satisfies "
                    "the required lab/equipment "
                    "constraints."
                )

            elif required_equipment:

                reason_code = "ROOM_EQUIPMENT"

                detail = (
                    "No available room satisfies "
                    "the required equipment "
                    "constraints."
                )

            else:

                reason_code = "ROOM_EQUIPMENT"

                detail = (
                    "No room satisfies the "
                    "course room requirements."
                )

            unplaced.append(
                {
                    "course_id": course_id,
                    "code": course["code"],
                    "title": course["title"],
                    "reason_code": reason_code,
                    "detail": detail,
                }
            )

            continue

        # =====================================================
        # 11. Remove rooms already occupied
        # =====================================================

        free_candidates = [
            room
            for room in resource_candidates
            if room["room_id"]
            not in used_rooms
        ]

        # =====================================================
        # 12. No free room at this timeslot
        # =====================================================

        if not free_candidates:

            unplaced.append(
                {
                    "course_id": course_id,
                    "code": course["code"],
                    "title": course["title"],
                    "reason_code": "ROOM_TIMESLOT_CONFLICT",
                    "detail": (
                        "Suitable rooms exist, "
                        "but all suitable rooms "
                        "are already occupied "
                        "in this timeslot."
                    ),
                }
            )

            continue

        # =====================================================
        # 13. Select the best room
        #
        # Prefer:
        #   1. smallest capacity that fits
        #   2. lowest room ID
        #
        # This prevents wasting large lecture halls.
        # =====================================================

        selected_room = min(
            free_candidates,
            key=lambda room: (
                room["capacity"],
                room["room_id"],
            ),
        )

        selected_room_id = (
            selected_room["room_id"]
        )

        # =====================================================
        # 14. Mark room as occupied
        # =====================================================

        used_rooms.add(
            selected_room_id
        )

        # =====================================================
        # 15. Add placed course
        # =====================================================

        placed.append(
            {
                **item,

                "lecturer": course.get(
                    "lecturer"
                ),

                "room_id": selected_room_id,

                "room_code": selected_room[
                    "code"
                ],

                "room_capacity": selected_room[
                    "capacity"
                ],
            }
        )

    # =========================================================
    # 16. Return
    # =========================================================

    return {
        "placed": placed,
        "unplaced": unplaced,
    }