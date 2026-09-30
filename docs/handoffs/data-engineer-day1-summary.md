# Data Engineer Day-1 Work Summary (Handoff)

**Role:** Data Engineer (Person A)  
**Source:** Team work summary (what was done, why, how tested)  
**Branch referenced:** `feature/data-seeding`  
**Status:** Database layer ready for algorithm handoff

> This is a **work / handoff summary**, not a test runbook.  
> Executable verification steps live under `tests/manual/`.

## Scope completed

| Area | Status | Notes |
|------|--------|--------|
| Git / collaboration | Done | Feature branch, push, PR for review |
| Database schema | Done | Executed, tested; added `course_allowed_timeslot` |
| Seed data | Done | Course count corrected; conflict scenarios made restrictive |
| PostgreSQL in Docker | Done | Schema + seed applied successfully |
| pgAdmin | Done | Invalid `*.local` email fixed → `admin@example.com` |

## Why schema was extended

Some scenarios labelled “unplaceable” remained schedulable because many timeslots were still open. A constraint table was added:

```sql
CREATE TABLE course_allowed_timeslot (
  course_id   INTEGER NOT NULL REFERENCES courses(course_id) ON DELETE CASCADE,
  timeslot_id INTEGER NOT NULL REFERENCES timeslots(timeslot_id) ON DELETE CASCADE,
  PRIMARY KEY (course_id, timeslot_id)
);
```

**Meaning:** if a course has rows here, it may **only** use those timeslots. No rows = unrestricted by this rule.

## Seed corrections (summary)

| Change | Reason |
|--------|--------|
| Total courses documented as 28 | 22 normal + 6 fixture courses across 3 conflict scenarios |
| CSC999 excluded from generic section insert | Avoid duplicate section |
| CSC351 / CSC352 restricted to Mon-09:00 | Shared instructor + single computer lab → genuine contention |
| MTH401/402/403 restricted to Mon-09:00 and Mon-10:00 | Pairwise co-enrolment needs distinct slots; 3 courses cannot fit in 2 slots |

## How it was tested (high level)

1. Docker Compose up after Docker Desktop started; images pulled as needed.
2. Schema applied inside container; no SQL errors.
3. Isolated DB `scheduler_test` used to validate schema + seed before relying on main volume.
4. Verification queries: 28 courses, CSC999 single section, allowed-timeslot rows present.
5. pgAdmin logs diagnosed; email env fixed; container recreated.
6. n8n port 5678 conflict noted (existing local n8n) — left for workflow role.

## Handoff to algorithm team

- Use rooms, instructors, sections, co-enrolment, equipment **and** `course_allowed_timeslot`.
- When generating candidate timeslots for a course, **intersect** with allowed timeslots if any rows exist for that `course_id`.
- Deliberate fixtures must produce unplaced entries so the conflict / AI path can be demonstrated.

## Related verification checklists

- `tests/manual/01_docker_stack.md`
- `tests/manual/02_postgres_schema_seed.md`
- `tests/manual/03_pgadmin.md`
- `tests/manual/04_gotenberg.md`
