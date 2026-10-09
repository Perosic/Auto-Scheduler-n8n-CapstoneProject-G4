# Course Timetable Auto-Scheduler

**Group 4 Capstone · Masterplan v3 (FINAL)**

Conflict-free university course timetable scheduler. It loads courses, rooms, instructors and constraints from PostgreSQL, runs a DSATUR-based scheduling algorithm with independent verification, and orchestrates the result through **n8n** — producing either an HTML timetable or an AI-assisted conflict report.

> **Status (2026-10-03)**  
> P0 pipeline is implemented and validated locally: database → Python scheduler + verifier → HTTP API → n8n (conflict path + HTML timetable path).

---

## Why this exists

Manual timetable construction is error-prone and slow. This project automates placement under hard constraints (room capacity, equipment, instructor availability, co-enrolment, allowed timeslots) and surfaces the courses that cannot be placed so humans can act on them.

**P0 (never cut):** Database → DSATUR scheduling → verified `placed[]` / `unplaced[]` → n8n → HTML timetable or conflict explanation.

---

## Quick Start

### 1. Clone and start the stack

```bash
git clone https://github.com/Perosic/Auto-Scheduler-n8n-CapstoneProject-G4.git
cd Auto-Scheduler-n8n-CapstoneProject-G4

cp .env.example .env          # optional – defaults work for local demo
docker compose up -d
```

Schema and seed data are applied automatically on first Postgres start.

| Service   | URL / Port              | Credentials                                      |
|-----------|-------------------------|--------------------------------------------------|
| Postgres  | `localhost:5432`        | db: `auto_scheduler` · user: `postgres` · pass: `postgrespassword` |
| pgAdmin   | http://localhost:5050   | `admin@example.com` / `admin`                    |
| n8n       | http://localhost:5678   | —                                                |
| Gotenberg | http://localhost:3000   | — (PDF conversion for P1)                        |

### 2. Start the Python scheduler API

The API must be running for n8n to call it.

**Linux / macOS**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r algorithm/requirements.txt
# If the API uses FastAPI/uvicorn (or similar), install those deps as well
python -m algorithm.api
```

**Windows (PowerShell)**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r algorithm\requirements.txt
python -m algorithm.api
```

Endpoints:
- `GET  /health`
- `POST /schedule`

From inside the n8n Docker container, call:
```
http://host.docker.internal:8000/schedule
```

Keep the API process running while you test n8n workflows.

---

## Architecture (P0)

```
PostgreSQL (schema + seed)
        ↓
Python scheduling pipeline
  ├─ database loader
  ├─ conflict graph
  ├─ DSATUR timeslot colouring (respects allowed timeslots)
  ├─ room / capacity / equipment assignment
  └─ independent verifier
        ↓
{ status, success, placed[], unplaced[], violations_count, verification_errors[] }
        ↓
n8n workflow
  ├─ Contract Validation
  ├─ IF unplaced.length > 0
  │     TRUE  → Conflict Handler → Gemini AI → Conflict Success
  │     FALSE → n8n-native HTML Timetable
```

### Scope ladder (locked)

| Tier | Scope | If time is short |
|------|--------|------------------|
| **P0** | DB → DSATUR → verified output → n8n HTML / conflict path | **Never cut** |
| **P1** | Streamlit UI, PDF+email (Gotenberg), plain Slack, standalone verifier | Narrate if not live |
| **P2** | Interactive Slack approval buttons | Cut first |

---

## Features

- **Constraint-aware scheduling** – room capacity, equipment/lab requirements, instructor hours, co-enrolment cliques, and per-course allowed timeslots.
- **Independent verifier** – placed schedules are checked for residual violations (`violations_count` and `verification_errors`).
- **Contract-driven integration** – algorithm output shape is a locked interface used by n8n.
- **Dual n8n paths** – success path renders an HTML timetable; conflict path produces an AI explanation of unplaced courses.
- **Deliberate failure fixtures** – seed data guarantees conflict scenarios so the conflict branch can be demonstrated.

---

## Data Contract (Algorithm → n8n)

See `/contracts` for the authoritative interface. Minimal shape:

```json
{
  "placed": [
    {
      "course_id": 1,
      "section_id": 1,
      "room_id": 1,
      "timeslot": "Mon-09:00",
      "instructor_id": 1
    }
  ],
  "unplaced": [
    {
      "course_id": 23,
      "reason_code": "ROOM_CAPACITY",
      "detail": "Expected enrolment 150 exceeds largest available room capacity 80"
    }
  ],
  "violations_count": 0
}
```

`reason_code` values:  
`ROOM_CAPACITY` | `ROOM_EQUIPMENT` | `CO_ENROLMENT` | `INSTRUCTOR_CLASH` | `OTHER`

Do not change field names, nesting, or enum values without team approval.

---

## Deliberate Failure Fixtures (Do Not Remove)

Seed data contains **28 course-sections**, including six fixture courses that form three structurally unplaceable scenarios:

1. **CSC999** – enrolment 150 > largest room (80) → `ROOM_CAPACITY`
2. **CSC351 + CSC352** – lab contention + same instructor hour limit → `ROOM_EQUIPMENT` / clash
3. **MTH401 / MTH402 / MTH403** – co-enrolment clique with insufficient free slots → `CO_ENROLMENT`

These are intentional test fixtures so the conflict path fires during demos. Removing or “fixing” them breaks validation design.

---

## Repository Layout

```
├── algorithm/                 # DSATUR scheduler, graph, room assigner, verifier, API
├── contracts/                 # Locked JSON interface + example
├── database/
│   ├── schema.sql
│   └── seed_data.sql          # 28 courses incl. deliberate failures
├── docs/
│   └── REPO_STATUS.md
├── frontend/                  # Streamlit (P1)
├── n8n/ / workflows/          # Validated n8n workflow export
├── docker-compose.yml         # Postgres + pgAdmin + n8n + Gotenberg
├── .env.example
├── CONTRIBUTING.md
└── README.md
```

---

## Validation Status

| Path                              | Status |
|-----------------------------------|--------|
| Python API health                 | PASS   |
| Python scheduling API             | PASS   |
| Contract validation               | PASS   |
| Conflict IF branch                | PASS   |
| Conflict Handler + Gemini         | PASS   |
| Successful / no-conflict HTML path| PASS   |

Latest observed behaviour: scheduler can return unplaced courses while `violations_count = 0` and `verification_errors = []` (i.e. everything that *was* placed is conflict-free). Exact counts depend on a clean run from a fresh database.

More detail: [`docs/REPO_STATUS.md`](docs/REPO_STATUS.md)

---

## Contributor Roles

| Role | Owns |
|------|------|
| **A** | Database, seed data, Docker, Gotenberg, setup docs |
| **B** | Scheduling algorithm (graph + DSATUR), verifier |
| **C** | n8n orchestration, contract validation, HTML timetable |
| **D** | AI conflict explanation + Slack messaging |
| **E** | Streamlit CSV upload + calendar view |

### Collaboration rules (summary)

- Preserve data contracts and the P0 architecture unless the team explicitly approves a change.
- Never remove the deliberate failure fixtures.
- Work on feature/fix branches; never push directly to `main`.
- Full rules and AI/LLM guardrails: [`CONTRIBUTING.md`](CONTRIBUTING.md)

---

## License

MIT License – see [LICENSE](LICENSE).

Copyright (c) 2026 Group 4, Cohort 8 of TC  
(Granted by Perosic – Team Assistant Lead, on behalf of the group)

---

## Next Steps

1. Final team review and merge of the validated API + n8n work.
2. One clean end-to-end run from a fresh Docker/database state; record exact output for the demo.
3. Keep the P0 pipeline stable for presentation.
4. Add P1 features (Streamlit, PDF/email, Slack) only if required by final scope.
