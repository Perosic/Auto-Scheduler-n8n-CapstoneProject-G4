def _build_allowed_timeslot_map(allowed_timeslots, all_timeslot_ids):
    """
    Build a lookup of explicitly allowed timeslots for each course.

    Example:
        {
            24: {1},
            25: {1},
            26: {1, 2}
        }

    If a course has no entry in allowed_timeslots,
    it can use any available timeslot.
    """

    allowed_map = {}

    for row in allowed_timeslots:
        course_id = row["course_id"]
        timeslot_id = row["timeslot_id"]

        allowed_map.setdefault(course_id, set()).add(timeslot_id)

    all_slots = set(all_timeslot_ids)

    return allowed_map, all_slots


def dsatur_schedule(graph, courses, timeslots, allowed_timeslots):
    """
    Schedule courses using the DSATUR algorithm.

    Rules:
    1. Conflicting courses cannot share a timeslot.
    2. Explicit allowed-timeslot restrictions must be respected.
    3. Courses without restrictions may use any timeslot.
    4. If no legal timeslot exists, the course is UNPLACED.
    """

    # ---------------------------------------------------------
    # 1. Get all available timeslot IDs
    # ---------------------------------------------------------

    all_timeslot_ids = [
        timeslot["timeslot_id"]
        for timeslot in timeslots
    ]

    # ---------------------------------------------------------
    # 2. Build allowed-timeslot lookup
    # ---------------------------------------------------------

    explicit_allowed, all_slots = _build_allowed_timeslot_map(
        allowed_timeslots,
        all_timeslot_ids
    )

    # ---------------------------------------------------------
    # 3. Course lookup
    # ---------------------------------------------------------

    course_lookup = {
        course["course_id"]: course
        for course in courses
    }

    # ---------------------------------------------------------
    # 4. Store assigned courses separately
    #
    # IMPORTANT:
    # An unplaced course is NOT considered to have a color.
    # ---------------------------------------------------------

    assigned = {}

    unplaced_ids = set()

    # Courses still needing processing
    remaining = set(graph.keys())

    # ---------------------------------------------------------
    # 5. Helper: get allowed timeslots for a course
    # ---------------------------------------------------------

    def get_allowed_slots(course_id):

        if course_id in explicit_allowed:
            return explicit_allowed[course_id]

        return all_slots

    # ---------------------------------------------------------
    # 6. DSATUR loop
    # ---------------------------------------------------------

    while remaining:

        # -----------------------------------------------------
        # Calculate DSATUR priority.
        #
        # Saturation =
        # number of DIFFERENT timeslots used by already
        # assigned neighboring courses.
        #
        # Degree =
        # number of conflicts this course has.
        # -----------------------------------------------------

        def priority(course_id):

            neighbor_timeslots = {
                assigned[neighbor]
                for neighbor in graph[course_id]
                if neighbor in assigned
            }

            saturation = len(neighbor_timeslots)
            degree = len(graph[course_id])

            return saturation, degree

        # -----------------------------------------------------
        # Choose the next course.
        # Highest saturation first.
        # Degree breaks ties.
        # Course ID gives deterministic final tie-break.
        # -----------------------------------------------------

        selected_course = max(
            remaining,
            key=lambda course_id: (
                priority(course_id)[0],
                priority(course_id)[1],
                -course_id
            )
        )

        # -----------------------------------------------------
        # Find timeslots already used by its assigned neighbors
        # -----------------------------------------------------

        neighbor_timeslots = {
            assigned[neighbor]
            for neighbor in graph[selected_course]
            if neighbor in assigned
        }

        # -----------------------------------------------------
        # Find legal timeslots
        # -----------------------------------------------------

        candidates = (
            get_allowed_slots(selected_course)
            - neighbor_timeslots
        )

        # -----------------------------------------------------
        # Assign a timeslot if possible
        # -----------------------------------------------------

        if candidates:

            selected_timeslot = min(candidates)

            assigned[selected_course] = selected_timeslot

        else:

            # No legal timeslot exists.
            #
            # IMPORTANT:
            # We do NOT put this course into "assigned".
            # It therefore does not affect the saturation
            # calculation for other courses.

            unplaced_ids.add(selected_course)

        remaining.remove(selected_course)

    # ---------------------------------------------------------
    # 7. Build final schedule
    # ---------------------------------------------------------

    timeslot_lookup = {
        timeslot["timeslot_id"]: timeslot
        for timeslot in timeslots
    }

    schedule = []

    for course_id, timeslot_id in sorted(assigned.items()):

        course = course_lookup[course_id]
        timeslot = timeslot_lookup[timeslot_id]

        schedule.append({
            "course_id": course_id,
            "code": course["code"],
            "title": course["title"],
            "timeslot_id": timeslot_id,
            "timeslot_label": timeslot["label"],
            "day_of_week": timeslot["day_of_week"],
            "start_time": timeslot["start_time"],
            "end_time": timeslot["end_time"]
        })

    # ---------------------------------------------------------
    # 8. Build unplaced list
    # ---------------------------------------------------------

    unplaced = []

    for course_id in sorted(unplaced_ids):

        course = course_lookup[course_id]

        unplaced.append({
            "course_id": course_id,
            "code": course["code"],
            "title": course["title"],
            "reason": "No legal timeslot available"
        })

    # ---------------------------------------------------------
    # 9. Return result
    # ---------------------------------------------------------

    return {
        "schedule": schedule,
        "unplaced": unplaced
    }