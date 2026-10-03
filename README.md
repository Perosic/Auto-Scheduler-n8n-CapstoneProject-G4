# Course Timetable Auto-Scheduler
**Group 4 Capstone · Masterplan v3 (FINAL) · Guide v1.0**

University Course Timetable Conflict-Free Auto-Scheduler built around **n8n** as the orchestration core.

> **Status (2026-10-03)**: P0 scheduling + verification + Python API + n8n orchestration have been implemented and validated locally. Both conflict and successful/no-conflict workflow paths have been tested.

---

## Quick Start (Localhost – Default Deployment)

```bash
git clone https://github.com/Perosic/Auto-Scheduler-n8n-CapstoneProject-G4.git
cd Auto-Scheduler-n8n-CapstoneProject-G4

# Optional: copy env
cp .env.example .env

# Start the full stack
docker compose up -d

# Services
# Postgres      → localhost:5432  (db: auto_scheduler / user: postgres / pass: postgrespassword)
# pgAdmin       → http://localhost:5050  (admin@scheduler.local / admin)
# n8n           → http://localhost:5678
# Gotenberg     → http://localhost:3000
```

Schema and seed data are automatically applied on first Postgres start.

### Python scheduler API

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r algorithm\requirements.txt
python -m algorithm.api
```

The API exposes `GET /health` and `POST /schedule`.

For the Dockerized n8n container, use:

```
http://host.docker.internal:8000/schedule
```

Keep the Python API terminal running while testing n8n.

---

## Architecture (P0 Core – Never Cut)

```
Database (Postgres)
    ↓
Python scheduling pipeline
    ├─ database loader
    ├─ conflict graph
    ├─ DSATUR timeslot scheduling
    ├─ room assignment / resource checks
    └─ independent verifier
    ↓
{ status, success, placed[], unplaced[], violations_count, verification_errors[] }
    ↓
n8n workflow
    ├─ Contract Validation
    ├─ IF unplaced.length > 0
    │    ├─ TRUE  → Conflict Handler → Gemini AI Agent → Conflict Success
    │    └─ FALSE → n8n-native HTML Timetable
```

### Scope-Cut Ladder (locked)
| Tier | Feature | Action if time short |
|------|---------|----------------------|
| **P0** | DB → DSATUR → placed/unplaced → n8n HTML timetable | **Never cut** |
| **P1** | Streamlit UI, PDF+email (Gotenberg), plain Slack message, standalone verifier | Narrate if not live |
| **P2** | Interactive Slack approval buttons | Cut first |

---

## Data Contracts (Shared Interface)

See `/contracts` folder. The exact JSON shape is an **interface contract**.

**Algorithm → n8n**
```json
{
  "placed": [{ "course_id", "section_id", "room_id", "timeslot", "instructor_id" }],
  "unplaced": [{ "course_id", "reason_code", "detail" }],
  "violations_count": n
}
```

`reason_code` enum: `ROOM_CAPACITY | ROOM_EQUIPMENT | CO_ENROLMENT | INSTRUCTOR_CLASH | OTHER`

---

## Deliberate Failure Cases (Do Not Remove)

Seed data intentionally contains **six fixture courses across three failure scenarios** so the conflict path is exercised:

1. **CSC999** – enrolment 150 > largest room (80) → `ROOM_CAPACITY`
2. **CSC351 + CSC352** – two lab courses fighting for the single computer lab + same instructor → `ROOM_EQUIPMENT` / clash
3. **MTH401/402/403** – co-enrolment clique with insufficient free slots → `CO_ENROLMENT`

These are **test fixtures**, not bugs.

---

## Implementation Progress / Validation

### Person B — Algorithm + verification

Completed and validated:
- PostgreSQL data loader
- Conflict graph / adjacency construction
- DSATUR scheduling with allowed-timeslot constraints
- Room assignment with capacity, equipment/lab and occupancy checks
- Independent verifier
- End-to-end Python runner

### Person C — Python API + n8n orchestration

Completed and validated:
- `GET /health`
- `POST /schedule`
- API contract fields required by n8n
- n8n HTTP Request through `host.docker.internal`
- Contract Validation
- Conflict IF routing
- Conflict Handler
- Gemini AI Agent conflict reporting
- Conflict Success
- Successful/no-conflict HTML timetable branch

### Latest local scheduler validation

The latest API execution returned **7 unplaced courses**, with:
- `violations_count = 0`
- `verification_errors = []`

The placed records contain course, title, day/time, timeslot and room information. Unplaced records include room-capacity, room-occupancy and no-legal-timeslot details.

A zero `violations_count` means the placed schedule passed independent verification; it does not mean every course was placed.

### Branch coverage

| Path | Status |
|---|---|
| Python API health | **PASS** |
| Python scheduling API | **PASS** |
| Contract validation | **PASS** |
| Conflict IF branch | **PASS** |
| Conflict Handler | **PASS** |
| Gemini conflict explanation | **PASS** |
| Conflict Success | **PASS** |
| Successful/no-conflict IF branch | **PASS** |
| HTML timetable generator | **PASS** |

---

## Repository Layout

```
├── database/
│   ├── schema.sql          # Full normalized schema + hard-constraint flags
│   └── seed_data.sql       # 28 courses including 6 deliberate failure fixtures
├── contracts/
│   ├── algo_output.example.json
│   ├── CONTRIBUTING.md          # Collaboration + AI/LLM workflow rules
└── README.md           # Locked interface documentation
├── workflows/
│   └── course_scheduler_workflow.json  # validated n8n workflow export
├── docs/
│   └── REPO_STATUS.md        # Current implementation/validation status
├── frontend/
│   └── app.py              # Streamlit (P1) entry point
├── docker-compose.yml      # Postgres + pgAdmin + n8n + Gotenberg
├── .env.example
└── README.md
```

---

## Contributor Roles (from Masterplan)

| Person | Primary Focus |
|--------|---------------|
| **A**  | Database, seed data, Docker, Gotenberg, docs |
| **B**  | Algorithm (adjacency + DSATUR), verifier |
| **C**  | n8n orchestrator, HTML timetable, contract validation |
| **D**  | AI prompt + Slack conflict messaging |
| **E**  | Streamlit CSV upload + calendar view |

---

## Collaboration Rules (Summary)

- Preserve the data contracts unless the team explicitly approves a change.
- Never silently redesign architecture, replace n8n/Postgres, or remove P0 requirements.
- Never remove the three deliberate failure cases.
- Use the **Universal LLM Guardrails** prompt from the Collaboration Guide before asking any AI to write code.
- GREEN changes (own component, no interface break) can proceed; YELLOW/RED require team review.

Full repository workflow rules live in [`CONTRIBUTING.md`](CONTRIBUTING.md). Current implementation gaps and validation findings live in [`docs/REPO_STATUS.md`](docs/REPO_STATUS.md). The Masterplan v3 (FINAL) and Contributor & AI Collaboration Guide remain the project-level specification.

---

## Current Tracker Snapshot

| ID     | Owner   | Component | Task                          | Status  |
|--------|---------|-----------|-------------------------------|---------|
| DB-001 | Person A| Database  | Schema                        | DONE    |
| DB-002 | Person A| Database  | Seed data + 3 conflicts       | DONE    |
| DB-003 | Person A| Infra     | Docker Compose (full stack)   | DONE    |
| ALG-001| Person B| Algorithm | Adjacency + DSATUR v1         | DONE |
| ALG-002| Person B| Algorithm | Independent verifier         | DONE |
| ALG-003| A + B    | Integration | Room assignment + verification | DONE |
| CON-001| B + C   | Contracts | Validate algorithm/API output | DONE |
| N8N-001| Person C| n8n       | Python API → validation → IF  | DONE |
| N8N-002| Person C| n8n       | Conflict Handler → Gemini → Success | DONE |
| N8N-003| Person C| n8n       | Successful/no-conflict → HTML | DONE |
| DOC-001| Team    | Documentation | Sync README/status          | DONE    |
| N8N-004| Person C| n8n       | Export validated workflow JSON | DONE    |
| …      | …       | …         | (see Guide for full list)     | …       |

---

## Deployment Rule

**Default = localhost on the single shared machine.**  
Use ngrok **only** if Slack interactive buttons need to call back into n8n, and re-register the redirect URI in Google Cloud first.

---

## Next Steps

1. Finalize/merge the validated Person C API + n8n branch with the team.
2. Re-run the clean end-to-end demo from a fresh Docker/database state and record the exact result.
3. Keep the validated P0 pipeline stable while completing presentation/demo work.
4. Add P1 integrations only if required by the final presentation scope.
