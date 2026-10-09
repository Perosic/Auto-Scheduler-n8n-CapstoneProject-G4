# Auto-Scheduler

**Conflict-free university course timetables — generated in minutes, not days.**

Auto-Scheduler turns a list of courses, rooms, instructors and hard constraints into a verified timetable. Upload a CSV, select what to schedule, and get either a clean timetable or a clear explanation of why certain courses could not be placed — with the option to email the result.

Built as a Group 4 Capstone (Masterplan v3) around a DSATUR scheduling engine, PostgreSQL, and **n8n** orchestration.

---

## The problem

Building a semester timetable by hand is slow and fragile. One capacity mismatch, one lab clash, or one co-enrolled group with too few free slots and the whole grid has to be reworked. Conflicts are easy to miss until students or lecturers complain.

Auto-Scheduler automates the hard part: **constraint-aware placement** and **independent verification**, then surfaces anything that still cannot fit so a human can decide what to do.

---

## What you get

| Capability | What it means for you |
|---|---|
| **Constraint-aware scheduling** | Respects room capacity, lab/equipment needs, instructor limits, co-enrolment, and allowed timeslots |
| **Independent verification** | Every placed schedule is checked again so residual clashes do not slip through |
| **Clear conflict reporting** | Unplaced courses come with reason codes; Gemini can write a plain-language conflict report |
| **Web UI** | Streamlit app: upload CSV → select courses → generate → filter and export |
| **Email delivery** | Send the finished timetable to one or more addresses via Gmail (optional, user-triggered) |
| **Reproducible orchestration** | n8n workflows handle routing, validation, HTML output, and email — exportable and re-importable |

---

## How it works

```text
You (CSV + course selection)
        │
        ▼
Streamlit UI
        │
        ▼
n8n  ──  validates request, calls the scheduler, routes success vs conflict
        │
        ▼
Python scheduling engine
  • load courses / rooms / instructors from PostgreSQL
  • build conflict graph
  • DSATUR timeslot colouring
  • room & resource assignment
  • independent verifier
        │
        ├── Success  →  HTML timetable + export / email
        └── Conflict →  unplaced list + AI explanation
```

**Design principles**

- The database holds **reference data** (catalogue of courses, rooms, constraints). Your CSV is a **filter and enrolment override**, not a dump into the DB.
- Placement and verification are separate steps. A zero violation count means everything that *was* placed is clean — not that every requested course was placed.
- Email is never automatic. You choose when to send.

---

## Who it’s for

- Academic planners and departmental admins who need a first-pass conflict-free grid quickly  
- Teams that want a transparent, auditable scheduling pipeline (algorithm + contracts + workflows)  
- Capstone / demo environments where both success and failure paths must be showable on demand  

---

## Get started

**Full install, run, Gmail setup, and troubleshooting:**

→ **[User Guide — START_SCHEDULER.md](user-guide/START_SCHEDULER.md)**

That guide walks through Docker, the Python API, n8n workflow import, Streamlit, and optional email end-to-end.

---

## Tech stack (at a glance)

| Layer | Choice |
|---|---|
| Scheduling engine | Python (conflict graph + DSATUR + room assigner + verifier) |
| Data | PostgreSQL (schema + seed with deliberate conflict fixtures) |
| Orchestration | n8n (contract validation, dual paths, Gmail sender) |
| UI | Streamlit |
| AI (optional) | Google Gemini for conflict narratives |
| Infrastructure | Docker Compose (Postgres, pgAdmin, n8n, Gotenberg) |

Locked interfaces live in [`contracts/`](contracts/). Collaboration rules and roles: [`CONTRIBUTING.md`](CONTRIBUTING.md).

---

## Project status

| Area | Status |
|---|---|
| Core pipeline (DB → schedule → verify → n8n) | Validated |
| Streamlit UI | Implemented |
| Gmail timetable email | Implemented |
| PDF (Gotenberg) / Slack | In stack / optional |

Implementation notes: [`docs/REPO_STATUS.md`](docs/REPO_STATUS.md)

---

## License

MIT — see [LICENSE](LICENSE).

Copyright (c) 2026 Group 4, Cohort 8 of TC  
(Granted by Perosic – Team Assistant Lead, on behalf of the group)
