from algorithm.db_loader import load_data
from algorithm.graph import build_conflict_graph


def main():
    data = load_data()

    graph = build_conflict_graph(
        data["courses"],
        data["co_enrolments"]
    )

    print("\n=== CONFLICT GRAPH ===")

    for course_id in sorted(graph):
        neighbours = sorted(graph[course_id])

        print(
            f"Course {course_id}: "
            f"{len(neighbours)} conflicts -> {neighbours}"
        )


if __name__ == "__main__":
    main()
