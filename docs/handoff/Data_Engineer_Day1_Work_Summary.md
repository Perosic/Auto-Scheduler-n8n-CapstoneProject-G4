# Auto-Scheduler Capstone Project

## Data Engineer Work Summary
**What Was Done, Why It Was Done, and How It Was Tested**

**Purpose:** Concise, team-friendly explanation of the database work completed so far, including reasons for each change, commands used, and current handoff status.

---

## 1. Data Engineer Scope

The master plan assigns the Data Engineer role to the database layer: PostgreSQL, Docker, `schema.sql`, `seed_data.sql`, and PostgreSQL/pgAdmin setup. The objective is to provide reliable, realistic and testable scheduling data for the algorithm and workflow teams.

| Area | Status | Work completed |
|------|--------|----------------|
| Git / collaboration | Done | Repo cloned, feature branch created, changes pushed, pull request opened |
| Database schema | Done | Schema executed and tested; extended with `course_allowed_timeslot` for deliberate conflict fixtures |
| Seed data | Done | Course count corrected, section logic fixed, conflict scenarios made genuinely restrictive |
| PostgreSQL | Done | Started in Docker; schema and seed executed successfully |
| pgAdmin | Done | Startup failure diagnosed, invalid default email corrected, container verified running |

---

## 2. Repository and Git Setup

```bash
git clone https://github.com/Perosic/Auto-Scheduler-n8n-CapstoneProject-G4.git
git checkout -b feature/data-seeding
git status
git push -u origin feature/data-seeding
```

After testing:

```bash
git add database/schema.sql database/seed_data.sql docker-compose.yml
git commit -m "Complete database seed data and pgAdmin setup"
git push
```

A pull request was opened from `feature/data-seeding` into `main` for team review and merge.

---

## 3. Docker Setup

```bash
docker ps
docker compose up -d
docker pull postgres:16
docker pull dpage/pgadmin4:latest
docker pull gotenberg/gotenberg:8
docker pull n8nio/n8n:latest
```

Docker Desktop had to be running first. A temporary TLS/network timeout during image download was resolved by pulling images individually.

---

## 4. Running and Verifying schema.sql

```bash
Get-Content .\database\schema.sql -Raw | docker exec -i scheduler_db sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

Output showed repeated `CREATE TABLE`, `CREATE INDEX` and `COMMENT` messages with no SQL error.

---

## 5. Why the Schema Was Changed

Two scenarios labelled as unplaceable were still schedulable because many alternative timeslots remained available. A new table was added:

```sql
CREATE TABLE course_allowed_timeslot (
  course_id INTEGER NOT NULL REFERENCES courses(course_id) ON DELETE CASCADE,
  timeslot_id INTEGER NOT NULL REFERENCES timeslots(timeslot_id) ON DELETE CASCADE,
  PRIMARY KEY (course_id, timeslot_id)
);
```

**Meaning:** if a course appears in this table, it may only be scheduled in the listed timeslots. If a course has no rows, it remains unrestricted by this rule. This gives the algorithm team a clear database-level representation of deliberate timeslot restrictions.

---

## 6. Seed Data Corrections

| Change | Reason |
|--------|--------|
| Corrected total from 25 to 28 courses | 22 normal + 6 courses used across 3 deliberate conflict scenarios |
| Excluded CSC999 from the normal section insert | Prevent a second section from the dedicated failure-case insert |
| CSC351 and CSC352 restricted to Mon-09:00 | Same instructor + computer-lab requirement; one valid slot makes contention genuine |
| MTH401/402/403 restricted to Mon-09:00 and Mon-10:00 | Pairwise co-enrolled; three mutually conflicting courses cannot fit into only two allowed timeslots |

---

## 7. Testing in a Separate Database

```bash
docker exec scheduler_db sh -c 'dropdb -U "$POSTGRES_USER" --if-exists scheduler_test && createdb -U "$POSTGRES_USER" scheduler_test'
```

Schema and seed were applied to `scheduler_test` with `ON_ERROR_STOP=1`. Both completed without SQL errors. Verification confirmed 28 courses, one section for CSC999, and the expected allowed-timeslot rows for the conflict fixtures.

---

## 8. pgAdmin Problem and Fix

```bash
docker logs scheduler_pgadmin --tail 50
```

`admin@scheduler.local` was rejected (`.local` is a reserved/special-use domain). Default email in `docker-compose.yml` was changed to `admin@example.com`.

```bash
docker compose up -d --force-recreate pgadmin
docker ps
```

After recreation, `scheduler_pgadmin` ran on port 5050; `scheduler_db` remained healthy on 5432.

---

## 9. n8n Port Conflict

The project n8n container could not start because an existing local n8n was already using port 5678. This was left unchanged because n8n workflow ownership sits with the workflow/integration role, not the database role. It does not block the successful PostgreSQL setup.

---

## 10. Current Handoff to the Team

The database layer is ready for the next stage. The algorithm team can use course, section, room, instructor, equipment, co-enrolment data, **plus** `course_allowed_timeslot`.

| Item | Current state |
|------|----------------|
| schema.sql | Updated and tested successfully |
| seed_data.sql | Updated, conflict fixtures corrected, tested |
| PostgreSQL | Running and healthy in Docker |
| pgAdmin | Running on port 5050 |
| Git branch | feature/data-seeding (merged / reviewed as applicable) |
| Algorithm handoff note | **`course_allowed_timeslot` must be respected** when generating valid timeslot candidates |

---

*University Course Timetable Auto-Scheduler · Group 4 Capstone · Data Engineer Day 1*
