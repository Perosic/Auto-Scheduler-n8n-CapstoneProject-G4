# Repository Sync & Integration Status

_Last checked: 2026-10-09_

## Current state

The repository contains the validated **P0 scheduler pipeline** plus **P1 Streamlit UI and Gmail email delivery**:

PostgreSQL → Python scheduling/verification → HTTP API → n8n orchestration → conflict reporting or HTML timetable → (optional) Streamlit UI → (optional) Gmail timetable email.

### Implemented

**P0**
- PostgreSQL schema and seed data (28 courses, including deliberate failure fixtures).
- Docker Compose for PostgreSQL, pgAdmin, n8n and Gotenberg.
- Conflict graph and DSATUR timeslot scheduling.
- Room/resource assignment.
- Independent schedule verifier.
- Python `GET /health` and `POST /schedule` API.
- Locked algorithm → n8n output fields.
- n8n Contract Validation.
- Conflict routing and Gemini conflict explanation.
- Successful/no-conflict HTML timetable branch.
- Reproducible n8n workflow exports under `n8n/` and `workflows/`.

**P1**
- Streamlit frontend (`frontend/app.py`) with CSV upload, course selection, timetable view, and export.
- n8n Streamlit integration workflow: `n8n/n8n_streamlit_integration_v2.json`.
- Standalone Gmail Timetable Sender workflow: `n8n/Gmail_Timetable_Sender.json`.
- Streamlit → Gmail connection (`frontend/email_timetable.py`).
- Integration docs under `docs/integrations/`.
- Full user guide: `user guide/START_SCHEDULER.md`.

## Validation record

Local validation has covered:

1. Python API health endpoint.
2. Python scheduling endpoint.
3. n8n HTTP Request via `host.docker.internal`.
4. Contract Validation.
5. Conflict IF routing.
6. Conflict Handler + Gemini AI Agent conflict reporting.
7. Conflict Success output.
8. Successful/no-conflict HTML timetable path.
9. Streamlit → n8n → scheduler end-to-end (conflict-free and conflict CSVs).
10. Gmail Timetable Sender (standalone samples + from Streamlit “Send Timetable”).

The seeded database is intentionally capable of producing unplaced courses so the conflict path can be demonstrated. Exact counts should be taken from the latest clean run rather than copied from an older run.

## Fixture note

The seed contains 28 course-sections, including deliberate failure fixtures. Do not remove these fixtures; they are part of the validation/demo design.

## Contract note

The API returns rich placed-course fields (course/title/day/time/timeslot/room/lecturer) plus the required `placed[]`, `unplaced[]`, `violations_count`, and `verification_errors[]` fields used by n8n. The checked-in contract example should be treated as the interface reference and kept synchronized if the public shape changes.

## Remaining / optional

- One clean end-to-end validation from a fresh database state; record exact output for the demo script.
- Keep the P0 pipeline stable for presentation.
- PDF (Gotenberg) and Slack messaging remain optional P1 polish if time allows.
- P2 interactive Slack approval buttons stay lowest priority.
