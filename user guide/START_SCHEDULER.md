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
.\venv\Scripts\Activate.ps1
pip install -r algorithm/requirements.txt
pip install -r frontend/requirements.txt
pip install requests
```

This installs `psycopg2-binary` and `python-dotenv` (scheduler), `streamlit` and `pandas` (frontend), and `requests` (used by both the scheduling call and the email form).

**You must activate the virtual environment in every new PowerShell window** before running the scheduler or Streamlit:

```powershell
.\venv\Scripts\Activate.ps1
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
.\venv\Scripts\Activate.ps1
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
.\venv\Scripts\Activate.ps1
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
7. **Results:** the timetable, filters (day, room, lecturer), unplaced courses (if any), and the conflict report (if any).
8. **Export:**
   - Download the timetable as CSV.
   - **Send Timetable by Email** (see next subsection).

### 10.3 Send the timetable by email

After at least one course has been placed, section **9. Export** shows a form:

- **Recipient email** — one address, or several separated by commas.
- **Subject** — defaults to `Your Course Timetable`.
- **Send Timetable** button.

What happens when you click **Send Timetable**:

1. Streamlit validates the addresses.
2. It builds a payload from the **full** placed list (not the filtered view you may be looking at):

   ```json
   {
     "recipient": "student@example.com",
     "subject": "Your Course Timetable",
     "schedule": [
       {
         "course": "CSC101",
         "title": "Intro to Programming",
         "lecturer": "Dr. Ada Okonkwo",
         "day": "Mon",
         "time": "09:00:00 - 10:00:00",
         "room": "LT2"
       }
     ]
   }
   ```

3. It POSTs to `http://localhost:5678/webhook/send-schedule` (or the value of `N8N_SEND_SCHEDULE_URL`).
4. The Gmail workflow formats the email (groups by day, expands `Mon` → `Monday`, strips seconds from times, adds a Lecturer column when lecturers are present) and sends it through Gmail.

Messages you may see:

| Situation | Message on the page |
|---|---|
| Success | ✅ Timetable sent to … |
| Empty or badly typed address | Error listing the bad address; nothing sent |
| Gmail workflow rejects the request (HTTP 400) | Error plus the workflow’s reasons |
| Gmail fails (expired sign-in, no credential, etc.) → HTTP 502 | Gmail error text shown |
| Workflow not imported / not published (404) | Instruction to import and publish `Gmail_Timetable_Sender.json` |
| n8n not running | “Could not connect to n8n” |

The email is HTML (table grouped by day: Time, Course, Title, Lecturer, Room) with a plain-text alternative. The sender name is **Group 4 Auto-Scheduler**.

### 10.4 Happy-path test

Upload `frontend/test_scheduler_courses.csv`, leave all courses selected, and click **Generate Schedule**. You should see a green success message and a timetable with every course placed. Then enter your email under Export and click **Send Timetable**. You should receive the email within a few seconds.

### 10.5 Test the conflict path

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

You can still email the **placed** courses from the Export section even on a conflict run.

In n8n, open the **Executions** tab to see which path each run took. Successful runs go through *Timetable HTML generator*; conflict runs go through *conflict handler → AI Agent → Conflict Success*. Gmail runs appear under the Gmail workflow’s executions.

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

After n8n processes the result, the response returned to Streamlit may also contain `html` (a ready-made timetable page), `message`, and `resolution_report` (the AI conflict explanation).

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
.\venv\Scripts\Activate.ps1
python -m algorithm.api
```

**Window 3 — Streamlit**

```powershell
cd path\to\Auto-Scheduler-n8n-CapstoneProject-G4
.\venv\Scripts\Activate.ps1
streamlit run frontend/app.py
```

Then open http://localhost:8501. Check that **both** workflows are still **Active / Published** at http://localhost:5678 (scheduling workflow and Gmail Timetable Sender).

If email suddenly stops working after about a week, re-sign in to the Gmail credential in n8n (Google Testing-mode expiry).

---

## 13. Stopping and resetting

**Stop the Python processes:** close the PowerShell windows running the API and Streamlit, or press `Ctrl+C` in each.

**Stop Docker services (keeps data and n8n workflows):**

```powershell
docker compose down
```

Start again later with `docker compose up -d`. Your database and n8n workflows are kept.

**Full reset (deletes the database AND your n8n workflows, accounts and credentials):**

```powershell
docker compose down -v
```

Use this only if you want a clean start. After it, you must repeat section 7 (n8n account, both workflow imports, credentials, activation/publish). The database reloads automatically from `schema.sql` and `seed_data.sql`.

---

## 14. Troubleshooting

### Streamlit or webhook: HTTP 404 from n8n (scheduling)

The scheduling workflow is not active, or another workflow holds the same path. In n8n, open the Workflows list, deactivate any old versions, and activate the v2 workflow. Make sure the Webhook node's path matches `N8N_WEBHOOK_URL` in `frontend/app.py`.

### The webhook returns `{"message": "Workflow was started"}` and no timetable

The active workflow responds immediately instead of waiting. Open the **Webhook** node and set **Respond** to **When Last Node Finishes**, save, then switch the workflow off and on again. Also check for an old duplicate workflow that is still active.

### Conflict path never runs / PARTIAL treated as success

You are running an old copy of the workflow whose **If** node checks for `status equals CONFLICT`. The v2 workflow checks `status not equals SUCCESS`. Re-import `n8n/n8n_streamlit_integration_v2.json`.

### “Connection refused” from n8n to the Python API

The Python scheduler is not running, or n8n cannot reach `host.docker.internal:8000`. Start the API with `python -m algorithm.api` and keep the window open. On Linux you may need the `extra_hosts` entry mentioned in section 5.

### AI Agent / Gemini error on conflict runs

The Gemini credential is missing or invalid. In n8n, open the **Executions** tab, open the failed run, and look at the **AI Agent** node. Add or fix the credential on the **Google Gemini Chat Model** node.

### Email: “The Gmail workflow was not found” (404)

Import `n8n/Gmail_Timetable_Sender.json`, connect a Gmail credential on the **Gmail: Send Timetable** node, and **Publish** the workflow. The production path must be `send-schedule`.

### Email: “Could not connect to n8n”

ning. Start Docker (`docker compose up -d`) and confirm http://localhost:5678 loads.

### Email: HTTP 502 / Gmail error text

Usually an expired or missing Gmail OAuth credential. Open the Gmail credential in n8n and click **Sign in with Google** again (required roughly every 7 days while the Google app is in Testing mode). Also check that the Gmail API is enabled in Google Cloud Console and that the sending address is listed as a test user.

### Email: validation errors (HTTP 400)

The payload is missing required fields or has an invalid recipient. The page shows the reasons returned by the workflow. Common causes: empty recipient, malformed address, or an empty `schedule` list.

### Course codes not found / missing courses

Every `course_code` in the CSV must exist in the seeded database (section 6). Use `frontend/test_scheduler_courses.csv` for a known-good set.

### The database seems to have old or missing data

Seed data only loads the first time. Do the full reset in section 13, then redo the n8n setup.

### A CSV is rejected by the page

Check the **Column Mapping** table on the page. A field showing "Not found" needs a column renamed to one of the accepted names in section 10.1. The page also rejects negative student counts and duplicate course codes.

### Python module / package errors

Always run the API with `python -m algorithm.api` from the repo root with the virtual environment activated. Install both requirement files and `requests` (section 5).

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

### Gmail webhook (email delivery)

| Item | Value |
|---|---|
| Method | `POST` |
| Production URL | `http://localhost:5678/webhook/send-schedule` |
| Content-Type | `application/json` |
| Workflow file | `n8n/Gmail_Timetable_Sender.json` |

**Request body:**

```json
{
  "recipient": "student@example.com",
  "subject": "Your Course Timetable",
  "schedule": [
    {
      "course": "CSC101",
      "title": "Computer Science",
      "lecturer": "Dr. Ada Okonkwo",
      "day": "Monday",
      "time": "09:00 - 11:00",
      "room": "CR101"
    }
  ]
}
```

| Field | Required | Notes |
|---|---|---|
| `recipient` | Yes | One address or several separated by commas |
| `subject` | No | Defaults to `Your Course Timetable` |
| `schedule` | Yes | At least one entry |
| `schedule[].course` | Yes | Course code |
| `schedule[].title` | No | Course title |
| `schedule[].lecturer` | No | Shown as a Lecturer column when present; `instructor` is also accepted |
| `schedule[].day` | Yes | Day name or short form (`Mon`, etc.) |
| `schedule[].time` | Yes | Time range |
| `schedule[].room` | Yes | Room code |

**Responses:**

- **200** — `"success": true`, email sent
- **400** — `"success": false`, validation errors listed
- **502** — `"success": false`, Gmail could not send (credential, network, etc.)

Full schemas: `n8n/schemas/send_schedule.request.schema.json` and `n8n/schemas/send_schedule.response.schema.json`.  
Sample payloads: `n8n/samples/send_schedule_valid.json`, `send_schedule_invalid.json`, `send_schedule_seed_data.json`.

### Default credentials (local development only)

| Service | Login |
|---|---|
| PostgreSQL | user `postgres`, password `postgrespassword`, database `auto_scheduler` |
| pgAdmin | `admin@example.com` / `admin` |
| n8n | the owner account you create on first visit |
| Gmail | the Google account you connect inside the n8n Gmail credential |

These are development defaults for a local machine. Change them before exposing anything to a network.

### Dependency summary

| File | Packages |
|---|---|
| `algorithm/requirements.txt` | psycopg2-binary, python-dotenv |
| `frontend/requirements.txt` | streamlit, pandas |
| (extra) | requests (used by `frontend/app.py` and `frontend/email_timetable.py`) |

### Startup order at a glance

```text
Docker Desktop
      ↓
docker compose up -d        (PostgreSQL + n8n + …)
      ↓
n8n: import & activate scheduling workflow (v2)
n8n: import Gmail Timetable Sender, add Gmail credential, Publish
      ↓
python -m algorithm.api     (Python scheduler on port 8000)
      ↓
streamlit run frontend/app.py   (frontend on port 8501)
      ↓
Upload CSV → Generate Schedule → (optional) Send Timetable by Email
```

### Related documentation in the repo

| Document | Content |
|---|---|
| `docs/integrations/GMAIL_N8N_INTEGRATION.md` | Full Gmail workflow design, setup, testing |
| `docs/integrations/STREAMLIT_GMAIL_CONNECTION.md` | How Streamlit calls the Gmail webhook |
| `docs/handoff/GMAIL_INTEGRATION_WORK_SUMMARY.md` | Work summary and decisions |
| `docs/handoff/N8N_WORKFLOW_GUIDE.md` | Scheduling workflow notes |
