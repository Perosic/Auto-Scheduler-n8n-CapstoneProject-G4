# Streamlit to Gmail Connection

**Branch:** `feat/p1-streamlit-gmail`
**Depends on:** PR #13 (`feat/p1-gmail-n8n`), which adds the n8n Gmail Timetable Sender workflow

## 1. What this adds

After a timetable is generated in Streamlit, the user can send it to one or more email addresses from the same page.

```text
Streamlit: Generate Schedule
   → n8n v2 workflow (webhook 08190fdc...) → Python scheduler → timetable / AI report
   → back to Streamlit

Streamlit: Send Timetable by Email  (new, section 9 "Export")
   → n8n Gmail Timetable Sender (POST /webhook/send-schedule)
   → Gmail → recipient's inbox
```

The scheduling workflow (`n8n/n8n_streamlit_integration_v2.json`) is not changed. Email is a separate step the user triggers, so a timetable is never emailed by accident and a Gmail problem cannot break schedule generation.

## 2. Files

| File | Change |
|---|---|
| `frontend/email_timetable.py` | New. Builds the request from the `placed` list, calls the Gmail webhook, shows the form and the result. |
| `frontend/app.py` | 4 lines: one import, and one call to `render_email_section(placed)` under the CSV download button. |

The email code is kept in its own file so front-end polish work on `app.py` does not clash with it.

## 3. How it works

- The form appears under **9. Export** whenever at least one course was placed, on both the conflict-free and the conflict path.
- Fields: recipient email (several allowed, separated by commas) and subject (defaults to "Your Course Timetable").
- On **Send Timetable**, the page checks the addresses, then posts to the Gmail workflow:

```json
{
  "recipient": "student@example.com",
  "subject": "Your Course Timetable",
  "schedule": [
    { "course": "CSC101", "title": "Intro to Programming", "lecturer": "Dr. Ada Okonkwo", "day": "Mon", "time": "09:00:00 - 10:00:00", "room": "LT2" }
  ]
}
```

- The full timetable is sent (all placed courses), not the filtered view.
- Each class includes its lecturer, so the email has a Lecturer column like the Streamlit timetable. ("Lecturer" is the scheduler's field name; the database calls them instructors.)
- The Gmail workflow converts `Mon` and `09:00:00` to `Monday` and `09:00` in the email.

Messages the user can see:

| Situation | Message |
|---|---|
| Sent | ✅ Timetable sent to ... |
| Empty or badly typed address | Error listing the address, nothing sent |
| Gmail workflow rejects the request (HTTP 400) | Error plus the workflow's reasons |
| Gmail fails, e.g. expired sign-in (HTTP 502) | Error plus the Gmail error text |
| Gmail workflow not imported or not published (HTTP 404) | Error explaining how to import and publish it |
| n8n not running | "Could not connect to n8n" |

## 4. Configuration

The webhook address defaults to `http://localhost:5678/webhook/send-schedule`. To use a different address, set the environment variable `N8N_SEND_SCHEDULE_URL` before starting Streamlit. No credentials are stored in the app.

## 5. Setup on a new laptop

1. Follow `user guide/START_SCHEDULER.md` to run the database, scheduler, n8n v2 workflow and Streamlit.
2. Import `n8n/Gmail_Timetable_Sender.json` into the same n8n, connect a Gmail OAuth2 credential on the Gmail node and publish it (see `docs/integrations/GMAIL_N8N_INTEGRATION.md`).
3. Start Streamlit, generate a timetable, scroll to **9. Export**, enter an email and click **Send Timetable**.

## 6. Test results

Tested on 7 October 2026 against `main` at `c0432f9`, with the full stack running locally (PostgreSQL seed data, Python scheduler API, n8n 2.31.4 with the v2 workflow and the Gmail Timetable Sender, Streamlit 1.65). The Gmail and Gemini steps were replaced by stubs for this run; the real Gmail send was tested separately in PR #13.

| Test | Result |
|---|---|
| Conflict-free CSV (4 courses) → Generate → Send | Timetable generated, "Timetable sent to student@example.com" |
| Conflict CSV (5 courses, 3 unplaced) → Generate → Send to two addresses | Conflict path ran, 2 placed courses emailed, "Timetable sent to a@x.com, b@y.org" |
| Badly typed address | Error shown, nothing sent |
| Empty timetable sent to workflow | HTTP 400 reason shown |
| Gmail workflow missing (404) | Import/publish instruction shown |
| n8n not running | "Could not connect to n8n" |
| Gmail failure (502) | Gmail error text shown |
| Non-JSON server error | "Unexpected response" with details |

**Live test on a team laptop (7 October 2026, Windows, n8n 2.42.4):** a 4-course conflict-free CSV was uploaded in Streamlit, the timetable was generated through the v2 workflow, and **Send Timetable** delivered the email through the real Gmail credential. Streamlit showed "Timetable sent to ...", and the email arrived with all 4 classes under Monday, times shown as 09:00 - 10:00. After the Lecturer column was added to the Gmail workflow (PR #13), the same test was repeated and the email showed Time, Course, Title, Lecturer and Room with the correct lecturer names.

**Not yet tested live:** the conflict path with a real Gemini key followed by an email send.

## 7. Note on n8n versions

`n8n/n8n_streamlit_integration_v2.json` uses HTTP Request node version 4.5. n8n 2.31.4 only supports up to 4.4, so on that version the **Python scheduler** node shows as an unknown "?" node after import and the workflow cannot be published. n8n 2.42.4 imports it correctly. Either update n8n (recommended), or delete that node and add a new HTTP Request node with the same settings (POST, `http://host.docker.internal:8000/schedule`, Send Body on, JSON, body `{{ $json.body }}`).
