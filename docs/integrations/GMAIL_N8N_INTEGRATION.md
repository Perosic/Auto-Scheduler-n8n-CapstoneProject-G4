# Gmail Timetable Integration (n8n)

**Branch:** `feat/p1-gmail-n8n`
**Tier:** P1 (email delivery of the generated timetable)
**Workflow file:** `n8n/Gmail_Timetable_Sender.json`

## 1. What this does

The Gmail Timetable Sender is a standalone n8n workflow. It receives a generated timetable over a webhook, formats it into a readable email and sends it to the recipient named in the request through Gmail.

```text
Streamlit Scheduler (later)  or  any HTTP client (now)
        ↓  POST /webhook/send-schedule
Webhook: Send Schedule
        ↓
Validate & Format Email   (checks the request, sorts by day/time, builds the email)
        ↓
Request Valid?
   ├─ false → Respond: Invalid Request (400)
   └─ true  → Gmail: Send Timetable
                 ├─ sent   → Respond: Sent (200)
                 └─ failed → Respond: Gmail Failed (502)
```

The workflow does not depend on the Python scheduler API, Postgres or Streamlit, so it can be tested on its own with a sample JSON payload.

No files in `frontend/` or `algorithm/` were changed.

## 2. Endpoint

| Item | Value |
|---|---|
| Method | `POST` |
| Production URL | `http://localhost:5678/webhook/send-schedule` |
| Test URL (while "Execute workflow" is listening in the editor) | `http://localhost:5678/webhook-test/send-schedule` |
| Content-Type | `application/json` |
| Authentication | None on the local stack (see section 8) |

The production URL only works after the workflow is **published** (n8n 2.x) or **activated** (n8n 1.x).

## 3. Request format

Formal schema: `n8n/schemas/send_schedule.request.schema.json`

```json
{
  "recipient": "student@example.com",
  "subject": "Your Course Timetable",
  "schedule": [
    {
      "course": "CSC101",
      "title": "Computer Science",
      "day": "Monday",
      "time": "09:00 - 11:00",
      "room": "CR101"
    }
  ]
}
```

| Field | Required | Notes |
|---|---|---|
| `recipient` | Yes | One email address, or several separated by commas. Set per request, so the recipient is dynamic. |
| `subject` | No | Defaults to `Your Course Timetable`. |
| `schedule` | Yes | List with at least one entry. |
| `schedule[].course` | Yes | Course code. |
| `schedule[].title` | No | Course title. Left blank in the email if missing. |
| `schedule[].day` | Yes | e.g. `Monday`. Entries are sorted Monday to Sunday. |
| `schedule[].time` | Yes | e.g. `09:00 - 11:00`. Entries on the same day are sorted by this. |
| `schedule[].room` | Yes | Room code. |

Extra fields are ignored. This means the `placed` list returned by the scheduler (`algorithm/run.py` through the API, or `algorithm/frontend_scheduler.py`) can be sent as `schedule` without reshaping: its items already contain `course`, `title`, `day`, `time` and `room`.

The scheduler returns short day names and times with seconds (`"day": "Mon"`, `"time": "09:00:00 - 10:00:00"`). The workflow converts these for the email to `Monday` and `09:00 - 10:00`. Full day names and times without seconds are left as they are.

## 4. Response format

Formal schema: `n8n/schemas/send_schedule.response.schema.json`

**200: email sent**

```json
{
  "success": true,
  "message": "Timetable email sent successfully",
  "recipient": "student@example.com",
  "entries_sent": 3,
  "gmail_message_id": "19a2b3c4d5e6f7a8"
}
```

**400: invalid request (nothing was sent)**

```json
{
  "success": false,
  "message": "Invalid timetable request. Email was not sent.",
  "errors": [
    "\"recipient\" contains an invalid email address: not-an-email",
    "schedule[0] is missing: room."
  ]
}
```

**502: Gmail could not send the email**

```json
{
  "success": false,
  "message": "Failed to send timetable email through Gmail.",
  "error": "<error message returned by the Gmail node>",
  "recipient": "student@example.com"
}
```

Callers should check `success` first, then show `errors` (400) or `error` (502) to the user.

## 5. Email content

The email is sent as HTML: a heading with the subject, a count of classes, and a table grouped by day with Time, Course, Title and Room columns. All values are HTML-escaped. The n8n attribution footer is turned off and the sender name is `Group 4 Auto-Scheduler`.

The formatting node also produces a plain-text version that follows the task example:

```text
Your Course Timetable

CSC101 - Computer Science
Monday | 09:00 - 11:00 | CR101

CSC201 - Database Systems
Tuesday | 11:00 - 13:00 | CR202
```

## 6. Setup

### 6.1 Import the workflow

1. In n8n: **Workflows → Create workflow → ⋯ menu → Import from File**, then choose `n8n/Gmail_Timetable_Sender.json`.
2. Open **Gmail: Send Timetable** and select a Gmail credential (6.2).
3. Save, then **Publish** the workflow so the production URL is live.

### 6.2 Gmail credential (Google OAuth2)

Credentials stay inside n8n. Nothing secret is stored in this repository.

1. In Google Cloud Console, create a project and enable the **Gmail API**.
2. Configure the OAuth consent screen (Google Auth Platform): app name, support email, audience **External**, and add the sending Gmail address as a **test user**.
3. Create an OAuth client of type **Web application**. Under **Authorized redirect URIs**, paste the **OAuth Redirect URL** shown in the n8n credential window. On a default local install this is:
   `http://localhost:5678/rest/oauth2-credential/callback`
4. In n8n, create a **Gmail OAuth2 API** credential, paste the Client ID and Client Secret, then click **Sign in with Google** and allow access.

Notes:

- While the Google app is in **Testing** status, Google expires the sign-in after about 7 days. Reconnect the credential before a demo.
- Use a project/test Gmail account as the sender rather than a personal account.
- `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env.example` are placeholders only. Do not commit real values.

## 7. Testing without Streamlit

Sample payloads are in `n8n/samples/`:

- `send_schedule_valid.json`: the 3-class example from the task sheet
- `send_schedule_seed_data.json`: the real scheduler output from the project seed data (21 placed classes, produced by `algorithm/run.py` against `database/seed_data.sql`)
- `send_schedule_invalid.json`: a bad request (invalid recipient, missing room)

Replace `student@example.com` with an inbox you can check before sending a valid sample. Do not commit your own email address.

Windows PowerShell (use `curl.exe`, not `curl`, and send the file with `@` so PowerShell does not strip quotes):

```text
curl.exe -i -X POST http://localhost:5678/webhook/send-schedule -H "Content-Type: application/json" --data-binary "@n8n\samples\send_schedule_valid.json"

curl.exe -i -X POST http://localhost:5678/webhook/send-schedule -H "Content-Type: application/json" --data-binary "@n8n\samples\send_schedule_invalid.json"
```

macOS / Linux:

```bash
curl -i -X POST http://localhost:5678/webhook/send-schedule \
  -H "Content-Type: application/json" \
  --data-binary @n8n/samples/send_schedule_valid.json
```

Expected:

| Test | Expected result |
|---|---|
| Valid sample | HTTP 200, `success: true`, email arrives with 3 classes (Monday ×2, Tuesday ×1) |
| Invalid sample | HTTP 400, `success: false`, two errors (bad recipient, missing room), no email |
| Valid sample with the Gmail credential removed or disconnected | HTTP 502, `success: false` with the Gmail error message |

## 8. Connecting Streamlit later

The Streamlit owner can call the webhook after a run, for example:

```python
import requests

resp = requests.post(
    "http://localhost:5678/webhook/send-schedule",
    json={
        "recipient": recipient_email,
        "subject": "Your Course Timetable",
        "schedule": result["placed"],
    },
    timeout=30,
)
data = resp.json()
if data.get("success"):
    st.success(data["message"])
else:
    st.error(data.get("error") or "; ".join(data.get("errors", [])))
```

The webhook URL should be read from configuration (for example an `N8N_SEND_SCHEDULE_URL` entry in `.env`) rather than hard-coded. If the webhook is exposed beyond localhost, add Header Auth on the Webhook node and keep the header secret in `.env` and in an n8n credential.

## 9. Test results

| Item | Result |
|---|---|
| n8n version | 2.31.4 |
| Workflow import | Imported with no unknown nodes |
| Invalid sample (5 Oct 2026) | HTTP 400 with the two expected errors (bad recipient, missing room); no email sent |
| Gmail failure path (no credential) | HTTP 502 with `Node does not have any credentials set` |
| Valid sample with Gmail credential (5 Oct 2026) | HTTP 200, `success: true`, `entries_sent: 3`; email received in Gmail inbox with all 3 classes grouped by day (screenshot in PR) |
| Project seed data (5 Oct 2026): real scheduler output (21 placed classes, `Mon`/`Tue`, times with seconds) | HTTP 200, `entries_sent: 21`; email received with Monday (16 classes) and Tuesday (5 classes), times shown as HH:MM (screenshot in PR) |
