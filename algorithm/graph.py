from collections import defaultdict


def build_conflict_graph(courses, co_enrolments):
    """
    Build an undirected conflict graph.

    Each course-section is a node.
    An edge means the two course-sections cannot
    occupy the same timeslot.
    """

    graph = {course["course_id"]: set() for course in courses}

    # -------------------------------------------------
    # 1. Co-enrolment conflicts
    # -------------------------------------------------

    for conflict in co_enrolments:
        course_a = conflict["course_id_a"]
        course_b = conflict["course_id_b"]

        if course_a not in graph:
            raise ValueError(
                f"Unknown course_id in co_enrolments: {course_a}"
            )

        if course_b not in graph:
            raise ValueError(
                f"Unknown course_id in co_enrolments: {course_b}"
            )

        graph[course_a].add(course_b)
        graph[course_b].add(course_a)

    # -------------------------------------------------
    # 2. Instructor conflicts
    # -------------------------------------------------

    instructor_courses = defaultdict(list)

    for course in courses:
        instructor_id = course.get("instructor_id")

        if instructor_id is not None:
            instructor_courses[instructor_id].append(
                course["course_id"]
            )

    for course_ids in instructor_courses.values():

        for i in range(len(course_ids)):
            for j in range(i + 1, len(course_ids)):

                course_a = course_ids[i]
                course_b = course_ids[j]

                graph[course_a].add(course_b)
                graph[course_b].add(course_a)

    return graph