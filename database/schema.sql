-- ============================================================
-- Course Timetable Auto-Scheduler
-- schema.sql  (Person A / Day 1)
-- Aligned with Masterplan v3 data contracts
-- ============================================================

-- Drop in reverse dependency order (safe for re-init)
DROP TABLE IF EXISTS course_allowed_timeslot CASCADE;
DROP TABLE IF EXISTS course_co_enrolment CASCADE;
DROP TABLE IF EXISTS course_equipment_req CASCADE;
DROP TABLE IF EXISTS room_equipment CASCADE;
DROP TABLE IF EXISTS equipment CASCADE;
DROP TABLE IF EXISTS sections CASCADE;
DROP TABLE IF EXISTS courses CASCADE;
DROP TABLE IF EXISTS instructors CASCADE;
DROP TABLE IF EXISTS rooms CASCADE;
DROP TABLE IF EXISTS timeslots CASCADE;
DROP TABLE IF EXISTS departments CASCADE;

-- ----------------------------------------------------------
-- Reference tables
-- ----------------------------------------------------------
CREATE TABLE departments (
    department_id   SERIAL PRIMARY KEY,
    code            VARCHAR(10) NOT NULL UNIQUE,
    name            VARCHAR(100) NOT NULL
);

CREATE TABLE timeslots (
    timeslot_id     SERIAL PRIMARY KEY,
    day_of_week     VARCHAR(10) NOT NULL,   -- Mon, Tue, Wed, Thu, Fri
    start_time      TIME NOT NULL,
    end_time        TIME NOT NULL,
    label           VARCHAR(20) NOT NULL UNIQUE,  -- e.g. Mon-09:00
    CONSTRAINT valid_day CHECK (day_of_week IN ('Mon','Tue','Wed','Thu','Fri')),
    CONSTRAINT valid_range CHECK (end_time > start_time)
);

CREATE TABLE rooms (
    room_id         SERIAL PRIMARY KEY,
    code            VARCHAR(20) NOT NULL UNIQUE,
    building        VARCHAR(50),
    capacity        INTEGER NOT NULL CHECK (capacity > 0),
    is_lab          BOOLEAN NOT NULL DEFAULT FALSE,
    notes           TEXT
);

CREATE TABLE equipment (
    equipment_id    SERIAL PRIMARY KEY,
    name            VARCHAR(50) NOT NULL UNIQUE,  -- projector, whiteboard, computers, etc.
    description     TEXT
);

CREATE TABLE room_equipment (
    room_id         INTEGER NOT NULL REFERENCES rooms(room_id) ON DELETE CASCADE,
    equipment_id    INTEGER NOT NULL REFERENCES equipment(equipment_id) ON DELETE CASCADE,
    PRIMARY KEY (room_id, equipment_id)
);

CREATE TABLE instructors (
    instructor_id   SERIAL PRIMARY KEY,
    staff_id        VARCHAR(20) NOT NULL UNIQUE,
    full_name       VARCHAR(100) NOT NULL,
    email           VARCHAR(120),
    department_id   INTEGER REFERENCES departments(department_id),
    max_hours_week  INTEGER DEFAULT 20
);

-- ----------------------------------------------------------
-- Core academic entities
-- ----------------------------------------------------------
CREATE TABLE courses (
    course_id       SERIAL PRIMARY KEY,
    code            VARCHAR(20) NOT NULL UNIQUE,   -- e.g. CSC301
    title           VARCHAR(150) NOT NULL,
    department_id   INTEGER REFERENCES departments(department_id),
    credits         INTEGER DEFAULT 3,
    is_lab          BOOLEAN NOT NULL DEFAULT FALSE,
    expected_enrolment INTEGER NOT NULL CHECK (expected_enrolment > 0),
    -- Explicit hard-constraint flags (used by algorithm)
    requires_lab    BOOLEAN NOT NULL DEFAULT FALSE,
    min_capacity    INTEGER,                       -- must fit in a room of at least this size
    notes           TEXT
);

CREATE TABLE sections (
    section_id      SERIAL PRIMARY KEY,
    course_id       INTEGER NOT NULL REFERENCES courses(course_id) ON DELETE CASCADE,
    section_code    VARCHAR(10) NOT NULL,          -- A, B, Lab1, etc.
    instructor_id   INTEGER REFERENCES instructors(instructor_id),
    duration_slots  INTEGER NOT NULL DEFAULT 1,    -- how many consecutive timeslots needed
    UNIQUE (course_id, section_code)
);

-- Many-to-many: courses that cannot share a timeslot (co-enrolment / student clash)
CREATE TABLE course_co_enrolment (
    course_id_a     INTEGER NOT NULL REFERENCES courses(course_id) ON DELETE CASCADE,
    course_id_b     INTEGER NOT NULL REFERENCES courses(course_id) ON DELETE CASCADE,
    PRIMARY KEY (course_id_a, course_id_b),
    CONSTRAINT ordered_pair CHECK (course_id_a < course_id_b)
);

-- Equipment required by a course
CREATE TABLE course_equipment_req (
    course_id       INTEGER NOT NULL REFERENCES courses(course_id) ON DELETE CASCADE,
    equipment_id    INTEGER NOT NULL REFERENCES equipment(equipment_id) ON DELETE CASCADE,
    PRIMARY KEY (course_id, equipment_id)
);
-- Optional hard constraint:
-- if a course has rows here, it may ONLY be scheduled
-- in those listed timeslots.
-- No rows means the course is unrestricted by timeslot.
CREATE TABLE course_allowed_timeslot (
    course_id       INTEGER NOT NULL REFERENCES courses(course_id) ON DELETE CASCADE,
    timeslot_id     INTEGER NOT NULL REFERENCES timeslots(timeslot_id) ON DELETE CASCADE,
    PRIMARY KEY (course_id, timeslot_id)
);
-- ----------------------------------------------------------
-- Helpful indexes
-- ----------------------------------------------------------
CREATE INDEX idx_sections_course ON sections(course_id);
CREATE INDEX idx_sections_instructor ON sections(instructor_id);
CREATE INDEX idx_rooms_capacity ON rooms(capacity);
CREATE INDEX idx_rooms_is_lab ON rooms(is_lab);

-- ----------------------------------------------------------
-- Comments for collaborators / LLMs
-- ----------------------------------------------------------
COMMENT ON TABLE courses IS 'Normalized course list. Algorithm receives this + instructor IDs + room capacities + hard-constraint flags.';
COMMENT ON COLUMN courses.requires_lab IS 'Hard constraint: must be placed in a lab room';
COMMENT ON COLUMN courses.min_capacity IS 'Hard constraint: room.capacity >= this value';
COMMENT ON TABLE course_co_enrolment IS 'Hard constraint: these two courses cannot share a timeslot';
COMMENT ON TABLE course_allowed_timeslot IS 'Optional hard constraint. If a course appears here, it may only be scheduled in its listed timeslots. No rows means unrestricted.';
