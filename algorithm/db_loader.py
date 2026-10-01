"""
db_loader.py
Loads all scheduling data from PostgreSQL (or falls back to a local JSON if DB is down).
"""

import os
import json
from typing import Dict, List, Any

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

from dotenv import load_dotenv

load_dotenv()


def get_connection():
    """Create a connection to the local Postgres container."""
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "auto_scheduler"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgrespassword"),
    )


def load_from_postgres() -> Dict[str, Any]:
    """Load the full dataset needed by the algorithm from Postgres."""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Courses + sections + instructor
    cur.execute("""
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
            s.duration_slots
        FROM courses c
        JOIN sections s ON s.course_id = c.course_id
        ORDER BY c.course_id;
    """)
    courses = cur.fetchall()

    # Rooms
    cur.execute("""
        SELECT room_id, code, capacity, is_lab
        FROM rooms
        ORDER BY room_id;
    """)
    rooms = cur.fetchall()

    # Timeslots
    cur.execute("""
        SELECT timeslot_id, label, day_of_week, start_time, end_time
        FROM timeslots
        ORDER BY timeslot_id;
    """)
    timeslots = cur.fetchall()

    # Co-enrolment pairs
    cur.execute("""
        SELECT course_id_a, course_id_b
        FROM course_co_enrolment;
    """)
    co_enrolments = cur.fetchall()

    # Allowed timeslots (hard restriction)
    cur.execute("""
        SELECT course_id, timeslot_id
        FROM course_allowed_timeslot;
    """)
    allowed_timeslots = cur.fetchall()

    # Equipment requirements
    cur.execute("""
        SELECT cer.course_id, e.name AS equipment_name
        FROM course_equipment_req cer
        JOIN equipment e ON e.equipment_id = cer.equipment_id;
    """)
    equipment_reqs = cur.fetchall()

    # Room equipment
    cur.execute("""
        SELECT re.room_id, e.name AS equipment_name
        FROM room_equipment re
        JOIN equipment e ON e.equipment_id = re.equipment_id;
    """)
    room_equipment = cur.fetchall()

    cur.close()
    conn.close()

    return {
        "courses": [dict(r) for r in courses],
        "rooms": [dict(r) for r in rooms],
        "timeslots": [dict(r) for r in timeslots],
        "co_enrolments": [dict(r) for r in co_enrolments],
        "allowed_timeslots": [dict(r) for r in allowed_timeslots],
        "equipment_reqs": [dict(r) for r in equipment_reqs],
        "room_equipment": [dict(r) for r in room_equipment],
    }


def load_data() -> Dict[str, Any]:
    """
    Main entry point.
    Tries Postgres first. If it fails, raises a clear error
    (we will add a JSON fallback later if needed).
    """
    if not PSYCOPG2_AVAILABLE:
        raise RuntimeError("psycopg2 is not installed. Run: pip install -r algorithm/requirements.txt")

    try:
        data = load_from_postgres()
        print(f"[db_loader] Loaded {len(data['courses'])} course-sections from Postgres")
        return data
    except Exception as e:
        raise RuntimeError(
            f"Could not connect to Postgres.\n"
            f"Make sure docker compose is running (postgres on localhost:5432).\n"
            f"Original error: {e}"
        )


if __name__ == "__main__":
    # Quick test
    data = load_data()
    print("Courses:", len(data["courses"]))
    print("Rooms:", len(data["rooms"]))
    print("Timeslots:", len(data["timeslots"]))