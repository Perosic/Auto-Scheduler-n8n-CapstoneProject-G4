"""
db_loader.py

Loads all scheduling data required by the timetable scheduler
from PostgreSQL.

The returned data structure is designed to work with:
    - graph.py
    - dsatur.py
    - room_assigner.py
    - verifier.py
"""

import os
from typing import Dict, Any

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv


# ------------------------------------------------------------
# Environment
# ------------------------------------------------------------

load_dotenv()


# ------------------------------------------------------------
# PostgreSQL connection
# ------------------------------------------------------------

def get_connection():
    """
    Create a PostgreSQL database connection.

    Environment variables:
        POSTGRES_HOST
        POSTGRES_PORT
        POSTGRES_DB
        POSTGRES_USER
        POSTGRES_PASSWORD
    """

    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "auto_scheduler"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv(
            "POSTGRES_PASSWORD",
            "postgrespassword"
        ),
    )


# ------------------------------------------------------------
# Load data from PostgreSQL
# ------------------------------------------------------------

def load_from_postgres() -> Dict[str, Any]:
    """
    Load all data required by the scheduling algorithm.

    Important:
        instructor_id comes from the sections table, not courses.

    The returned 'courses' list therefore contains:
        course_id
        code
        title
        expected_enrolment
        requires_lab
        min_capacity
        section_id
        section_code
        instructor_id
        lecturer
        duration_slots
    """

    conn = None
    cur = None

    try:
        conn = get_connection()

        cur = conn.cursor(
            cursor_factory=RealDictCursor
        )

        # ----------------------------------------------------
        # 1. Courses + sections + instructors
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT
                c.course_id,
                c.code,
                c.title,
                c.expected_enrolment,
                c.requires_lab,
                c.min_capacity,

                s.section_id,
                s.section_code,
                s.instructor_id,
                i.full_name AS lecturer,
                s.duration_slots

            FROM courses c

            JOIN sections s
                ON s.course_id = c.course_id

            LEFT JOIN instructors i
                ON i.instructor_id = s.instructor_id

            ORDER BY
                c.course_id,
                s.section_id;
            """
        )

        courses = cur.fetchall()

        # ----------------------------------------------------
        # 2. Rooms
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT
                room_id,
                code,
                capacity,
                is_lab
            FROM rooms
            ORDER BY room_id;
            """
        )

        rooms = cur.fetchall()

        # ----------------------------------------------------
        # 3. Timeslots
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT
                timeslot_id,
                label,
                day_of_week,
                start_time,
                end_time
            FROM timeslots
            ORDER BY timeslot_id;
            """
        )

        timeslots = cur.fetchall()

        # ----------------------------------------------------
        # 4. Co-enrolment conflicts
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT
                course_id_a,
                course_id_b
            FROM course_co_enrolment
            ORDER BY
                course_id_a,
                course_id_b;
            """
        )

        co_enrolments = cur.fetchall()

        # ----------------------------------------------------
        # 5. Allowed timeslots
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT
                course_id,
                timeslot_id
            FROM course_allowed_timeslot
            ORDER BY
                course_id,
                timeslot_id;
            """
        )

        allowed_timeslots = cur.fetchall()

        # ----------------------------------------------------
        # 6. Course equipment requirements
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT
                cer.course_id,
                e.name AS equipment_name

            FROM course_equipment_req cer

            JOIN equipment e
                ON e.equipment_id = cer.equipment_id

            ORDER BY
                cer.course_id,
                e.name;
            """
        )

        equipment_reqs = cur.fetchall()

        # ----------------------------------------------------
        # 7. Room equipment
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT
                re.room_id,
                e.name AS equipment_name

            FROM room_equipment re

            JOIN equipment e
                ON e.equipment_id = re.equipment_id

            ORDER BY
                re.room_id,
                e.name;
            """
        )

        room_equipment = cur.fetchall()

        # ----------------------------------------------------
        # Convert RealDictRow -> normal dictionaries
        # ----------------------------------------------------

        data = {
            "courses": [
                dict(row)
                for row in courses
            ],

            "rooms": [
                dict(row)
                for row in rooms
            ],

            "timeslots": [
                dict(row)
                for row in timeslots
            ],

            "co_enrolments": [
                dict(row)
                for row in co_enrolments
            ],

            "allowed_timeslots": [
                dict(row)
                for row in allowed_timeslots
            ],

            "equipment_reqs": [
                dict(row)
                for row in equipment_reqs
            ],

            "room_equipment": [
                dict(row)
                for row in room_equipment
            ],
        }

        return data

    finally:

        if cur is not None:
            cur.close()

        if conn is not None:
            conn.close()


# ------------------------------------------------------------
# Main loader
# ------------------------------------------------------------

def load_data() -> Dict[str, Any]:
    """
    Main entry point used by the scheduler.

    PostgreSQL is required.
    """

    try:

        data = load_from_postgres()

        print(
            "[db_loader] Loaded "
            f"{len(data['courses'])} course-sections, "
            f"{len(data['rooms'])} rooms, "
            f"{len(data['timeslots'])} timeslots, "
            f"{len(data['co_enrolments'])} conflicts"
        )

        return data

    except psycopg2.Error as e:

        raise RuntimeError(
            "Could not connect to PostgreSQL.\n"
            "\n"
            "Make sure your Docker containers are running:\n"
            "    docker compose up -d\n"
            "\n"
            "Check that PostgreSQL is available on:\n"
            "    localhost:5432\n"
            "\n"
            f"Original PostgreSQL error: {e}"
        ) from e

    except Exception as e:

        raise RuntimeError(
            "Could not load scheduling data from PostgreSQL.\n"
            f"Original error: {e}"
        ) from e


# ------------------------------------------------------------
# Debug / quick test
# ------------------------------------------------------------

def print_debug_data(data: Dict[str, Any]):
    """
    Print the loaded data in a human-readable format.

    Useful for checking that instructor_id and section_id
    are being loaded correctly.
    """

    print()
    print("=" * 70)
    print("COURSES / SECTIONS")
    print("=" * 70)

    for course in data["courses"]:

        print(
            f"course_id={course['course_id']} | "
            f"section_id={course['section_id']} | "
            f"code={course['code']} | "
            f"section={course['section_code']} | "
            f"instructor_id={course['instructor_id']} | "
            f"lecturer={course['lecturer']} | "
            f"duration={course['duration_slots']}"
        )

    print()
    print("=" * 70)
    print("ROOMS")
    print("=" * 70)

    for room in data["rooms"]:

        print(
            f"room_id={room['room_id']} | "
            f"code={room['code']} | "
            f"capacity={room['capacity']} | "
            f"is_lab={room['is_lab']}"
        )

    print()
    print("=" * 70)
    print("TIMESLOTS")
    print("=" * 70)

    for slot in data["timeslots"]:

        print(
            f"timeslot_id={slot['timeslot_id']} | "
            f"{slot['label']} | "
            f"{slot['day_of_week']} | "
            f"{slot['start_time']} - {slot['end_time']}"
        )

    print()
    print("=" * 70)
    print("CO-ENROLMENT CONFLICTS")
    print("=" * 70)

    for conflict in data["co_enrolments"]:

        print(
            f"{conflict['course_id_a']} "
            f"<-> "
            f"{conflict['course_id_b']}"
        )

    print()
    print("=" * 70)
    print("ALLOWED TIMESLOTS")
    print("=" * 70)

    for row in data["allowed_timeslots"]:

        print(
            f"course_id={row['course_id']} | "
            f"timeslot_id={row['timeslot_id']}"
        )

    print()
    print("=" * 70)
    print("EQUIPMENT REQUIREMENTS")
    print("=" * 70)

    for row in data["equipment_reqs"]:

        print(
            f"course_id={row['course_id']} | "
            f"equipment={row['equipment_name']}"
        )

    print()
    print("=" * 70)
    print("ROOM EQUIPMENT")
    print("=" * 70)

    for row in data["room_equipment"]:

        print(
            f"room_id={row['room_id']} | "
            f"equipment={row['equipment_name']}"
        )

    print()
    print("=" * 70)


# ------------------------------------------------------------
# Run directly
# ------------------------------------------------------------

if __name__ == "__main__":

    data = load_data()

    print_debug_data(data)