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


def _build_allowed_timeslot_map(
    allowed_timeslots,
    all_timeslot_ids
):
    """
    Build a lookup of explicitly allowed timeslots
    for each course.

    If a course has no explicit restriction,
    all timeslots are allowed.
    """

    allowed_map = {}

    for row in allowed_timeslots:
        allowed_map.setdefault(
            row["course_id"],
            set()
        ).add(row["timeslot_id"])

    return allowed_map, set(all_timeslot_ids)


def assign_rooms(
    schedule,
    courses,
    rooms,
    equipment_reqs,
    room_equipment,
    timeslots=None,
    allowed_timeslots=None,
    graph=None
):
    """
    Assign rooms to courses produced by DSATUR.

    The original DSATUR timeslot is tried first.

    If no suitable room is available in that timeslot,
    the scheduler tries other legal timeslots before
    declaring the course unplaced.

    Rules:

    1. Room capacity must satisfy course requirements.
    2. Required equipment must exist in the room.
    3. Courses requiring a lab must use a lab room.
    4. A room cannot be used by two courses
       in the same timeslot.
    5. Conflicting courses cannot share a timeslot.
    6. Explicit allowed-timeslot restrictions
       must be respected.
    """

    # ---------------------------------------------------------
    # Defaults
    # ---------------------------------------------------------

    timeslots = timeslots or []
    allowed_timeslots = allowed_timeslots or []
    graph = graph or {}

    # ---------------------------------------------------------
    # Course lookup
    # ---------------------------------------------------------

    course_lookup = {
        course["course_id"]: course
        for course in courses
    }

    # ---------------------------------------------------------
    # Timeslot lookup
    # ---------------------------------------------------------

    timeslot_lookup = {
        timeslot["timeslot_id"]: timeslot
        for timeslot in timeslots
    }

    all_timeslot_ids = [
        timeslot["timeslot_id"]
        for timeslot in timeslots
    ]

    explicit_allowed, all_slots = (
        _build_allowed_timeslot_map(
            allowed_timeslots,
            all_timeslot_ids
        )
    )

    # ---------------------------------------------------------
    # Equipment maps
    # ---------------------------------------------------------

    course_equipment = _build_course_equipment_map(
        equipment_reqs
    )

    room_equipment_map = _build_room_equipment_map(
        room_equipment
    )

    # ---------------------------------------------------------
    # Keep track of the current timeslot of every course.
    #
    # Initially these are the timeslots selected by DSATUR.
    #
    # If room assignment moves a course, its new timeslot
    # is stored here.
    # ---------------------------------------------------------

    assigned_timeslots = {
        item["course_id"]: item["timeslot_id"]
        for item in schedule
    }

    # ---------------------------------------------------------
    # Track room usage.
    #
    # Example:
    #
    # {
    #     1: {2, 4},
    #     2: {1}
    # }
    #
    # Meaning:
    # timeslot 1 uses rooms 2 and 4
    # timeslot 2 uses room 1
    # ---------------------------------------------------------

    room_usage = {}

    placed = []
    unplaced = []

    # =========================================================
    # Helper functions
    # =========================================================

    def get_allowed_slots(course_id):

        if course_id in explicit_allowed:
            return explicit_allowed[course_id]

        return all_slots

    def has_conflicting_neighbor(
        course_id,
        candidate_timeslot
    ):
        """
        Prevent a course from being moved into a timeslot
        occupied by one of its conflicting courses.
        """

        for neighbor in graph.get(
            course_id,
            set()
        ):

            if (
                neighbor in assigned_timeslots
                and
                assigned_timeslots[neighbor]
                == candidate_timeslot
            ):
                return True

        return False

    def get_resource_candidates(
        course,
        required_capacity
    ):
        """
        Return rooms satisfying:

        - capacity
        - lab requirement
        - equipment requirements
        """

        course_id = course["course_id"]

        requires_lab = bool(
            course.get("requires_lab")
        )

        required_equipment = (
            course_equipment.get(
                course_id,
                set()
            )
        )

        candidates = []

        for room in rooms:

            # ---------------------------------------------
            # Capacity
            # ---------------------------------------------

            if (
                room["capacity"]
                < required_capacity
            ):
                continue

            # ---------------------------------------------
            # Lab requirement
            # ---------------------------------------------

            if (
                requires_lab
                and not room.get(
                    "is_lab",
                    False
                )
            ):
                continue

            # ---------------------------------------------
            # Equipment requirement
            # ---------------------------------------------

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

            candidates.append(room)

        return candidates

    # =========================================================
    # Process courses
    # =========================================================

    for item in schedule:

        course_id = item["course_id"]

        original_timeslot_id = (
            item["timeslot_id"]
        )

        course = course_lookup.get(
            course_id
        )

        # -----------------------------------------------------
        # Course not found
        # -----------------------------------------------------

        if course is None:

            unplaced.append({
                "course_id": course_id,
                "reason_code": "OTHER",
                "detail": (
                    "Course data could not be found"
                )
            })

            assigned_timeslots.pop(
                course_id,
                None
            )

            continue

        # -----------------------------------------------------
        # Determine required capacity
        # -----------------------------------------------------

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
            min_capacity
        )

        # -----------------------------------------------------
        # Find rooms that satisfy the course's permanent
        # requirements.
        #
        # These requirements do NOT depend on timeslot.
        # -----------------------------------------------------

        resource_candidates = (
            get_resource_candidates(
                course,
                required_capacity
            )
        )

        # -----------------------------------------------------
        # No room anywhere can satisfy the course.
        #
        # Moving to another timeslot cannot help.
        # -----------------------------------------------------

        if not resource_candidates:

            largest_capacity = max(
                (
                    room["capacity"]
                    for room in rooms
                ),
                default=0
            )

            capacity_possible = any(
                room["capacity"]
                >= required_capacity
                for room in rooms
            )

            if not capacity_possible:

                reason_code = "ROOM_CAPACITY"

                detail = (
                    f"Requires capacity "
                    f"{required_capacity}; "
                    f"largest available room "
                    f"capacity is "
                    f"{largest_capacity}"
                )

            else:

                reason_code = "ROOM_EQUIPMENT"

                detail = (
                    "No room satisfies the required "
                    "lab/equipment constraints"
                )

            unplaced.append({
                "course_id": course_id,
                "code": course["code"],
                "title": course["title"],
                "reason_code": reason_code,
                "detail": detail
            })

            assigned_timeslots.pop(
                course_id,
                None
            )

            continue

        # =====================================================
        # Build timeslot candidates
        #
        # IMPORTANT:
        # Original DSATUR timeslot comes FIRST.
        #
        # Other legal timeslots are tried afterwards.
        # =====================================================

        allowed_slots = get_allowed_slots(
            course_id
        )

        candidate_timeslots = []

        # -----------------------------------------------------
        # Try DSATUR's original timeslot first.
        # -----------------------------------------------------

        if (
            original_timeslot_id
            in allowed_slots
        ):

            candidate_timeslots.append(
                original_timeslot_id
            )

        # -----------------------------------------------------
        # Then try all other allowed timeslots.
        # -----------------------------------------------------

        for timeslot_id in sorted(
            allowed_slots
        ):

            if (
                timeslot_id
                != original_timeslot_id
            ):

                candidate_timeslots.append(
                    timeslot_id
                )

        selected_room = None
        selected_timeslot_id = None

        # =====================================================
        # Try each possible timeslot
        # =====================================================

        for candidate_timeslot_id in (
            candidate_timeslots
        ):

            # -------------------------------------------------
            # Check course conflicts.
            #
            # This prevents the room-repair step from
            # accidentally creating a student/course clash.
            # -------------------------------------------------

            if has_conflicting_neighbor(
                course_id,
                candidate_timeslot_id
            ):

                continue

            # -------------------------------------------------
            # Rooms already used in this timeslot
            # -------------------------------------------------

            used_rooms = room_usage.setdefault(
                candidate_timeslot_id,
                set()
            )

            # -------------------------------------------------
            # Find suitable rooms that are currently free.
            # -------------------------------------------------

            free_candidates = [
                room
                for room in resource_candidates
                if room["room_id"]
                not in used_rooms
            ]

            # No room available here.
            # Try another timeslot.
            if not free_candidates:
                continue

            # -------------------------------------------------
            # Prefer the smallest suitable room.
            #
            # This preserves larger rooms for courses that
            # actually need them.
            # -------------------------------------------------

            selected_room = min(
                free_candidates,
                key=lambda room: (
                    room["capacity"],
                    room["room_id"]
                )
            )

            selected_timeslot_id = (
                candidate_timeslot_id
            )

            break

        # =====================================================
        # No valid room/timeslot combination
        # =====================================================

        if selected_room is None:

            unplaced.append({
                "course_id": course_id,
                "code": course["code"],
                "title": course["title"],
                "reason_code": "OTHER",
                "detail": (
                    "No legal timeslot has a free room "
                    "that satisfies the course requirements"
                )
            })

            assigned_timeslots.pop(
                course_id,
                None
            )

            continue

        # =====================================================
        # Commit room assignment
        # =====================================================

        used_rooms = room_usage.setdefault(
            selected_timeslot_id,
            set()
        )

        used_rooms.add(
            selected_room["room_id"]
        )

        # -----------------------------------------------------
        # Record the possibly changed timeslot.
        # -----------------------------------------------------

        assigned_timeslots[
            course_id
        ] = selected_timeslot_id

        # -----------------------------------------------------
        # Get complete timeslot information.
        # -----------------------------------------------------

        selected_timeslot = (
            timeslot_lookup.get(
                selected_timeslot_id
            )
        )

        if selected_timeslot is None:

            unplaced.append({
                "course_id": course_id,
                "code": course["code"],
                "title": course["title"],
                "reason_code": "OTHER",
                "detail": (
                    "Selected timeslot data "
                    "could not be found"
                )
            })

            assigned_timeslots.pop(
                course_id,
                None
            )

            continue

        # =====================================================
        # Add final placed record
        # =====================================================

        placed.append({
            **item,

            "timeslot_id":
                selected_timeslot_id,

            "timeslot_label":
                selected_timeslot["label"],

            "day_of_week":
                selected_timeslot[
                    "day_of_week"
                ],

            "start_time":
                selected_timeslot[
                    "start_time"
                ],

            "end_time":
                selected_timeslot[
                    "end_time"
                ],

            "lecturer":
                course.get(
                    "lecturer"
                ),

            "room_id":
                selected_room[
                    "room_id"
                ],

            "room_code":
                selected_room[
                    "code"
                ],

            "room_capacity":
                selected_room[
                    "capacity"
                ]
        })

    # =========================================================
    # Return result
    # =========================================================

    return {
        "placed": placed,
        "unplaced": unplaced
    }