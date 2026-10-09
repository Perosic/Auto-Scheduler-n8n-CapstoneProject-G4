# User Guide — Run the Auto-Scheduler Stack

This guide takes you from a fresh clone of the repository to a working timetable in the browser, including optional email delivery of the timetable. It covers every moving part:

1. **Docker** — PostgreSQL (scheduling data), n8n (workflow orchestration), pgAdmin, Gotenberg
2. **Python scheduler API** — the scheduling engine (`algorithm/api.py`)
3. **Streamlit frontend** — the web page where you upload a CSV (`frontend/app.py`)
4. **n8n scheduling workflow** — connects the frontend to the scheduler and handles conflicts
5. **n8n Gmail workflow** — sends the generated timetable by email (optional but fully integrated)

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
 n8n Webhook (scheduling) ── http://localhost:5678/webhook/08190fdc-...
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
                 │
                 │  (user clicks "Send Timetable")
                 ▼
 Streamlit  ── frontend/email_timetable.py
     │  POST JSON  {recipient, subject, schedule}
     ▼
 n8n Webhook (Gmail) ── http://localhost:5678/webhook/send-schedule
     │
     ▼
 Gmail  →  recipient inbox
```

**Important design facts**

- The **database holds reference data** (courses, rooms, timeslots, instructors, constraints). Your CSV is **not** written into it.
- Your CSV acts as a **filter**: only the courses you upload and select are scheduled, and the student counts in the CSV override the enrolment stored in the database.
- Every course code in your CSV **must already exist in the database**. Codes that do not exist cause an error (see [Troubleshooting](#14-troubleshooting)).
- Docker runs PostgreSQL and n8n. The Python scheduler API and Streamlit run **directly on your computer**, not in Docker.
- **Email is a separate, optional step.** Generating a timetable never sends email automatically. You must click **Send Timetable** under section 9 (Export) on the Streamlit page. A Gmail problem cannot break schedule generation.

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
| **A Gmail account** (optional) | Lets you email the timetable from Streamlit | Any Google account you control |

Without a Gemini key, everything still works, except the **Conflict Resolution Report** that appears when courses cannot be placed.

Without a Gmail credential, everything still works, except the **Send Timetable by Email** form under Export. You can still download the CSV.

> **Tip:** Use a dedicated project / test Gmail account for the n8n Gmail credential. Google’s permission screen allows reading and sending mail, so keeping personal email separate is safer.

---

## 3. Get the code

```powershell
git clone https://github.com/Perosic/Auto-Scheduler-n8n-CapstoneProject-G4.git
cd Auto-Scheduler-n8n-CapstoneProject-G4
```

In the rest of this guide, `<repo>` means the folder you just entered.

Key files you will use:

| Path | Purpose |
|---|---|
| `docker-compose.yml` | Starts PostgreSQL, n8n, pgAdmin, Gotenberg |
| `algorithm/api.py` | Python scheduler HTTP API |
| `frontend/app.py` | Streamlit web UI |
| `frontend/email_timetable.py` | Email form and call to the Gmail webhook |
| `n8n/n8n_streamlit_integration_v2.json` | **The scheduling workflow to import** |
| `n8n/Gmail_Timetable_Sender.json` | **The Gmail email workflow to import** |
| `frontend/test_scheduler_courses.csv` | Ready-made CSV that schedules cleanly |
| `docs/integrations/GMAIL_N8N_INTEGRATION.md` | Full technical detail for the Gmail workflow |
| `docs/integrations/STREAMLIT_GMAIL_CONNECTION.md` | How Streamlit talks to the Gmail webhook |

---

## 4. Create the environment file

Copy the example and leave the defaults for local development:

```powershell
copy .env.example .env
```

Open `.env` if you want to change anything. For a first run the defaults are fine:

```text
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgrespassword
POSTGRES_DB=auto_scheduler
N8N_PORT=5678
```

You do **not** need to fill in the Slack or OpenAI entries for the core workflow. The Gemini key is entered inside n8n later (section 7). Gmail credentials are also created inside n8n (never put Client ID / Secret into `.env` for this project).

Optional environment variable used by Streamlit for the email webhook (defaults are already correct for local use):

```text
N8N_SEND_SCHEDULE_URL=http://localhost:5678/webhook/send-schedule
```

---

## 5. Create the Python virtual environment and install packages

From `<repo>`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r algorithm/requirements.txt
pip install -r frontend/requirements.txt
pip install requests
```

This installs `psycopg2-binary` and `python-dotenv` (scheduler), `streamlit` and `pandas` (frontend), and `requests` (used by both the scheduling call and the email form).

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

Open http://localhost:5050 and sign in with `admin@example.com` / `admin`. Add a server with host `postgres`, port `5432`, username `postgres`, password `postgrespassword`, database `auto_scheduler`.

---

## 7. Set up n8n (first time only)

Open http://localhost:5678 in your browser.

### 7.1 Create the owner account

On the first visit, n8n asks you to create an owner account. Use any email and password you will remember. This account is only for your local n8n.

### 7.2 Import the scheduling workflow

1. In n8n, go to **Workflows** and create a new workflow (or open the empty canvas).
2. Open the **three-dot menu** (top right) and choose **Import from file**.
3. Select `n8n/n8n_streamlit_integration_v2.json` from the repository.

The workflow is named **Auto-Scheduler Streamlit Integration v2 (conflict routing fix)**. You should see these nodes: Webhook, Python scheduler, Contract Validation, If, conflict handler, AI Agent, Google Gemini Chat Model, Conflict Success, Timetable HTML generator.

> **n8n version note:** The v2 workflow uses HTTP Request node version 4.5. Older n8n builds (for example 2.31.4) only support up to 4.4 and will show the **Python scheduler** node as unknown ("?"). Prefer n8n 2.42+ (or the current Docker image). If you are stuck on an older build, delete the Python scheduler node and re-add an HTTP Request node with the same settings: POST, URL `http://host.docker.internal:8000/schedule`, Send Body on, Body Content Type JSON, body `{{ $json.body }}`.

### 7.3 Add your Gemini credential

1. Open the **Google Gemini Chat Model** node.
2. Under **Credential**, choose **Create new credential** and paste your Gemini API key.
3. Save the credential and close the node.

Skip this if you do not have a key. The workflow still runs, but conflict runs will report an error at the AI Agent step.

### 7.4 Check the Webhook node (scheduling)

Open the **Webhook** node and confirm:

- **HTTP Method:** POST
- **Path:** the path that matches the URL used by Streamlit (see below)
- **Respond:** **When Last Node Finishes** (the response is sent after the whole workflow runs)

The production URL Streamlit calls is:

```text
http://localhost:5678/webhook/08190fdc-b0cf-4c0f-a7c0-b6c60e7595e2
```

That path is hard-coded in `frontend/app.py` as `N8N_WEBHOOK_URL`. If you change the path in n8n, update the constant in `app.py` (or set an environment variable if you prefer).

### 7.5 Activate the scheduling workflow

**Save** the workflow, then switch it to **Active** (toggle at the top right, or the **Publish** button in newer n8n versions).

Only the **active** workflow answers the production webhook. The URL starting with `/webhook-test/` only works once, after you click "Execute workflow", so Streamlit does not use it.

**Only one workflow can use this webhook path at a time.** If you imported earlier versions, deactivate or delete them first.

### 7.6 Import the Gmail Timetable Sender workflow (for email)

This is a **separate** workflow. It does not replace the scheduling workflow.

1. In n8n: **Workflows → Create workflow → ⋯ menu → Import from File**.
2. Choose `n8n/Gmail_Timetable_Sender.json`.
3. You should see nodes including: Webhook (Send Schedule), Validate & Format Email, Request Valid?, Gmail: Send Timetable, and the success / error Respond nodes.

### 7.7 Add a Gmail OAuth2 credential

Credentials stay inside n8n. Nothing secret is stored in this repository.

1. In [Google Cloud Console](https://console.cloud.google.com/), create a project (or reuse one) and enable the **Gmail API**.
2. Configure the **OAuth consent screen** (Google Auth Platform): app name, support email, audience **External**, and add the sending Gmail address as a **test user**.
3. Create an OAuth client of type **Web application**. Under **Authorized redirect URIs**, paste the **OAuth Redirect URL** shown in the n8n credential window. On a default local install this is:

   ```text
   http://localhost:5678/rest/oauth2-credential/callback
   ```

4. In n8n, open the **Gmail: Send Timetable** node → **Credential** → **Create new credential** (Gmail OAuth2 API).
5. Paste the Client ID and Client Secret, then click **Sign in with Google** and allow access.

**Important notes about Gmail sign-in:**

- While the Google app is in **Testing** status, Google expires the sign-in after about **7 days**. Before any demo, open the Gmail credential in n8n and click **Sign in with Google** again.
- Use a dedicated project Gmail account when possible.
- The Gmail node retries up to 3 times (about 10 seconds total) before returning a failure response.

### 7.8 Publish the Gmail workflow

**Save**, then **Publish** / set the workflow to **Active**.

The production URL used by Streamlit is:

```text
http://localhost:5678/webhook/send-schedule
```

(This is the default in `frontend/email_timetable.py`. You can override it with the environment variable `N8N_SEND_SCHEDULE_URL`.)

### 7.9 Optional: test the Gmail workflow on its own

From `<repo>`, with the Gmail workflow published:

```powershell
curl.exe -X POST http://localhost:5678/webhook/send-schedule `
  -H "Content-Type: application/json" `
  --data-binary "@n8n\samples\send_schedule_valid.json"
```

Expected: HTTP 200, JSON with `"success": true`, and an email in the inbox of the address written in the sample file (edit the sample first if you want it to go to your own address).

Invalid sample (should return 400, no email):

```powershell
curl.exe -X POST http://localhost:5678/webhook/send-schedule `
  -H "Content-Type: application/json" `
  --data-binary "@n8n\samples\send_schedule_invalid.json"
```

Use `curl.exe` (not the PowerShell `curl` alias) and pass the JSON as a file so quotes are preserved.

---

## 8. Start the Python scheduler API

Open a **new PowerShell window**, go to `<repo>`, activate the virtual environment, and start it:

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

### Test the n8n scheduling connection by itself (optional but useful)

Before using the page, check that n8n answers correctly:

```powershell
Invoke-RestMethod -Uri http://localhost:5678/webhook/08190fdc-b0cf-4c0f-a7c0-b6c60e7595e2 -Method Post -ContentType "application/json" -Body '{"course_codes":["CSC101","CSC201","MTH101"],"enrollment_overrides":{}}' | ConvertTo-Json -Depth 5
```

You should get the full schedule back (`placed` with three courses). If you get `"message": "Workflow was started"` instead, the active workflow is an old version (see troubleshooting).

---

## 10. Use the app

### 10.1 Prepare your CSV

Your CSV needs one row per course with these five pieces of information. Column names are flexible:

| Required | Example columns accepted |
|---|---|
| Course code | `course_code`, `Course Code`, `code`, `Course` |
| Title | `title`, `Course Title`, `name` |
| Enrolment | `enrollment`, `students`, `Enrolment`, `size` |
| Duration (hours) | `duration`, `hours`, `Duration` |
| Preferred / allowed times (optional) | `preferred_times`, `timeslots` |

A ready-made clean CSV is in the repo:

```text
frontend/test_scheduler_courses.csv
```

Upload that file for a first successful run. To exercise the conflict path, include any of the deliberate failure codes (CSC999, CSC351, CSC352, MTH401, MTH402, MTH403).

### 10.2 Generate a schedule

1. Open http://localhost:8501.
2. Upload your CSV (or the test file).
3. Select the courses you want to schedule.
4. Optionally adjust enrolment numbers.
5. Click **Generate Schedule**.

Streamlit posts to the n8n scheduling webhook. n8n calls the Python API, runs the scheduler, and returns either a timetable or a conflict report.

### 10.3 Read the results

- **Success path:** a table of placed courses (day, time, room, lecturer) and a downloadable CSV.
- **Conflict path:** a list of unplaced courses with reason codes, plus (if Gemini is configured) an AI-written Conflict Resolution Report.

### 10.4 Send the timetable by email (optional)

Under **9. Export**, when at least one course was placed:

1. Enter one or more recipient addresses (comma-separated).
2. Optionally change the subject (default: "Your Course Timetable").
3. Click **Send Timetable**.

Streamlit posts to the Gmail n8n workflow (`/webhook/send-schedule`). The email is HTML, grouped by day, with Time / Course / Title / Lecturer / Room columns.

If the Gmail workflow is not imported or not published, Streamlit shows a clear error telling you how to fix it. A Gmail failure never blocks schedule generation.

---

## 11. Understanding the results

| Field | Meaning |
|---|---|
| `placed` | Courses successfully assigned a timeslot and room |
| `unplaced` | Courses that could not be placed, each with a `reason_code` |
| `violations_count` | Residual hard-constraint violations on the *placed* set (should be 0) |
| `verification_errors` | Human-readable list from the independent verifier |

`reason_code` values:

- `ROOM_CAPACITY` — enrolment exceeds every available room
- `ROOM_EQUIPMENT` — needs a lab/equipment type that is already fully booked
- `CO_ENROLMENT` — clique of co-enrolled courses with too few free slots
- `INSTRUCTOR_CLASH` — instructor hour or overlap limit
- `OTHER` — catch-all

A run can return unplaced courses while `violations_count = 0`. That means everything that *was* placed is conflict-free; the unplaced items are the ones the algorithm could not fit.

---

## 12. Daily quick-start

After the first-time setup is done:

```powershell
# Terminal 1 — infrastructure (if not already running)
cd path\to\Auto-Scheduler-n8n-CapstoneProject-G4
docker compose up -d

# Terminal 2 — Python API
.\.venv\Scripts\Activate.ps1
python -m algorithm.api

# Terminal 3 — Streamlit
.\.venv\Scripts\Activate.ps1
streamlit run frontend/app.py
```

Confirm both n8n workflows are **Active / Published**, then open http://localhost:8501.

---

## 13. Stopping and resetting

```powershell
# Stop Streamlit and the Python API: Ctrl+C in their terminals

# Stop Docker services (keeps data)
docker compose down

# Stop Docker and delete the Postgres volume (full reset of seed data)
docker compose down -v
```

After a volume reset, the next `docker compose up -d` reloads schema and seed data automatically.

---

## 14. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `connection refused` from n8n to the API | Python API not running | Start `python -m algorithm.api` and leave the window open |
| `ModuleNotFoundError: algorithm` | Ran `python algorithm\api.py` instead of the module form | Use `python -m algorithm.api` from the repo root with the venv active |
| n8n returns `"Workflow was started"` only | Old / inactive workflow, or Respond mode is "Immediately" | Use the v2 workflow, set Respond to **When Last Node Finishes**, Publish/Activate |
| Python scheduler node shows "?" in n8n | n8n version too old for HTTP Request 4.5 | Upgrade n8n, or replace the node with a fresh HTTP Request (POST, `http://host.docker.internal:8000/schedule`, JSON body `{{ $json.body }}`) |
| Course code not found | Code not in the seed database | Use only the codes listed in section 6 |
| Gmail send fails / 502 | Credential expired or missing | Re-open the Gmail credential in n8n → Sign in with Google again (Testing apps expire ~7 days) |
| Gmail 404 from Streamlit | Workflow not imported or not published | Import `n8n/Gmail_Timetable_Sender.json` and Publish it |
| Port already in use | Another process on 5432 / 5678 / 8000 / 8501 | Stop the other process or change the port in `.env` / Streamlit |
| `host.docker.internal` fails on Linux | Docker networking | Add `extra_hosts: ["host.docker.internal:host-gateway"]` under the n8n service in `docker-compose.yml` |

---

## 15. Reference

| Item | Value |
|---|---|
| Scheduling webhook (Streamlit → n8n) | `http://localhost:5678/webhook/08190fdc-b0cf-4c0f-a7c0-b6c60e7595e2` |
| Gmail webhook (Streamlit → n8n) | `http://localhost:5678/webhook/send-schedule` |
| Python API | `http://localhost:8000` (`GET /health`, `POST /schedule`) |
| From n8n container to API | `http://host.docker.internal:8000/schedule` |
| Scheduling workflow file | `n8n/n8n_streamlit_integration_v2.json` |
| Gmail workflow file | `n8n/Gmail_Timetable_Sender.json` |
| Full Gmail docs | `docs/integrations/GMAIL_N8N_INTEGRATION.md` |
| Streamlit ↔ Gmail docs | `docs/integrations/STREAMLIT_GMAIL_CONNECTION.md` |
| Test CSV (clean) | `frontend/test_scheduler_courses.csv` |

---

*Guide maintained for Group 4 Capstone · Auto-Scheduler n8n · last aligned with Gmail + Streamlit integration (Oct 2026).*
