-- ============================================================
-- seed_data.sql  (Person A / Day 1)
-- 25 courses + 3 deliberately unplaceable cases
-- These 3 cases are intentional test fixtures – do NOT remove.
-- ============================================================

-- Departments
INSERT INTO departments (code, name) VALUES
('CSC', 'Computer Science'),
('MTH', 'Mathematics'),
('PHY', 'Physics'),
('ENG', 'Engineering');

-- Timeslots (Mon–Fri, 5 slots/day = 25 total)
INSERT INTO timeslots (day_of_week, start_time, end_time, label) VALUES
('Mon', '09:00', '10:00', 'Mon-09:00'),
('Mon', '10:00', '11:00', 'Mon-10:00'),
('Mon', '11:00', '12:00', 'Mon-11:00'),
('Mon', '13:00', '14:00', 'Mon-13:00'),
('Mon', '14:00', '15:00', 'Mon-14:00'),
('Tue', '09:00', '10:00', 'Tue-09:00'),
('Tue', '10:00', '11:00', 'Tue-10:00'),
('Tue', '11:00', '12:00', 'Tue-11:00'),
('Tue', '13:00', '14:00', 'Tue-13:00'),
('Tue', '14:00', '15:00', 'Tue-14:00'),
('Wed', '09:00', '10:00', 'Wed-09:00'),
('Wed', '10:00', '11:00', 'Wed-10:00'),
('Wed', '11:00', '12:00', 'Wed-11:00'),
('Wed', '13:00', '14:00', 'Wed-13:00'),
('Wed', '14:00', '15:00', 'Wed-14:00'),
('Thu', '09:00', '10:00', 'Thu-09:00'),
('Thu', '10:00', '11:00', 'Thu-10:00'),
('Thu', '11:00', '12:00', 'Thu-11:00'),
('Thu', '13:00', '14:00', 'Thu-13:00'),
('Thu', '14:00', '15:00', 'Thu-14:00'),
('Fri', '09:00', '10:00', 'Fri-09:00'),
('Fri', '10:00', '11:00', 'Fri-10:00'),
('Fri', '11:00', '12:00', 'Fri-11:00'),
('Fri', '13:00', '14:00', 'Fri-13:00'),
('Fri', '14:00', '15:00', 'Fri-14:00');

-- Rooms (note: largest room capacity is 80)
INSERT INTO rooms (code, building, capacity, is_lab, notes) VALUES
('LT1',  'Main', 80,  FALSE, 'Large lecture theatre'),
('LT2',  'Main', 60,  FALSE, NULL),
('CR101','Block A', 40, FALSE, NULL),
('CR102','Block A', 35, FALSE, NULL),
('CR201','Block B', 30, FALSE, NULL),
('LAB1', 'Science', 25, TRUE,  'Computer lab – only lab room'),
('LAB2', 'Science', 20, TRUE,  'Physics lab');

-- Equipment
INSERT INTO equipment (name, description) VALUES
('projector', 'Digital projector'),
('whiteboard', 'Large whiteboard'),
('computers', 'Student workstations'),
('lab_benches', 'Physics / chemistry benches');

-- Room equipment mapping
INSERT INTO room_equipment (room_id, equipment_id)
SELECT r.room_id, e.equipment_id
FROM rooms r, equipment e
WHERE (r.code IN ('LT1','LT2','CR101') AND e.name IN ('projector','whiteboard'))
   OR (r.code = 'LAB1' AND e.name IN ('computers','projector'))
   OR (r.code = 'LAB2' AND e.name IN ('lab_benches','whiteboard'));

-- Instructors
INSERT INTO instructors (staff_id, full_name, email, department_id, max_hours_week) VALUES
('S001', 'Dr. Ada Okonkwo',   'ada.okonkwo@uni.edu', 1, 16),
('S002', 'Prof. Chidi Eze',   'chidi.eze@uni.edu',   1, 12),
('S003', 'Dr. Fatima Bello',  'fatima.bello@uni.edu',2, 14),
('S004', 'Mr. Ibrahim Musa',  'ibrahim.musa@uni.edu',3, 18),
('S005', 'Dr. Ngozi Uche',    'ngozi.uche@uni.edu',  4, 15);

-- ============================================================
-- COURSES (22 normal + 3 deliberate unplaceable)
-- ============================================================

-- Normal placeable courses
INSERT INTO courses (code, title, department_id, credits, is_lab, expected_enrolment, requires_lab, min_capacity, notes) VALUES
('CSC101', 'Intro to Programming',          1, 3, FALSE, 55, FALSE, 50, NULL),
('CSC201', 'Data Structures',               1, 3, FALSE, 45, FALSE, 40, NULL),
('CSC301', 'Algorithms',                    1, 3, FALSE, 35, FALSE, 30, NULL),
('CSC302', 'Database Systems',              1, 3, FALSE, 40, FALSE, 35, NULL),
('CSC401', 'Software Engineering',          1, 3, FALSE, 30, FALSE, 25, NULL),
('MTH101', 'Calculus I',                    2, 3, FALSE, 70, FALSE, 60, NULL),
('MTH201', 'Linear Algebra',                2, 3, FALSE, 50, FALSE, 40, NULL),
('MTH301', 'Discrete Mathematics',          2, 3, FALSE, 40, FALSE, 35, NULL),
('PHY101', 'General Physics',               3, 3, FALSE, 60, FALSE, 50, NULL),
('PHY201', 'Electromagnetism',              3, 3, FALSE, 35, FALSE, 30, NULL),
('ENG101', 'Engineering Drawing',           4, 2, FALSE, 45, FALSE, 40, NULL),
('ENG201', 'Mechanics of Materials',        4, 3, FALSE, 30, FALSE, 25, NULL),
('CSC210', 'Object-Oriented Programming',   1, 3, FALSE, 40, FALSE, 35, NULL),
('CSC310', 'Operating Systems',             1, 3, FALSE, 35, FALSE, 30, NULL),
('CSC320', 'Computer Networks',             1, 3, FALSE, 30, FALSE, 25, NULL),
('MTH210', 'Probability & Statistics',      2, 3, FALSE, 45, FALSE, 40, NULL),
('PHY210', 'Optics',                        3, 3, FALSE, 25, FALSE, 20, NULL),
('ENG210', 'Thermodynamics',                4, 3, FALSE, 35, FALSE, 30, NULL),
('CSC110', 'Web Development Basics',        1, 2, FALSE, 50, FALSE, 40, NULL),
('MTH110', 'Introduction to Logic',         2, 2, FALSE, 40, FALSE, 30, NULL),
('CSC220', 'Mobile App Development',        1, 3, FALSE, 30, FALSE, 25, NULL),
('ENG110', 'Introduction to CAD',           4, 2, FALSE, 25, FALSE, 20, NULL);

-- ============================================================
-- 3 DELIBERATE UNPLACEABLE CASES (required by Masterplan)
-- Do NOT remove or "fix" these – they prove the conflict path.
-- ============================================================

-- 1. Course too large for ANY available room (max room = 80)
INSERT INTO courses (code, title, department_id, credits, is_lab, expected_enrolment, requires_lab, min_capacity, notes) VALUES
('CSC999', 'Massive Open Seminar (UNPLACEABLE)', 1, 1, FALSE, 150, FALSE, 150,
 'DELIBERATE FAILURE: expected_enrolment 150 > largest room capacity 80 → ROOM_CAPACITY');

-- 2. Two lab courses that both require the single computer lab (LAB1)
--    and share the same instructor → impossible to schedule both
INSERT INTO courses (code, title, department_id, credits, is_lab, expected_enrolment, requires_lab, min_capacity, notes) VALUES
('CSC351', 'Advanced Programming Lab A (UNPLACEABLE)', 1, 1, TRUE, 22, TRUE, 20,
 'DELIBERATE FAILURE: competes with CSC352 for the only computer lab + same instructor'),
('CSC352', 'Advanced Programming Lab B (UNPLACEABLE)', 1, 1, TRUE, 22, TRUE, 20,
 'DELIBERATE FAILURE: competes with CSC351 for the only computer lab + same instructor');

-- 3. Co-enrolled clique with too few available slots
--    Three courses that all pairwise conflict and need distinct slots,
--    but we will force them into a tiny set of possible times via other constraints.
INSERT INTO courses (code, title, department_id, credits, is_lab, expected_enrolment, requires_lab, min_capacity, notes) VALUES
('MTH401', 'Graph Theory (UNPLACEABLE clique)',     2, 3, FALSE, 25, FALSE, 20,
 'DELIBERATE FAILURE: part of co-enrolment clique with too few free slots'),
('MTH402', 'Combinatorics (UNPLACEABLE clique)',    2, 3, FALSE, 25, FALSE, 20,
 'DELIBERATE FAILURE: part of co-enrolment clique with too few free slots'),
('MTH403', 'Number Theory (UNPLACEABLE clique)',    2, 3, FALSE, 25, FALSE, 20,
 'DELIBERATE FAILURE: part of co-enrolment clique with too few free slots');

-- Sections for normal courses (one section each for simplicity)
INSERT INTO sections (course_id, section_code, instructor_id, duration_slots)
SELECT c.course_id, 'A',
       CASE
         WHEN c.department_id = 1 THEN 1
         WHEN c.department_id = 2 THEN 3
         WHEN c.department_id = 3 THEN 4
         ELSE 5
       END,
       1
FROM courses c
WHERE c.code NOT LIKE '%UNPLACEABLE%'
  AND c.code NOT IN ('CSC351','CSC352','MTH401','MTH402','MTH403');

-- Sections for the deliberate failures
INSERT INTO sections (course_id, section_code, instructor_id, duration_slots)
SELECT course_id, 'A', 1, 1 FROM courses WHERE code = 'CSC999';

INSERT INTO sections (course_id, section_code, instructor_id, duration_slots)
SELECT course_id, 'A', 2, 1 FROM courses WHERE code IN ('CSC351','CSC352');  -- same instructor

INSERT INTO sections (course_id, section_code, instructor_id, duration_slots)
SELECT course_id, 'A', 3, 1 FROM courses WHERE code IN ('MTH401','MTH402','MTH403');

-- Co-enrolment clique (all three pairwise conflict)
INSERT INTO course_co_enrolment (course_id_a, course_id_b)
SELECT a.course_id, b.course_id
FROM courses a, courses b
WHERE a.code = 'MTH401' AND b.code = 'MTH402'
UNION ALL
SELECT a.course_id, b.course_id
FROM courses a, courses b
WHERE a.code = 'MTH401' AND b.code = 'MTH403'
UNION ALL
SELECT a.course_id, b.course_id
FROM courses a, courses b
WHERE a.code = 'MTH402' AND b.code = 'MTH403';

-- Equipment requirements for lab courses
INSERT INTO course_equipment_req (course_id, equipment_id)
SELECT c.course_id, e.equipment_id
FROM courses c, equipment e
WHERE c.code IN ('CSC351','CSC352') AND e.name = 'computers';

-- ============================================================
-- Summary for verification
-- ============================================================
-- Normal courses: 22
-- Deliberate failures:
--   1. CSC999          → ROOM_CAPACITY (150 > 80)
--   2. CSC351 + CSC352 → ROOM_EQUIPMENT / lab contention + same instructor
--   3. MTH401/402/403  → CO_ENROLMENT clique
-- Total courses: 25
