# User Guide — Run the Auto-Scheduler Stack

This guide takes you from a fresh clone of the repository to a working timetable in the browser. It covers every moving part:

1. **Docker** — PostgreSQL (scheduling data), n8n (workflow orchestration), pgAdmin, Gotenberg
2. **Python scheduler API** — the scheduling engine (`algorithm/api.py`)
3. **Streamlit frontend** — the web page where you upload a CSV (`frontend/app.py`)
4. **n8n workflow** — connects the frontend to the scheduler and handles conflicts

All commands are written for **Windows PowerShell**. A short note for macOS/Linux is at the end of the setup section.

---

## Table of contents

1. [How the system fits together](#1-how-the-system-fits-together)
2. [Prerequisites](#2-prerequisites)
3. [Get the code](#3-get-the-code)
4. [Create the environment file](#4-create-the-environment-file)
5. [Create the Python virtual environment and install packages](#5-create-the-python-virtual-environment-and-install-packages)
6. [Start Docker and the database](#6-start-docker-and-the-database)
7. [Set up n8n (first time only)](#7-set-up-n8n-first-time-only)
8. [Start the Python scheduler API](#8-start-the-python-scheduler-api)
9. [Start the Streamlit frontend](#9-start-the-streamlit-frontend)
10. [Use the app](#10-use-the-app)
11. [Understanding the results](#11-understanding-the-results)
12. [Daily quick-start](#12-daily-quick-start)
13. [Stopping and resetting](#13-stopping-and-resetting)
14. [Troubleshooting](#14-troubleshooting)
15. [Reference](#15-reference)

---

## 1. How the system fits together

```text
 Browser (you)
     │  upload CSV, pick courses
     ▼
 Streamlit  ── frontend/app.py ── http://localhost:8501
     │  POST JSON  {course_codes, enrollment_overrides}
     ▼
 n8n Webhook ── http://localhost:5678/webhook/<id>      (runs in Docker)
     │
     ▼
 Python scheduler API ── http://localhost:8000/schedule  (runs on your computer)
     │      reads scheduling data from PostgreSQL (runs in Docker)
     ▼
 Contract Validation
     │
     ▼
    IF  status is not SUCCESS?
   ┌─┴───────────────────────────┐
  YES                            NO
   │                             │
 Conflict handler            Timetable HTML generator
   │                             │
 AI Agent (Gemini)               │
   │                             │
 Conflict Success                │
   └─────────────┬───────────────┘
                 ▼
        JSON result returned to Streamlit
```

**Important design facts**

- The **database holds reference data** (courses, rooms, timeslots, instructors, constraints). Your CSV is **not** written into it.
- Your CSV acts as a **filter**: only the courses you upload and select are scheduled, and the student counts in the CSV override the enrolment stored in the database.
- Every course code in your CSV **must already exist in the database**. Codes that do not exist cause an error (see [Troubleshooting](#14-troubleshooting)).
- Docker runs PostgreSQL and n8n. The Python scheduler API and Streamlit run **directly on your computer**, not in Docker.

### Ports used

| Service | Where it runs | Address |
|---|---|---|
| Streamlit frontend | Your computer | http://localhost:8501 |
| Python scheduler API | Your computer | http://localhost:8000 |
| n8n | Docker | http://localhost:5678 |
| PostgreSQL | Docker | `localhost:5432` |
| pgAdmin (database viewer) | Docker | http://localhost:5050 |
| Gotenberg (PDF service) | Docker | http://localhost:3000 |

Make sure nothing else on your computer is already using these ports.

---

## 2. Prerequisites

Install these first:

| Tool | Why | Check it works |
|---|---|---|
| **Git** | Download the code | `git --version` |
| **Docker Desktop** | Runs PostgreSQL and n8n | `docker --version` and `docker compose version` |
| **Python 3.10 or newer** | Runs the scheduler API and Streamlit | `python --version` |
| **A Gemini API key** (optional but recommended) | Lets the AI Agent write the conflict report | Free keys are available from Google AI Studio |

Without a Gemini key, everything still works, except the **Conflict Resolution Report** that appears when courses cannot be placed.

Open **PowerShell** and run the three check commands above. Each should print a version number. If one says the command is not recognised, install that tool and open a **new** PowerShell window.

---

## 3. Get the code

Choose a folder where you keep projects, then clone the repository and enter it:

```powershell
git clone https://github.com/Perosic/Auto-Scheduler-n8n-CapstoneProject-G4.git
cd Auto-Scheduler-n8n-CapstoneProject-G4
```

From now on, **`<repo>`** means this folder (the one that contains `docker-compose.yml`). Run every command in this guide from inside it unless told otherwise.

If you already have the repository, update it instead:

```powershell
cd Auto-Scheduler-n8n-CapstoneProject-G4
git checkout main
git pull origin main
```

### Where the important files are

| Path | What it is |
|---|---|
| `algorithm/api.py` | **The Python scheduler API.** Started with `python -m algorithm.api` |
| `algorithm/run.py` | The scheduling pipeline (DSATUR, rooms, verifier) |
| `algorithm/frontend_scheduler.py` | Adapter that schedules only the courses you select |
| `algorithm/db_loader.py` | Reads scheduling data from PostgreSQL |
| `frontend/app.py` | **The Streamlit frontend.** Started with `streamlit run frontend/app.py` |
| `database/schema.sql` | Database tables |
| `database/seed_data.sql` | Starting data, including the deliberate failure courses |
| `n8n/n8n_streamlit_integration_v2.json` | **The n8n workflow to import** |
| `docker-compose.yml` | Defines PostgreSQL, pgAdmin, n8n and Gotenberg |
| `.env.example` | Template for settings |
| `frontend/test_scheduler_courses.csv` | A ready-made CSV that works with the seeded database |

---

## 4. Create the environment file

Copy the template:

```powershell
Copy-Item .env.example .env
```

The default values work as they are:

```text
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgrespassword
POSTGRES_DB=auto_scheduler
N8N_PORT=5678
```

You do **not** need to fill in the Slack or OpenAI entries for the core workflow. The Gemini key is entered inside n8n later (section 7).

Never commit your `.env` file. It is listed in `.gitignore`.

---

## 5. Create the Python virtual environment and install packages

A virtual environment keeps this project's packages separate from the rest of your computer. Do this once.

Create it:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell refuses with an execution-policy error, allow scripts for this window only, then activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

Your prompt should now start with `(.venv)`:

```text
(.venv) PS C:\...\Auto-Scheduler-n8n-CapstoneProject-G4>
```

Install the packages:

```powershell
pip install -r algorithm\requirements.txt
pip install -r frontend\requirements.txt
```

This installs `psycopg2-binary` and `python-dotenv` (scheduler), and `streamlit` and `pandas` (frontend).

**You must activate the virtual environment in every new PowerShell window** before running the scheduler or Streamlit:

```powershell
.\.venv\Scripts\Activate.ps1
```

> **macOS / Linux:** use `python3 -m venv .venv`, activate with `source .venv/bin/activate`, and write paths with `/` (for example `pip install -r algorithm/requirements.txt`). On Linux, Docker may also need `extra_hosts: ["host.docker.internal:host-gateway"]` on the `n8n` service so n8n can reach the Python API.

---

## 6. Start Docker and the database

1. Open **Docker Desktop** and wait until it says Docker is running.
2. From `<repo>`, start the services:

```powershell
docker compose up -d
```

The first run downloads images and can take several minutes. Later runs are fast.

3. Check the services:

```powershell
docker compose ps
```

You should see four containers running: `scheduler_db`, `scheduler_pgadmin`, `scheduler_n8n`, `scheduler_gotenberg`. `scheduler_db` should show **healthy**. If it still says "starting", wait a few seconds and run the command again.

### The database loads itself the first time

On its first start, PostgreSQL automatically runs `database/schema.sql` (creates the tables) and `database/seed_data.sql` (loads the data). You do not need to run SQL yourself.

To confirm the data loaded:

```powershell
docker exec -it scheduler_db psql -U postgres -d auto_scheduler -c "SELECT COUNT(*) FROM courses;"
```

With the default seed data the count is **28**.

### Courses available in the database

CSV uploads can only use these course codes:

| Group | Codes |
|---|---|
| Normal courses | CSC101, CSC110, CSC201, CSC210, CSC220, CSC301, CSC302, CSC310, CSC320, CSC401, MTH101, MTH110, MTH201, MTH210, MTH301, PHY101, PHY201, PHY210, ENG101, ENG110, ENG201, ENG210 |
| **Deliberate failure fixtures** (do not remove) | CSC999, CSC351, CSC352, MTH401, MTH402, MTH403 |

The six fixtures exist on purpose so the conflict path can be tested. They are test data, not bugs:

- **CSC999**: enrolment 150, larger than the biggest room (80).
- **CSC351 and CSC352**: two lab courses that compete for the single computer lab with the same instructor.
- **MTH401, MTH402, MTH403**: a group that cannot all fit into the available timeslots.

### Optional: view the database in pgAdmin

Open http://localhost:5050 and sign in with `admin@example.com` / `admin`. Add a server with host `postgres`, port `5432`, database `auto_scheduler`, user `postgres`, password `postgrespassword`.

---

## 7. Set up n8n (first time only)

n8n runs in Docker and is the orchestration layer between Streamlit and the Python API.

### 7.1 Open n8n and create an account

Open http://localhost:5678. The first time, n8n asks you to create an owner account. Use any email and password you will remember. This account is local to your computer.

### 7.2 Import the workflow

1. In n8n, go to **Workflows** and create a new workflow.
2. Open the **three-dot menu** (top right) and choose **Import from file**.
3. Select `n8n/n8n_streamlit_integration_v2.json` from the repository.

The workflow is named **Auto-Scheduler Streamlit Integration v2 (conflict routing fix)**. You should see these nodes: Webhook, Python scheduler, Contract Validation, If, conflict handler, AI Agent, Google Gemini Chat Model, Conflict Success, Timetable HTML generator.

### 7.3 Add your Gemini credential

Credentials are never stored in the exported file, so you add yours:

1. Open the **Google Gemini Chat Model** node.
2. Under **Credential**, choose **Create new credential** and paste your Gemini API key.
3. Save the credential and close the node.

Skip this if you do not have a key. The workflow still runs, but conflict runs will report an error at the AI Agent step.

### 7.4 Check the Webhook node

Open the **Webhook** node and confirm:

- **HTTP Method:** `POST`
- **Path:** `08190fdc-b0cf-4c0f-a7c0-b6c60e7595e2`
- **Respond:** **When Last Node Finishes** (the response is sent after the whole workflow runs)

The **Production URL** shown in the node should be:

```text
http://localhost:5678/webhook/08190fdc-b0cf-4c0f-a7c0-b6c60e7595e2
```

This must match `N8N_WEBHOOK_URL` in `frontend/app.py`. If you ever change the path, update that line in `frontend/app.py` too.

### 7.5 Check the Python scheduler node

Open the **Python scheduler** node and confirm:

- **Method:** `POST`
- **URL:** `http://host.docker.internal:8000/schedule`
- **Body:** JSON, with the expression `{{ $json.body }}`

`host.docker.internal` is how n8n (inside Docker) reaches the Python API running on your computer.

### 7.6 Activate the workflow

**Save** the workflow, then switch it to **Active** (toggle at the top right, or the **Publish** button in newer n8n versions).

Only the **active** workflow answers the production webhook. The URL starting with `/webhook-test/` only works once, after you click "Execute workflow", so Streamlit does not use it.

**Only one workflow can use this webhook path at a time.** If you imported earlier versions, deactivate or delete them first.

---

## 8. Start the Python scheduler API

The scheduler is `algorithm/api.py`. Open a **new PowerShell window**, go to `<repo>`, activate the virtual environment, and start it:

```powershell
cd path\to\Auto-Scheduler-n8n-CapstoneProject-G4
.\.venv\Scripts\Activate.ps1
python -m algorithm.api
```

You should see:

```text
======================================
 Auto-Scheduler Python API
 http://localhost:8000
 POST /schedule
 GET  /health
======================================
```

**Leave this window open.** Closing it stops the scheduler, and n8n will get "connection refused".

### Run it exactly like this

Use `python -m algorithm.api`. Do **not** run `python algorithm\api.py`, because the file imports other parts of the `algorithm` package and fails with `ModuleNotFoundError: No module named 'algorithm'`. Also do not paste Python lines such as `from algorithm.run import run_scheduler` into PowerShell. That is Python code, and PowerShell rejects it.

### Test the API

Open a **second PowerShell window**, go to `<repo>`, and activate the virtual environment again.

**1. Check the API is up.** `/health` only confirms the API process is running; it does not test the database:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

Expected:

```text
status service
------ -------
ok     auto-scheduler
```

**2. Check the scheduler and database together** by scheduling three courses:

```powershell
Invoke-RestMethod -Uri http://localhost:8000/schedule -Method Post -ContentType "application/json" -Body '{"course_codes":["CSC101","CSC201","MTH101"],"enrollment_overrides":{}}' | ConvertTo-Json -Depth 5
```

You should get `"status": "SUCCESS"`, with `requested_courses` listing exactly those three codes and a `placed` list with three entries. If you see a database connection error here, PostgreSQL is not running (see section 6).

---

## 9. Start the Streamlit frontend

Open a **third PowerShell window**:

```powershell
cd path\to\Auto-Scheduler-n8n-CapstoneProject-G4
.\.venv\Scripts\Activate.ps1
streamlit run frontend/app.py
```

Streamlit prints a local address. Open **http://localhost:8501** in your browser if it does not open automatically. Keep this window open while you use the app.

### Test the n8n connection by itself (optional but useful)

Before using the page, check that n8n answers correctly:

```powershell
Invoke-RestMethod -Uri http://localhost:5678/webhook/08190fdc-b0cf-4c0f-a7c0-b6c60e7595e2 -Method Post -ContentType "application/json" -Body '{"course_codes":["CSC101","CSC201","MTH101"],"enrollment_overrides":{}}' | ConvertTo-Json -Depth 5
```

You should get the full schedule back (`placed` with three courses). If you get `"message": "Workflow was started"` instead, the active workflow is an old version (see troubleshooting).

---

## 10. Use the app

### 10.1 Prepare your CSV

Your CSV needs one row per course with these five pieces of information. Column names are flexible:

| Required field | Accepted column names (case-insensitive; `_`, `-` and spaces are treated alike) |
|---|---|
| `course_id` | course_id, course id, id |
| `course_code` | course_code, course code, code, course |
| `course_name` | course_name, course name, title, course title, name |
| `instructor` | instructor, lecturer, lecturer name, teacher, instructor name |
| `students` | students, student count, number of students, enrollment, enrolment |

Example:

```csv
course_id,course_code,course_name,instructor,students
1,CSC101,Intro to Programming,Dr. Ada Okonkwo,55
2,CSC201,Data Structures,Dr. Ada Okonkwo,45
3,MTH101,Calculus I,Dr. Fatima Bello,60
```

Rules the page checks:

- All five fields must be present.
- `students` must be a non-negative number.
- Course codes must not repeat.
- **Every `course_code` must exist in the database** (see the list in section 6).

The instructor and course name in the CSV are checked for presence but the **database values are used for scheduling**. The **student count** from the CSV (or your override on the page) is what gets scheduled.

Ready-made files in the repository:

- `frontend/test_scheduler_courses.csv`: eleven courses that all exist in the database and schedule successfully.
- `frontend/test_courses.csv` and `frontend/test_courses_alt.csv`: **contain course codes that are not in the seeded database** (for example CSC102, STA201, GST101). They are useful for testing the validation error, but they will not schedule.

### 10.2 Step through the page

1. **Upload Course CSV:** choose your file. The page shows a preview.
2. **Column Mapping:** confirms which CSV column matched which field.
3. **Validate Courses:** checks the data and shows summary numbers.
4. **Select Courses:** all courses are selected by default. Remove any you do not want to schedule.
5. **Enrollment:** change student counts if you want to test a different size.
6. **Generate Schedule:** click the button. The request goes through n8n to the Python scheduler. The AI report on a conflict run can take a little longer. The page waits up to 180 seconds.
7. **Results:** the timetable, filters (day, room, lecturer), a CSV download, unplaced courses, verification results and, for conflicts, the AI report.

### 10.3 Test the success path

Upload `frontend/test_scheduler_courses.csv`, keep the courses selected, and click **Generate Schedule**. You should see a green success message and a timetable with every course placed.

### 10.4 Test the conflict path

Create a CSV that includes the failure fixtures, for example:

```csv
course_id,course_code,course_name,instructor,students
1,CSC101,Intro to Programming,Dr. Ada Okonkwo,55
2,CSC201,Data Structures,Dr. Ada Okonkwo,45
3,MTH101,Calculus I,Dr. Fatima Bello,60
4,CSC999,Massive Open Seminar,Unassigned,150
5,CSC351,Advanced Programming Lab A,Unassigned,22
6,CSC352,Advanced Programming Lab B,Unassigned,22
```

Upload it and click **Generate Schedule**. You should see:

- A warning that the schedule has conflicts or unplaced courses.
- The normal courses still in the timetable.
- **Unplaced Courses** listing CSC999 and the lab courses with reasons.
- A **Conflict Resolution Report** written by the AI agent (needs the Gemini credential).

In n8n, open the **Executions** tab to see which path each run took. Successful runs go through *Timetable HTML generator*; conflict runs go through *conflict handler → AI Agent → Conflict Success*.

---

## 11. Understanding the results

The scheduler returns one of these statuses:

| Status | Meaning | n8n path |
|---|---|---|
| `SUCCESS` | Every requested course was placed and verification passed | Timetable HTML generator |
| `PARTIAL` | Some courses were placed, some could not be | Conflict handler → AI Agent |
| `CONFLICT` | No courses could be placed, or verification failed | Conflict handler → AI Agent |

The **If** node sends anything that is **not** `SUCCESS` down the conflict path, so partial results are never reported as complete.

Common reasons a course is unplaced:

| Reason | What it means |
|---|---|
| `ROOM_CAPACITY` | The enrolment is larger than every available room |
| Room occupied | Rooms that are big enough are already taken in the allowed timeslots |
| No legal timeslot | Co-enrolment or instructor constraints leave no free slot |
| `ROOM_EQUIPMENT` | A lab or equipment requirement cannot be met |

`violations_count` counts unplaced courses plus verification errors. A `verification_errors` list that is empty means the placed schedule passed the independent verifier. It does not mean every course was placed.

---

## 12. Daily quick-start

Once everything is set up, this is all you need each time.

**Window 1 — Docker**

```powershell
cd path\to\Auto-Scheduler-n8n-CapstoneProject-G4
docker compose up -d
docker compose ps
```

(Start Docker Desktop first.)

**Window 2 — Python scheduler**

```powershell
cd path\to\Auto-Scheduler-n8n-CapstoneProject-G4
.\.venv\Scripts\Activate.ps1
python -m algorithm.api
```

**Window 3 — Streamlit**

```powershell
cd path\to\Auto-Scheduler-n8n-CapstoneProject-G4
.\.venv\Scripts\Activate.ps1
streamlit run frontend/app.py
```

Then open http://localhost:8501. Check that the workflow is still **Active** at http://localhost:5678.

**Startup order matters:** Docker first, then the Python API, then Streamlit.

---

## 13. Stopping and resetting

**Stop the Python API and Streamlit:** click their windows and press `Ctrl + C`.

**Stop Docker without losing anything:**

```powershell
docker compose stop
```

Start again later with `docker compose up -d`. Your database and n8n workflows are kept.

**Remove the containers but keep your data:**

```powershell
docker compose down
```

**Full reset (deletes the database AND your n8n workflows, accounts and credentials):**

```powershell
docker compose down -v
docker compose up -d
```

Use this only if you want a clean start. After it, you must repeat section 7 (n8n account, workflow import, credential, activation). The database reloads automatically from `schema.sql` and `seed_data.sql`.

Seed data loads **only when the database volume is created**. Editing `seed_data.sql` later has no effect unless you do the full reset above.

---

## 14. Troubleshooting

### Streamlit: "Could not connect to n8n"

n8n is not running or not reachable. Run `docker compose ps` and confirm `scheduler_n8n` is up. Open http://localhost:5678 to confirm it loads.

### Streamlit or webhook: HTTP 404 from n8n

The workflow is not active, or another workflow holds the same path. In n8n, open the Workflows list, deactivate any old versions, and activate the v2 workflow. Make sure the Webhook node's path matches `N8N_WEBHOOK_URL` in `frontend/app.py`.

### The webhook returns `{"message": "Workflow was started"}` and no timetable

The active workflow responds immediately instead of waiting. Open the **Webhook** node and set **Respond** to **When Last Node Finishes**, save, then switch the workflow off and on again. Also check for an old duplicate workflow that is still active.

### Streamlit shows "n8n returned an HTTP error" with a message about courses not in the database

Your CSV contains a course code that does not exist in the database. The error lists the missing codes. Use only the codes in section 6, or add the missing courses to the database.

### Every upload goes to the success path, even with the conflict courses

You are running an old copy of the workflow whose **If** node checks for `status equals CONFLICT`. The v2 workflow checks `status not equals SUCCESS`. Re-import `n8n/n8n_streamlit_integration_v2.json`.

### n8n: `ECONNREFUSED` or "connection refused" on the Python scheduler node

The Python API is not running, or the URL is wrong. Check the Python window is still open and shows the API banner, and test:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

Confirm the node URL is `http://host.docker.internal:8000/schedule`.

### Python API error: "Could not connect to PostgreSQL" or port 5432 refused

The database is not running. Start Docker Desktop, then:

```powershell
docker compose up -d
docker compose ps
```

Wait until `scheduler_db` shows **healthy**, then try again. If you need more detail:

```powershell
docker compose logs postgres
```

### `ModuleNotFoundError: No module named 'algorithm'`

Start the API with `python -m algorithm.api` from the repository root, not `python algorithm\api.py`.

### `ModuleNotFoundError` for `streamlit`, `pandas`, `psycopg2` or `dotenv`

The virtual environment is not active, or packages are not installed. Activate it and reinstall:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r algorithm\requirements.txt
pip install -r frontend\requirements.txt
```

### PowerShell: "running scripts is disabled on this system"

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

Then activate the virtual environment again.

### `The 'from' keyword is not supported in this version of the language`

You pasted Python code into PowerShell. Use the commands in this guide instead.

### Conflict runs work but there is no AI report

The Gemini credential is missing or invalid. In n8n, open the **Executions** tab, open the failed run, and look at the **AI Agent** node. Add or fix the credential on the **Google Gemini Chat Model** node.

### Streamlit says "n8n timed out"

The page waits 180 seconds. Check the n8n Executions tab to see which node is slow. The AI Agent step is usually the slowest.

### "Port is already allocated" when starting Docker

Another program is using port 5432, 5678, 5050 or 3000. Close it, or change the port in `.env` (for `N8N_PORT`) or `docker-compose.yml`.

### The database seems to have old or missing data

Seed data only loads the first time. Do the full reset in section 13, then redo the n8n setup.

### A CSV is rejected by the page

Check the **Column Mapping** table on the page. A field showing "Not found" needs a column renamed to one of the accepted names in section 10.1. The page also rejects negative student counts and duplicate course codes.

---

## 15. Reference

### Scheduler API

| Endpoint | Purpose |
|---|---|
| `GET /health` | Confirms the API process is running |
| `POST /schedule` | Schedules the given courses |

**Request body for `POST /schedule`:**

```json
{
  "course_codes": ["CSC101", "CSC201", "MTH101"],
  "enrollment_overrides": { "CSC101": 50 }
}
```

- `course_codes` must be a JSON array.
- `enrollment_overrides` must be a JSON object (use `{}` for none).

**Main fields in the response:**

| Field | Meaning |
|---|---|
| `status` | `SUCCESS`, `PARTIAL` or `CONFLICT` |
| `success` | `true` only if every requested course was placed |
| `requested_courses` | The course codes that were scheduled |
| `placed` | Placed courses with day, time, room and lecturer |
| `unplaced` | Courses that could not be placed, with reasons |
| `violations_count` | Unplaced courses plus verification errors |
| `verification_errors` | Problems found by the independent verifier |
| `missing_courses` | Requested codes not found in the database |

After n8n processes it, the response may also contain `html` (a ready-made timetable page), `message`, and `resolution_report` (the AI conflict explanation).

### Default credentials (local development only)

| Service | Login |
|---|---|
| PostgreSQL | user `postgres`, password `postgrespassword`, database `auto_scheduler` |
| pgAdmin | `admin@example.com` / `admin` |
| n8n | the owner account you create on first visit |

These are development defaults for a local machine. Change them before exposing anything to a network.

### Dependency summary

| File | Packages |
|---|---|
| `algorithm/requirements.txt` | psycopg2-binary, python-dotenv |
| `frontend/requirements.txt` | streamlit, pandas |

### Startup order at a glance

```text
Docker Desktop
      ↓
docker compose up -d        (PostgreSQL + n8n)
      ↓
n8n workflow imported, credential added, workflow ACTIVE   (first time only)
      ↓
python -m algorithm.api     (Python scheduler on port 8000)
      ↓
streamlit run frontend/app.py   (frontend on port 8501)
      ↓
Upload CSV → Generate Schedule
```
