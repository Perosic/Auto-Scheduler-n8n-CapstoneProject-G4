# Repository Sync & Integration Status

_Last checked: 2026-10-03_

## Current state

The repository now contains the validated **P0 scheduler pipeline**:

PostgreSQL → Python scheduling/verification → HTTP API → n8n orchestration → conflict reporting or HTML timetable output.

### Implemented

- PostgreSQL schema and seed data.
- Docker Compose for PostgreSQL, pgAdmin, n8n and Gotenberg.
- Conflict graph and DSATUR timeslot scheduling.
- Room/resource assignment.
- Independent schedule verifier.
- Python GET /health and POST /schedule API.
- Locked algorithm → n8n output fields.
- n8n Contract Validation.
- Conflict routing and Gemini conflict explanation.
- Successful/no-conflict HTML timetable branch.
- Reproducible n8n workflow export at workflows/course_scheduler_workflow.json.

## Validation record

The local validation covered:

1. Python API health endpoint.
2. Python scheduling endpoint.
3. n8n HTTP Request via host.docker.internal.
4. Contract Validation.
5. Conflict IF routing.
6. Conflict Handler.
7. Gemini AI Agent conflict reporting.
8. Conflict Success output.
9. Successful/no-conflict HTML timetable path using successful test input.

The seeded database is intentionally capable of producing unplaced courses so the conflict path can be demonstrated. The exact counts should be taken from the latest clean run rather than copied from an older run.

## Fixture note

The seed contains 28 course-sections, including deliberate failure fixtures. Do not remove these fixtures; they are part of the validation/demo design.

## Contract note

The API currently returns rich placed-course fields (course/title/day/time/timeslot/room) plus the required placed[], unplaced[], violations_count, and verification_errors[] fields used by n8n. The checked-in contract example should be treated as the interface reference and kept synchronized if the public shape changes.

## Remaining cleanup

- Run one clean end-to-end validation from a fresh database state and record the exact output.
- Finalize/merge the Person C branch after team review.
- Keep P0 stable for the final demo/presentation.
- Add P1 features only if they are required by the final presentation scope.