# User Guide — Start the Auto-Scheduler Stack

This is the complete quick-start procedure for running the Auto-Scheduler locally, including Docker/PostgreSQL, the Python scheduler API, Streamlit, and the n8n integration.

## 1. Prerequisites

You need:

- Git
- Docker Desktop
- Python 3.x
- The project repository
- The project's `.venv` virtual environment

Project directory:

```text
C:\Users\hp\Auto-Scheduler-n8n-CapstoneProject-G4
```

## 2. Install and start Docker Desktop

Install Docker Desktop for your operating system if it is not already installed. After installation, open **Docker Desktop** and wait until Docker reports that it is running.

Verify Docker from PowerShell:

```powershell
docker --version
docker compose version
```

Both commands should return version information.

## 3. Start the project's Docker services

From the repository root:

```powershell
cd C:\Users\hp\Auto-Scheduler-n8n-CapstoneProject-G4
```

Check the current containers:

```powershell
docker compose ps
```

Start the services defined by the repository's Compose configuration:

```powershell
docker compose up -d
```

The first run may download or build the required Docker images. This can take longer than subsequent runs.

If you want to pull the Compose images before starting them:

```powershell
docker compose pull
```

Then:

```powershell
docker compose up -d
```

**Do not manually invent image names.** Use the images and services defined by this repository's Compose configuration.

Check that the containers are running:

```powershell
docker compose ps
```

If a service is still starting, wait a few seconds and run `docker compose ps` again.

To see the services defined by the Compose file:

```powershell
docker compose config --services
```

## 4. Confirm PostgreSQL is running

The Python scheduler loads scheduling data from PostgreSQL. If PostgreSQL is not running, the scheduler's `/health` endpoint will report a database connection error such as:

```text
Could not connect to Postgres
localhost:5432
Connection refused
```

First check:

```powershell
docker compose ps
```

Make sure the PostgreSQL service is running.

If needed, inspect the database logs. If the service is named `postgres`:

```powershell
docker compose logs postgres
```

If it has another service name, find it with:

```powershell
docker compose config --services
```

Then use:

```powershell
docker compose logs <service-name>
```

## 5. Activate the Python virtual environment

Open a new PowerShell window and go to the project root:

```powershell
cd C:\Users\hp\Auto-Scheduler-n8n-CapstoneProject-G4
```

Activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Your prompt should begin with something similar to:

```text
(.venv) PS C:\Users\hp\Auto-Scheduler-n8n-CapstoneProject-G4>
```

## 6. Start the Python scheduler API

**Use this exact command:**

```powershell
python -m algorithm.api
```

The API should display something similar to:

```text
======================================
 Auto-Scheduler Python API
 http://localhost:8000
 POST /schedule
 GET  /health
======================================
```

### Important: do not start it this way

Do **not** use:

```powershell
python algorithm\api.py
```

The API imports the `algorithm` package. Starting it as a package module with:

```powershell
python -m algorithm.api
```

allows imports such as `algorithm.run` to resolve correctly.

### Important: Python code is not PowerShell

Do not paste Python statements such as:

```python
from algorithm.run import run_scheduler
```

into PowerShell. That produces the PowerShell error:

```text
The 'from' keyword is not supported in this version of the language.
```

Use the Python module command instead:

```powershell
python -m algorithm.api
```

## 7. Keep the scheduler terminal running

Do **not** close the terminal running:

```powershell
python -m algorithm.api
```

The scheduler must remain running while Streamlit or n8n sends requests to it.

## 8. Test the scheduler health endpoint

Open a **second PowerShell window**. You can activate the virtual environment there as well:

```powershell
cd C:\Users\hp\Auto-Scheduler-n8n-CapstoneProject-G4
.\.venv\Scripts\Activate.ps1
```

Then run:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

The API should respond successfully when both the Python API and PostgreSQL are available.

If you receive:

```text
Could not connect to Postgres
localhost:5432
Connection refused
```

the Python API is running, but PostgreSQL is not available yet. Return to the Docker steps:

```powershell
docker compose up -d
docker compose ps
```

Then retry:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

## 9. Start Streamlit

Open another PowerShell terminal:

```powershell
cd C:\Users\hp\Auto-Scheduler-n8n-CapstoneProject-G4
.\.venv\Scripts\Activate.ps1
streamlit run frontend/app.py
```

Keep this terminal running while testing the frontend.

## 10. n8n integration

The n8n workflow calls the Python scheduler using:

```text
POST http://host.docker.internal:8000/schedule
```

This address is important when n8n is running inside Docker and the Python API is running on the Windows host.

The intended flow is:

```text
Streamlit / Test Client
        |
        | POST JSON
        v
     n8n Webhook
        |
        v
  Python Scheduler
        |
        v
 Contract Validation
        |
        v
       IF
      /  \
 conflict  timetable
 handling   output
```

Before testing the n8n Python Scheduler node, confirm:

1. Docker Desktop is running.
2. PostgreSQL is running through Docker Compose.
3. n8n is running.
4. The Python API is running on port `8000`.
5. `Invoke-RestMethod http://localhost:8000/health` succeeds.
6. The n8n Python Scheduler node uses `POST http://host.docker.internal:8000/schedule`.

## 11. Quick-start: every time you work on the project

### Terminal 1 — Docker services

Start Docker Desktop, then:

```powershell
cd C:\Users\hp\Auto-Scheduler-n8n-CapstoneProject-G4
docker compose up -d
docker compose ps
```

### Terminal 2 — Python scheduler

```powershell
cd C:\Users\hp\Auto-Scheduler-n8n-CapstoneProject-G4
.\.venv\Scripts\Activate.ps1
python -m algorithm.api
```

Leave this terminal running.

### Terminal 3 — Health check

```powershell
cd C:\Users\hp\Auto-Scheduler-n8n-CapstoneProject-G4
.\.venv\Scripts\Activate.ps1
Invoke-RestMethod http://localhost:8000/health
```

### Terminal 4 — Streamlit

```powershell
cd C:\Users\hp\Auto-Scheduler-n8n-CapstoneProject-G4
.\.venv\Scripts\Activate.ps1
streamlit run frontend/app.py
```

Then use n8n for workflow/integration tests.

## 12. Troubleshooting

### `ModuleNotFoundError: No module named 'algorithm'`

Use:

```powershell
python -m algorithm.api
```

not:

```powershell
python algorithm\api.py
```

Also make sure PowerShell is currently in the repository root.

### `The 'from' keyword is not supported in this version of the language`

You pasted Python code directly into PowerShell. For example, this is Python code:

```python
from algorithm.run import run_scheduler
```

Start the API with:

```powershell
python -m algorithm.api
```

### `Could not connect to Postgres` / port `5432` connection refused

Start Docker Desktop and the Compose services:

```powershell
docker compose up -d
docker compose ps
```

Then retry:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

### n8n reports `ECONNREFUSED` or cannot connect to port `8000`

Make sure the Python API is still running:

```powershell
python -m algorithm.api
```

Then verify from the Windows host:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

Do not close the API terminal while n8n is testing the workflow.

### Docker Compose cannot start

Check Docker Desktop first:

```powershell
docker --version
docker compose version
docker compose ps
```

Then inspect available Compose services:

```powershell
docker compose config --services
```

For a service that fails to start, inspect logs:

```powershell
docker compose logs <service-name>
```

## 13. Current integration checkpoint

The n8n Webhook has already been successfully tested with a POST JSON payload. The Python scheduler API is implemented in `algorithm/api.py` and exposes `/health` and `/schedule`.

The correct startup sequence is:

```text
Docker Desktop
      ↓
docker compose up -d
      ↓
PostgreSQL + n8n
      ↓
python -m algorithm.api
      ↓
GET /health
      ↓
Streamlit
      ↓
n8n Webhook → Python Scheduler → Contract Validation
```

Keep this guide with the repository so contributors do not need to search the codebase to discover how to start the scheduler.
