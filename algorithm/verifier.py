def verify_schedule(
    schedule,
    courses,
    graph,
    timeslots,
    allowed_timeslots
):
    """
    Independently verify a generated timetable.

    Checks:
    1. Every scheduled course exists.
    2. A course is not scheduled more than once.
    3. Conflicting courses do not share a timeslot.
    4. Explicit allowed-timeslot restrictions are respected.
    5. Every assigned timeslot exists.

    Returns:
        {
            "valid": True/False,
            "errors": [...]
        }
    """

    errors = []

    # ---------------------------------------------------------
    # 1. Build lookup tables
    # ---------------------------------------------------------

    course_lookup = {
        course["course_id"]: course
        for course in courses
    }

    valid_timeslot_ids = {
        timeslot["timeslot_id"]
        for timeslot in timeslots
    }

    allowed_map = {}

    for row in allowed_timeslots:
        allowed_map.setdefault(
            row["course_id"],
            set()
        ).add(row["timeslot_id"])

    # ---------------------------------------------------------
    # 2. Track assignments
    # ---------------------------------------------------------

    assigned_courses = set()
    assignments_by_timeslot = {}

    # ---------------------------------------------------------
    # 3. Check each schedule entry
    # ---------------------------------------------------------

    for item in schedule:

        course_id = item["course_id"]
        timeslot_id = item["timeslot_id"]

        # -----------------------------------------------------
        # Check that course exists
        # -----------------------------------------------------

        if course_id not in course_lookup:
            errors.append(
                f"Unknown course_id: {course_id}"
            )
            continue

        # -----------------------------------------------------
        # Check duplicate course assignment
        # -----------------------------------------------------

        if course_id in assigned_courses:
            errors.append(
                f"Course {course_id} is scheduled more than once"
            )

        assigned_courses.add(course_id)

        # -----------------------------------------------------
        # Check timeslot exists
        # -----------------------------------------------------

        if timeslot_id not in valid_timeslot_ids:
            errors.append(
                f"Course {course_id} uses invalid timeslot "
                f"{timeslot_id}"
            )
            continue

        # -----------------------------------------------------
        # Check explicit allowed-timeslot restriction
        # -----------------------------------------------------

        if course_id in allowed_map:

            if timeslot_id not in allowed_map[course_id]:

                errors.append(
                    f"Course {course_id} is assigned to timeslot "
                    f"{timeslot_id}, but it is not allowed there"
                )

        # -----------------------------------------------------
        # Store assignment by timeslot
        # -----------------------------------------------------

        assignments_by_timeslot.setdefault(
            timeslot_id,
            []
        ).append(course_id)

    # ---------------------------------------------------------
    # 4. Check conflict graph
    #
    # Two conflicting courses must never share a timeslot.
    # ---------------------------------------------------------

    for timeslot_id, course_ids in assignments_by_timeslot.items():

        for i in range(len(course_ids)):

            course_a = course_ids[i]

            for j in range(i + 1, len(course_ids)):

                course_b = course_ids[j]

                if course_b in graph.get(course_a, set()):

                    errors.append(
                        f"Conflict: courses {course_a} and "
                        f"{course_b} share timeslot {timeslot_id}"
                    )

    # ---------------------------------------------------------
    # 5. Final result
    # ---------------------------------------------------------

    return {
        "valid": len(errors) == 0,
        "errors": errors
    }