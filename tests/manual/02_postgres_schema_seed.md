# 02 — PostgreSQL schema & seed verification

**Owner:** Data Engineer  
**Depends on:** `01_docker_stack.md` passed (Postgres healthy)  
**Goal:** Schema and seed load correctly; deliberate conflict fixtures are present and restrictive.

## Connect

```bash
docker exec -it scheduler_db psql -U postgres -d auto_scheduler
```

## Checks (run inside `psql`)

### 1. Core table counts

```sql
SELECT 'departments' AS t, COUNT(*) FROM departments
UNION ALL SELECT 'timeslots', COUNT(*) FROM timeslots
UNION ALL SELECT 'rooms', COUNT(*) FROM rooms
UNION ALL SELECT 'instructors', COUNT(*) FROM instructors
UNION ALL SELECT 'courses', COUNT(*) FROM courses
UNION ALL SELECT 'sections', COUNT(*) FROM sections;
```

**Expected (approx):**
- timeslots = 25
- courses = 28 (22 placeable + 6 fixture courses across 3 conflict scenarios)
- sections ≥ 1 per course (exactly 1 for CSC999)

- [ ] Counts look correct

### 2. Deliberate conflict courses exist

```sql
SELECT code, expected_enrolment, requires_lab, min_capacity, LEFT(notes, 80) AS notes
FROM courses
WHERE code IN ('CSC999', 'CSC351', 'CSC352', 'MTH401', 'MTH402', 'MTH403')
ORDER BY code;
```

- [ ] All six codes present
- [ ] CSC999 has enrolment / min_capacity that exceeds largest room (80)

### 3. `course_allowed_timeslot` restrictions (critical)

```sql
SELECT c.code, t.label
FROM course_allowed_timeslot cat
JOIN courses c ON c.course_id = cat.course_id
JOIN timeslots t ON t.timeslot_id = cat.timeslot_id
ORDER BY c.code, t.label;
```

**Expected (per Data Engineer design):**
- CSC351 and CSC352 → only `Mon-09:00` (shared instructor + lab contention becomes genuine)
- MTH401, MTH402, MTH403 → only `Mon-09:00` and `Mon-10:00` (3 mutual co-enrolments cannot fit in 2 slots)

- [ ] Allowed-timeslot rows match the design above

### 4. Co-enrolment clique

```sql
SELECT a.code AS course_a, b.code AS course_b
FROM course_co_enrolment ce
JOIN courses a ON a.course_id = ce.course_id_a
JOIN courses b ON b.course_id = ce.course_id_b
ORDER BY 1, 2;
```

- [ ] MTH401–MTH402, MTH401–MTH403, MTH402–MTH403 present

### 5. Instructor hour limits (if used)

```sql
SELECT staff_id, full_name, max_hours_week
FROM instructors
ORDER BY staff_id;
```

- [ ] Values match seed intent (document actual values here if different from older drafts)

### 6. Largest room capacity

```sql
SELECT code, capacity FROM rooms ORDER BY capacity DESC LIMIT 3;
```

- [ ] Max capacity = 80 (so CSC999 remains unplaceable by capacity)

## Pass criteria

- [ ] No SQL errors when schema/seed applied (fresh volume)
- [ ] 28 courses present
- [ ] Three conflict scenarios are **structurally** constrained (allowed timeslots and/or capacity)
- [ ] Algorithm team can rely on `course_allowed_timeslot` as a hard filter

## Optional isolated re-test (does not touch main DB data volume permanently)

```bash
docker exec scheduler_db sh -c 'dropdb -U "$POSTGRES_USER" --if-exists scheduler_test && createdb -U "$POSTGRES_USER" scheduler_test'
# Then pipe schema.sql and seed_data.sql into -d scheduler_test (see Data Engineer handoff)
```

## Result

- Date run: __________
- Run by: __________
- Outcome: Pass / Fail
- Notes: __________
