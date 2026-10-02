# n8n Workflow Guide

## Overview

This folder contains the exported n8n orchestration workflow used by the Auto-Scheduler capstone.

Workflow file:

`n8n/Auto_scheduler_n8n_Orchestrator.json`

The workflow keeps the Python scheduler authoritative and uses n8n for orchestration, contract validation, conflict routing, AI-assisted conflict analysis, and HTML timetable generation.

## Architecture

```text
Manual Trigger
      |
      v
Python scheduler
      |
      v
Contract Validation
      |
      v
IF: unplaced.length > 0
     / \
   TRUE  FALSE
    |      |
    v      v
Conflict   Timetable HTML
Handler    generator
    |
    v
AI Agent
    |
    v
Conflict Success
```

## 1. Python Scheduler node

The **Python scheduler** node is an HTTP Request node.

It sends:

```text
POST http://host.docker.internal:8000/schedule
```

This URL is used because the n8n instance is expected to run in Docker while the Python API can run on the host machine.

The Python API exposes:

- `GET /health`
- `POST /schedule`

Start the API with:

```bash
python -m algorithm.api
```

## 2. Contract Validation

The **Contract Validation** Code node checks that the scheduler response contains the basic fields required by n8n:

- `placed` must be an array.
- `unplaced` must be an array.
- `violations_count` must be a number.

It adds:

```json
{
  "contract_valid": true,
  "contract_errors": []
}
```

The node does not perform scheduling. It validates the interface between the Python scheduler and n8n.

## 3. IF routing

The **If** node checks:

```text
$json.unplaced.length > 0
```

### TRUE branch

If one or more courses are unplaced:

```text
Conflict Handler
      ↓
AI Agent
      ↓
Conflict Success
```

### FALSE branch

If all courses are placed:

```text
Timetable HTML generator
```

This allows the same workflow to handle both successful schedules and schedules containing unresolved courses.

## 4. Conflict Handler

The **conflict handler** Code node converts the scheduler's `unplaced` records into a consistent downstream conflict structure.

The node reads:

- `course_id`
- `code` or `course`
- `title`
- `reason_code`
- `detail`

It also normalizes the reason code from the detail text when necessary.

### Normalized reason codes

| Normalized code | Triggered by detail | Meaning |
|---|---|---|
| `NO_LEGAL_TIMESLOT` | `No legal timeslot available` | The scheduler could not find a legal timeslot. |
| `ROOM_OCCUPIED` | Suitable rooms exist but are occupied | Suitable rooms are unavailable in the attempted timeslot. |
| `ROOM_CAPACITY` | Detail contains a capacity mismatch | Available rooms cannot satisfy the required capacity. |

For example:

```text
"No legal timeslot available"
        ↓
NO_LEGAL_TIMESLOT
```

```text
"Suitable rooms exist but are already occupied in this timeslot"
        ↓
ROOM_OCCUPIED
```

```text
"Requires capacity 150; largest available room capacity is 80"
        ↓
ROOM_CAPACITY
```

The output is structured as:

```json
{
  "status": "CONFLICT",
  "success": false,
  "violations_count": 7,
  "conflicts": [],
  "message": "7 course(s) could not be scheduled.",
  "ai_ready": true
}
```

## 5. AI Agent

The **AI Agent** receives the normalized `conflicts` array.

Its role is **AI-assisted conflict analysis**, not timetable generation.

The Python scheduling engine remains authoritative.

The AI is instructed to:

1. Identify the affected course.
2. State the reported reason and detail.
3. Explain only what can be concluded from the supplied conflict data.
4. Identify information that should be reviewed.
5. State when more information is required.
6. Avoid claiming that a conflict has been resolved.

The workflow uses a **Google Gemini Chat Model** connected to the AI Agent.

### Credential setup

The exported workflow does not provide a user's Gemini API key.

When importing the workflow into another n8n instance, configure the Google Gemini credential in that instance and select it for the Gemini Chat Model node.

Never commit API keys, passwords, or other secrets to this repository.

## 6. Conflict Success

The **Conflict Success** Code node packages the AI output into a stable final response:

```json
{
  "status": "CONFLICT",
  "success": false,
  "conflicts_analyzed": true,
  "message": "Scheduling completed with unresolved conflicts.",
  "resolution_report": "..."
}
```

The name "Conflict Success" means the conflict-analysis branch completed successfully; it does not mean that the timetable conflicts were solved.

## 7. Timetable HTML generator

The FALSE branch uses the **Timetable HTML generator** Code node.

It reads the `placed` courses and generates a complete HTML timetable containing:

- Course
- Title
- Lecturer
- Room
- Day
- Time

It also displays:

- Scheduled course count
- Unplaced course count
- Verification error count

HTML values are escaped before insertion into the page.

## Importing the workflow

1. Start n8n.
2. Open the n8n editor.
3. Import the workflow JSON from:
   `n8n/Auto_scheduler_n8n_Orchestrator.json`
4. Configure the Google Gemini credential.
5. Start the Python scheduler API.
6. Make sure n8n can reach the API at:
   `http://host.docker.internal:8000/schedule`
7. Execute the workflow from the Manual Trigger.

## Local test setup

Start PostgreSQL if it is not already running:

```bash
docker compose up -d postgres
```

Start the scheduler API:

```bash
python -m algorithm.api
```

Check the API:

```text
http://localhost:8000/health
```

Then open:

```text
http://localhost:5678
```

and execute the imported workflow.

## Important implementation boundary

The project deliberately separates responsibilities:

```text
Python
  = scheduling algorithm + room assignment + verification

n8n
  = orchestration + contract validation + routing + AI analysis + HTML generation

AI
  = conflict explanation only; it does not replace the scheduler
```

This separation prevents the AI node from inventing timetable assignments or silently overriding the authoritative scheduling engine.
