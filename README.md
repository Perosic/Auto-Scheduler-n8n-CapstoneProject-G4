# Course Timetable Auto-Scheduler
**Group 4 Capstone · Masterplan v3 (FINAL) · Guide v1.0**

University Course Timetable Conflict-Free Auto-Scheduler built around **n8n** as the orchestration core.

> **Status**: Day-1 ready scaffold. Collaborators can clone and start immediately.

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

---

## Architecture (P0 Core – Never Cut)

```
Database (Postgres)
    → Scheduling Algorithm (DSATUR / Greedy)
        → { placed[], unplaced[], violations_count }
            → n8n workflow
                → n8n-native HTML timetable  (P0 demo)
                → IF branch → AI / Slack conflict path (P1)
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

Seed data intentionally contains **three unplaceable courses** so the conflict path is exercised:

1. **CSC999** – enrolment 150 > largest room (80) → `ROOM_CAPACITY`
2. **CSC351 + CSC352** – two lab courses fighting for the single computer lab + same instructor → `ROOM_EQUIPMENT` / clash
3. **MTH401/402/403** – co-enrolment clique with insufficient free slots → `CO_ENROLMENT`

These are **test fixtures**, not bugs.

---

## Repository Layout

```
├── database/
│   ├── schema.sql          # Full normalized schema + hard-constraint flags
│   └── seed_data.sql       # 25 courses including 3 deliberate failures
├── contracts/
│   ├── algo_output.example.json
│   └── README.md           # Locked interface documentation
├── workflows/
│   └── course_scheduler_workflow.json  # n8n workflow (to be built)
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

Full rules live in the **Contributor & AI Collaboration Guide v1.0** and **Masterplan v3 (FINAL)**.

---

## Current Tracker Snapshot

| ID     | Owner   | Component | Task                          | Status  |
|--------|---------|-----------|-------------------------------|---------|
| DB-001 | Person A| Database  | Schema                        | DONE    |
| DB-002 | Person A| Database  | Seed data + 3 conflicts       | DONE    |
| DB-003 | Person A| Infra     | Docker Compose (full stack)   | DONE    |
| ALG-001| Person B| Algorithm | Adjacency + DSATUR v1         | PENDING |
| CON-001| B + C   | Contracts | Validate mock JSON            | PENDING |
| N8N-001| Person C| n8n       | DB → Code → IF                | PENDING |
| …      | …       | …         | (see Guide for full list)     | …       |

---

## Deployment Rule

**Default = localhost on the single shared machine.**  
Use ngrok **only** if Slack interactive buttons need to call back into n8n, and re-register the redirect URI in Google Cloud first.

---

## Next Steps for the Team

1. All five roles confirm data contracts + scope-cut ladder + deployment rule.
2. Person B starts ALG-001 (adjacency matrix + DSATUR) against the locked contract.
3. Person C starts the n8n skeleton (DB node → Code node → IF).
4. Keep the Collaboration Guide and this README as the single source of truth for LLMs.
