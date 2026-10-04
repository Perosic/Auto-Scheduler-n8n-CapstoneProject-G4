# User Guide — Start the Python Scheduler

## Purpose

This is the quick-start guide for running the project's Python scheduler API locally so that n8n can call it.

The scheduler API is implemented in:

```text
algorithm/api.py
```

It provides:

```text
GET  /health
POST /schedule
```

n8n calls the scheduler at:

```text
http://host.docker.internal:8000/schedule
```

## 1. Open PowerShell in the project root

Go to:

```powershell
cd C:\Users\hp\Auto-Scheduler-n8n-CapstoneProject-G4
```

You should be in the repository root, where the `algorithm`, `frontend`, and `n8n` folders are located.

## 2. Activate the virtual environment

If it is not already active:

```powershell
.\.venv\Scripts\Activate.ps1
```

Your prompt should begin with something similar to:

```text
(.venv) PS C:\Users\hp\Auto-Scheduler-n8n-CapstoneProject-G4>
```

## 3. Start the scheduler API

**Use this command exactly:**

```powershell
python -m algorithm.api
```

### Important

Do **not** use:

```powershell
python algorithm\api.py
```

The API imports the `algorithm` package. Running it with `python -m algorithm.api` starts it as a package module and avoids the `ModuleNotFoundError: No module named 'algorithm'` problem.

Also, do not paste Python statements such as:

```python
from algorithm.run import run_scheduler
```

into PowerShell. That is Python code, not a PowerShell command.

The Python `-m` option runs a module through Python's normal module/package import mechanism.

## 4. Leave the scheduler terminal running

Do not close the terminal running:

```powershell
python -m algorithm.api
```

The scheduler must remain running while n8n sends requests to it.

## 5. Test the health endpoint

Open a **second PowerShell window** and run:

```powershell
cd C:\Users\hp\Auto-Scheduler-n8n-CapstoneProject-G4
.\.venv\Scripts\Activate.ps1
Invoke-RestMethod http://localhost:8000/health
```

A successful response confirms that the scheduler API is listening on port `8000`.

## 6. Start Streamlit when needed

In another terminal, from the project root:

```powershell
cd C:\Users\hp\Auto-Scheduler-n8n-CapstoneProject-G4
.\.venv\Scripts\Activate.ps1
streamlit run frontend/app.py
```

The Streamlit application should then provide its local URL in the terminal.

## 7. Test the n8n integration

Make sure:

1. The Python scheduler terminal is still running.
2. n8n is running.
3. The n8n Webhook is configured as `POST`.
4. The n8n `Python scheduler` HTTP Request node uses:

```text
Method: POST
URL: http://host.docker.internal:8000/schedule
```

5. The Python scheduler node forwards the Webhook request body as JSON.

The expected flow is:

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

## 8. If you see `ModuleNotFoundError: No module named 'algorithm'`

First check that the terminal is in the repository root:

```text
C:\Users\hp\Auto-Scheduler-n8n-CapstoneProject-G4
```

Then activate `.venv` and run:

```powershell
python -m algorithm.api
```

Do not run `python algorithm\api.py` from the project root for this API.

## 9. If n8n says `ECONNREFUSED` or `The service refused the connection`

This normally means the scheduler API is not running or is not listening on port `8000`.

Check:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

If that fails, return to the scheduler terminal and start it again:

```powershell
python -m algorithm.api
```

Keep the scheduler terminal open while testing n8n.

## Quick reference

### Terminal 1 — Python scheduler

```powershell
cd C:\Users\hp\Auto-Scheduler-n8n-CapstoneProject-G4
.\.venv\Scripts\Activate.ps1
python -m algorithm.api
```

### Terminal 2 — Health check

```powershell
cd C:\Users\hp\Auto-Scheduler-n8n-CapstoneProject-G4
.\.venv\Scripts\Activate.ps1
Invoke-RestMethod http://localhost:8000/health
```

### Terminal 3 — Streamlit

```powershell
cd C:\Users\hp\Auto-Scheduler-n8n-CapstoneProject-G4
.\.venv\Scripts\Activate.ps1
streamlit run frontend/app.py
```

## Current integration checkpoint

At the point this guide was created, the n8n Webhook had already been successfully tested with a POST JSON payload. The remaining integration checkpoint was ensuring the Python scheduler API is running on port `8000` so the n8n `Python scheduler` node can reach `POST /schedule`.
