"""
graph.py

Builds the conflict graph used by the DSATUR scheduler.

A node represents one course-section.

An edge between two nodes means:
    - the courses cannot be scheduled in the same timeslot.

Conflicts come from:
    1. Explicit student/co-enrolment conflicts.
    2. Shared instructor conflicts.
"""


from collections import defaultdict


def build_conflict_graph(courses, co_enrolments):
    """
    Build an undirected conflict graph.

    Parameters
    ----------
    courses : list[dict]
        Course-section records loaded from the database.

        Each course should contain at least:
            course_id
            instructor_id

    co_enrolments : list[dict]
        Explicit student/co-enrolment conflicts.

        Each row should contain:
            course_id_a
            course_id_b

    Returns
    -------
    dict[int, set[int]]
        Example:

        {
            1: {2, 3},
            2: {1},
            3: {1}
        }

        If course A has an edge to course B, they cannot
        use the same timeslot.
    """

    # =========================================================
    # 1. Create a node for every course
    # =========================================================

    graph = {
        course["course_id"]: set()
        for course in courses
    }

    # =========================================================
    # 2. Add explicit co-enrolment conflicts
    # =========================================================

    for conflict in co_enrolments:

        course_a = conflict["course_id_a"]
        course_b = conflict["course_id_b"]

        # -----------------------------------------------------
        # Validate course IDs
        # -----------------------------------------------------

        if course_a not in graph:
            raise ValueError(
                f"Unknown course_id in co_enrolments: {course_a}"
            )

        if course_b not in graph:
            raise ValueError(
                f"Unknown course_id in co_enrolments: {course_b}"
            )

        # -----------------------------------------------------
        # Ignore self-conflicts
        # -----------------------------------------------------

        if course_a == course_b:
            continue

        # -----------------------------------------------------
        # Undirected edge
        # -----------------------------------------------------

        graph[course_a].add(course_b)
        graph[course_b].add(course_a)

    # =========================================================
    # 3. Add instructor conflicts
    # =========================================================
    #
    # If the same instructor teaches two courses, those
    # courses cannot occupy the same timeslot.
    #
    # Example:
    #
    # Dr. Ada teaches:
    #   CSC101
    #   CSC201
    #   CSC301
    #
    # Therefore:
    #
    # CSC101 <-> CSC201
    # CSC101 <-> CSC301
    # CSC201 <-> CSC301
    #
    # =========================================================

    instructor_courses = defaultdict(list)

    for course in courses:

        course_id = course["course_id"]
        instructor_id = course.get("instructor_id")

        # -----------------------------------------------------
        # Courses without an instructor do not create an
        # instructor conflict.
        # -----------------------------------------------------

        if instructor_id is None:
            continue

        instructor_courses[instructor_id].append(course_id)

    # ---------------------------------------------------------
    # Create pairwise conflicts for each instructor
    # ---------------------------------------------------------

    for instructor_id, course_ids in instructor_courses.items():

        for i in range(len(course_ids)):

            for j in range(i + 1, len(course_ids)):

                course_a = course_ids[i]
                course_b = course_ids[j]

                if course_a == course_b:
                    continue

                graph[course_a].add(course_b)
                graph[course_b].add(course_a)

    # =========================================================
    # 4. Return graph
    # =========================================================

    return graph


if __name__ == "__main__":
    # Simple standalone test.
    #
    # This does NOT connect to the database.
    # It is only here to verify the graph logic.

    test_courses = [
        {
            "course_id": 1,
            "instructor_id": 10,
        },
        {
            "course_id": 2,
            "instructor_id": 10,
        },
        {
            "course_id": 3,
            "instructor_id": 20,
        },
        {
            "course_id": 4,
            "instructor_id": 30,
        },
    ]

    test_co_enrolments = [
        {
            "course_id_a": 3,
            "course_id_b": 4,
        }
    ]

    test_graph = build_conflict_graph(
        test_courses,
        test_co_enrolments,
    )

    print("Conflict graph:")

    for course_id in sorted(test_graph):
        print(
            f"course {course_id} -> "
            f"{sorted(test_graph[course_id])}"
        )