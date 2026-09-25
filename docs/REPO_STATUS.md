# Repository Sync & Integration Status

_Last updated: 2026-09-25_

## Current state

The repository is a **Day-1 scaffold** with validated deliberate-failure fixtures. P0 implementation is still in progress.

### Present and validated

- PostgreSQL schema with hard-constraint flags
- Seed data containing **structurally unplaceable** conflict fixtures
- Docker Compose (Postgres, pgAdmin, n8n, Gotenberg)
- Locked algorithm → n8n JSON contract (`contracts/`)
- Streamlit P1 placeholder
- n8n workflow placeholder
- Collaboration rules (`CONTRIBUTING.md`)

### Not yet implemented

- Scheduling algorithm / DSATUR
- Standalone verifier
- Real n8n nodes and orchestration
- P0 HTML timetable generation
- Streamlit CSV / calendar
- AI conflict explanation
- Slack integration
- PDF / email integration

## Deliberate failure fixtures (now validated)

| Scenario | Courses | Why it is unplaceable | Expected reason_code |
|----------|---------|-----------------------|----------------------|
| 1. Capacity | CSC999 | enrolment 150 > largest room 80 | `ROOM_CAPACITY` |
| 2. Lab + hours | CSC351, CSC352 | same instructor limited to 1 h/week + only one computer lab | `INSTRUCTOR_CLASH` (or `ROOM_EQUIPMENT`) |
| 3. Clique + hours | MTH401, MTH402, MTH403 | full co-enrolment clique + same instructor limited to 2 h/week | `CO_ENROLMENT` / `INSTRUCTOR_CLASH` |

A correct scheduler **must** leave CSC999 and at least one course from each of scenarios 2 and 3 unplaced. These fixtures exist so the conflict / AI / Slack path is exercised in the demo.

## Integration contract

P0 pipeline remains:

```
PostgreSQL → scheduling algorithm → locked JSON contract → n8n → HTML timetable
```

Downstream contributors should use `contracts/algo_output.example.json` as the temporary upstream fixture until the real algorithm exists.

## Recommended implementation order

1. ~~Validate/finalize the database fixtures~~ **DONE**
2. Build the algorithm input adapter (Person B)
3. Implement DSATUR / greedy scheduling (Person B)
4. Implement the independent verifier (Person B)
5. Validate algorithm output against the locked contract (B + C)
6. Build n8n DB → algorithm → validation → HTML path (Person C)
7. Add P1 features only after P0 works end-to-end
