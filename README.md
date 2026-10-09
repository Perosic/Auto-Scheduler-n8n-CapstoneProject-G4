# Course Timetable Auto-Scheduler

**Group 4 Capstone · Masterplan v3 (FINAL)**

Conflict-free university course timetable scheduler. It loads courses, rooms, instructors and constraints from PostgreSQL, runs a **DSATUR-based** scheduling algorithm with independent verification, and orchestrates results through **n8n** — producing either an HTML timetable, an AI-assisted conflict report, or (optionally) an emailed timetable via Gmail.

> **Status (2026-10-09)**  
> **P0** (core pipeline) is implemented and validated.  
> **P1** Streamlit UI + Gmail timetable email are implemented and integrated.  
> Full step-by-step setup: **[User Guide → START_SCHEDULER.md](user%20guide/START_SCHEDULER.md)**

---

## Why this exists

Manual timetable construction is error-prone and slow. This project automates placement under hard constraints (room capacity, equipment, instructor availability, co-enrolment, allowed timeslots) and surfaces courses that cannot be placed so humans can act on them.

**P0 (never cut):** Database → DSATUR scheduling → verified `placed[]` / `unplaced[]` → n8n → HTML timetable or conflict explanation.

---

## Features

| Feature | Tier | Status |
|---------|------|--------|
| Constraint-aware DSATUR scheduling + independent verifier | P0 | Done |
| PostgreSQL schema + deliberate conflict fixtures | P0 | Done |
| n8n orchestration (contract validation, dual success/conflict paths) | P0 | Done |
| Gemini AI conflict explanation | P0 | Done |
| Streamlit UI (CSV upload, course selection, timetable view) | P1 | Done |
| Email timetable via Gmail (n8n workflow) | P1 | Done |
| PDF via Gotenberg / Slack messaging | P1 | Available in stack / narrate if needed |
| Interactive Slack approval buttons | P2 | Out of scope if time-constrained |

---

## Quick Start

> For the complete, tested walkthrough (including Gmail setup, n8n import, and troubleshooting), use the **[User Guide](user%20guide/START_SCHEDULER.md)**.  
> The steps below are a short overview.

### 1. Clone & start infrastructure

```bash
git clone https://github.com/Perosic/Auto-Scheduler-n8n-CapstoneProject-G4.git
cd Auto-Scheduler-n8n-CapstoneProject-G4

cp .env.example .env          # defaults work for local demo
docker compose up -d
```

| Service   | URL / Port            | Credentials |
|-----------|-----------------------|-------------|
| Postgres  | `localhost:5432`      | db: `auto_scheduler` · user: `postgres` · pass: `postgrespassword` |
| pgAdmin   | http://localhost:5050 | `admin@example.com` / `admin` |
| n8n       | http://localhost:5678 | Create owner account on first visit |
| Gotenberg | http://localhost:3000 | — (PDF conversion) |
| Streamlit | http://localhost:8501 | After you start the frontend |
| Scheduler API | http://localhost:8000 | After you start the Python API |

Schema and seed data (28 courses, including deliberate failure fixtures) load automatically on first Postgres start.

### 2. Python environment + scheduler API

```powershell
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r algorithm/requirements.txt
pip install -r frontend/requirements.txt
pip install requests
python -m algorithm.api
```

```bash
# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
pip install -r algorithm/requirements.txt
pip install -r frontend/requirements.txt
pip install requests
python -m algorithm.api
```

API endpoints: `GET /health` · `POST /schedule`  
From n8n (Docker): `http://host.docker.internal:8000/schedule`

### 3. Import & activate n8n workflows

1. Open http://localhost:5678 and create the owner account.
2. Import **[`n8n/n8n_streamlit_integration_v2.json`](n8n/n8n_streamlit_integration_v2.json)** (scheduling + conflict routing).
3. (Optional email) Import **[`n8n/Gmail_Timetable_Sender.json`](n8n/Gmail_Timetable_Sender.json)** and connect a Gmail OAuth2 credential.
4. Add your Gemini API key on the Google Gemini Chat Model node (optional but recommended for conflict reports).
5. **Save** and **Publish / Activate** both workflows.

Detailed Gmail setup: [`docs/integrations/GMAIL_N8N_INTEGRATION.md`](docs/integrations/GMAIL_N8N_INTEGRATION.md)

### 4. Start Streamlit

```powershell
.\.venv\Scripts\Activate.ps1
streamlit run frontend/app.py
```

Open http://localhost:8501 → upload a CSV (try [`frontend/test_scheduler_courses.csv`](frontend/test_scheduler_courses.csv)) → Generate Schedule → optionally **Send Timetable** by email under Export.

---

## Architecture

```
Browser (Streamlit)
        │  CSV + course selection
        ▼
n8n Webhook (scheduling)  ── n8n/n8n_streamlit_integration_v2.json
        │
        ▼
Python scheduler API  ── algorithm/api.py  →  PostgreSQL
        │
        ▼
Contract Validation
        │
   ┌────┴────────────────────┐
unplaced > 0              success
   │                         │
Conflict Handler          HTML Timetable
   + Gemini AI                 │
   │                         │
   └──────────┬──────────────┘
              ▼
     JSON result → Streamlit
              │  (user clicks “Send Timetable”)
              ▼
n8n Gmail webhook  ── n8n/Gmail_Timetable_Sender.json
              │
              ▼
           Gmail inbox
```

### Scope ladder (locked)

| Tier | Scope | If time is short |
|------|--------|------------------|
| **P0** | DB → DSATUR → verified output → n8n HTML / conflict path | **Never cut** |
| **P1** | Streamlit UI, PDF+email (Gotenberg), Gmail sender, plain Slack, standalone verifier | Narrate if not live |
| **P2** | Interactive Slack approval buttons | Cut first |

---

## Documentation map

| Document | Purpose |
|----------|---------|
| **[user guide/START_SCHEDULER.md](user%20guide/START_SCHEDULER.md)** | **Primary setup & usage guide** (install, run, email, troubleshooting) |
| [docs/integrations/GMAIL_N8N_INTEGRATION.md](docs/integrations/GMAIL_N8N_INTEGRATION.md) | Gmail n8n workflow details, request/response schema, testing |
| [docs/integrations/STREAMLIT_GMAIL_CONNECTION.md](docs/integrations/STREAMLIT_GMAIL_CONNECTION.md) | How Streamlit calls the Gmail webhook |
| [docs/REPO_STATUS.md](docs/REPO_STATUS.md) | Implementation / validation status |
| [contracts/README.md](contracts/README.md) | Locked algorithm ↔ n8n interface |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Collaboration rules, roles, branch workflow |
| [docs/handoff/](docs/handoff/) | Per-role work summaries |

---

## Data Contract (Algorithm → n8n)

Authoritative reference: [`contracts/`](contracts/). Minimal shape:

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
2. **CSC351 + CSC352** – lab contention + same instructor → `ROOM_EQUIPMENT` / clash
3. **MTH401 / MTH402 / MTH403** – co-enrolment clique with insufficient free slots → `CO_ENROLMENT`

These are intentional test fixtures so the conflict path fires during demos. Removing or “fixing” them breaks validation design.

---

## Repository layout

```
├── algorithm/                 # DSATUR scheduler, graph, room assigner, verifier, API
├── contracts/                 # Locked JSON interface + example
├── database/
│   ├── schema.sql
│   └── seed_data.sql          # 28 courses incl. deliberate failures
├── docs/
│   ├── REPO_STATUS.md
│   ├── integrations/          # Gmail + Streamlit connection docs
│   └── handoff/               # Per-person work summaries
├── frontend/                  # Streamlit UI + email helper
│   ├── app.py
│   ├── email_timetable.py
│   └── test_*.csv
├── n8n/                       # Workflow exports (import these)
│   ├── n8n_streamlit_integration_v2.json
│   ├── Gmail_Timetable_Sender.json
│   └── samples/
├── user guide/
│   └── START_SCHEDULER.md     # Full install & run guide
├── workflows/                 # Additional / historical n8n exports
├── docker-compose.yml         # Postgres + pgAdmin + n8n + Gotenberg
├── .env.example
├── CONTRIBUTING.md
└── README.md
```

---

## Validation status

| Path | Status |
|------|--------|
| Python API health | PASS |
| Python scheduling API | PASS |
| Contract validation | PASS |
| Conflict IF branch + Gemini | PASS |
| Successful / no-conflict HTML path | PASS |
| Streamlit → n8n → scheduler end-to-end | PASS |
| Gmail Timetable Sender (standalone + from Streamlit) | PASS |

More detail: [`docs/REPO_STATUS.md`](docs/REPO_STATUS.md)

---

## Contributor roles

| Role | Owns |
|------|------|
| **A** | Database, seed data, Docker, Gotenberg, setup docs |
| **B** | Scheduling algorithm (graph + DSATUR), verifier |
| **C** | n8n orchestration, contract validation, HTML timetable |
| **D** | AI conflict explanation + Slack messaging |
| **E** | Streamlit CSV upload + calendar / email UI |

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
