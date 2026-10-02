# n8n Implementation Work Summary

## Purpose

This document records the work completed on the n8n orchestration side of the Auto-Scheduler capstone and the integration work required to connect it to the Python scheduling engine.

## What was implemented

### 1. n8n orchestration workflow

Created and exported the n8n workflow:

`n8n/Auto_scheduler_n8n_Orchestrator.json`

The workflow contains:

- Manual Trigger
- Python Scheduler HTTP Request
- Contract Validation
- IF conflict router
- Conflict Handler
- AI Agent
- Google Gemini Chat Model
- Conflict Success
- Timetable HTML generator

### 2. Python-to-n8n integration

Connected n8n to the Python scheduler through:

```text
POST http://host.docker.internal:8000/schedule
```

The Python API provides the scheduler result to n8n as JSON.

The integration was designed so that the Python scheduler remains the authoritative source for scheduling decisions.

### 3. Contract validation

Added a validation step before routing the scheduler result.

The validation checks:

```text
placed      → array
unplaced    → array
violations_count → number
```

Validation errors are returned as `contract_errors` instead of allowing malformed scheduler output to silently continue.

### 4. Conflict routing

Added an IF node based on:

```text
$json.unplaced.length > 0
```

This creates two execution paths:

```text
unplaced > 0
    → conflict analysis

unplaced = 0
    → timetable HTML
```

### 5. Conflict Handler normalization

Implemented normalization of scheduler conflict details into consistent reason codes.

The current normalized codes are:

- `NO_LEGAL_TIMESLOT`
- `ROOM_OCCUPIED`
- `ROOM_CAPACITY`

This creates a stable interface for downstream AI analysis.

Example:

```text
No legal timeslot available
    → NO_LEGAL_TIMESLOT

Suitable rooms exist but are already occupied in this timeslot
    → ROOM_OCCUPIED

Requires capacity 150; largest available room capacity is 80
    → ROOM_CAPACITY
```

### 6. AI-assisted conflict analysis

Connected an n8n AI Agent to a Google Gemini Chat Model.

The AI receives the normalized conflict list and produces a human-readable conflict report.

The design explicitly keeps the AI outside the authoritative scheduling loop.

The AI does not:

- assign courses;
- select rooms;
- select timeslots;
- change the schedule;
- claim that a conflict has been resolved.

Instead, it explains the reported conflict and identifies information that should be reviewed.

### 7. Conflict completion response

Added the Conflict Success Code node to return a stable response containing:

- conflict status;
- unresolved state;
- number of conflicts analyzed;
- AI-generated report.

### 8. HTML timetable generation

Added a Code node for the successful scheduling path.

The generator creates an HTML timetable from the `placed` array and includes:

- course;
- title;
- lecturer;
- room;
- day;
- time.

It also displays scheduled, unplaced, and verification-error counts.

### 9. Room-aware scheduler output

The n8n integration consumes the scheduler output after room assignment and verification.

The placed records include room information such as:

- `room_id`
- `room`
- `room_capacity`

This allows the generated timetable to display actual room assignments rather than only course/time information.

## Validation performed during implementation

The integrated scheduler was exercised against the project data.

The tested result contained:

- 21 placed courses;
- 7 unplaced courses;
- 0 verification errors in the independent verification result.

The seven unresolved courses were:

| Course | Normalized conflict |
|---|---|
| CSC352 | `NO_LEGAL_TIMESLOT` |
| MTH401 | `NO_LEGAL_TIMESLOT` |
| MTH402 | `NO_LEGAL_TIMESLOT` |
| MTH403 | `NO_LEGAL_TIMESLOT` |
| PHY101 | `ROOM_OCCUPIED` |
| ENG101 | `ROOM_OCCUPIED` |
| CSC999 | `ROOM_CAPACITY` |

The AI conflict-analysis branch was also exercised using these seven conflicts.

## Final responsibility split

```text
PostgreSQL
    ↓
Python scheduler
    ├── conflict graph
    ├── DSATUR scheduling
    ├── room assignment
    └── independent verification
    ↓
n8n
    ├── contract validation
    ├── conflict routing
    ├── reason-code normalization
    ├── AI-assisted conflict analysis
    └── HTML timetable generation
```

## Files relevant to this work

- `n8n/Auto_scheduler_n8n_Orchestrator.json`
- `algorithm/api.py`
- `algorithm/run.py`
- `algorithm/room_assigner.py`
- `algorithm/verifier.py`

## Reproduction

A collaborator can reproduce the n8n portion by:

1. Starting the project dependencies.
2. Starting the Python API.
3. Opening n8n.
4. Importing `n8n/Auto_scheduler_n8n_Orchestrator.json`.
5. Configuring their own Google Gemini credential.
6. Executing the workflow.

The workflow JSON is the portable representation of the n8n canvas and connections.

## Known boundary

The current conflict branch analyzes unresolved conflicts but does not automatically reschedule them.

The scheduler therefore remains authoritative, while n8n and the AI layer provide orchestration, presentation, validation, and explanation.
