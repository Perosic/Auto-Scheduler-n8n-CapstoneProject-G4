# Gmail Integration via n8n: Work Summary

**Date:** 5 October 2026
**Branch:** `feat/p1-gmail-n8n`
**Pull request:** #13 (into `main`)

## Purpose

This summary records the work completed on the Gmail integration task (P1): what was built, how it was set up, how it was tested and what is left for the team.

## Status at a glance

| Area | Status | Notes |
|---|---|---|
| n8n Gmail workflow | Done | `n8n/Gmail_Timetable_Sender.json` |
| Webhook accepts timetable data | Done | `POST /webhook/send-schedule` |
| Recipient set per request | Done | Comes from the `recipient` field |
| Email contains the timetable | Done | Table grouped by day, sorted by time |
| Multiple entries handled | Done | Tested with 3 entries and with 21 entries |
| Success response | Done | HTTP 200, `success: true` |
| Useful error responses | Done | HTTP 400 for bad requests, HTTP 502 if Gmail fails |
| Tested without Streamlit | Done | Tested with sample JSON from PowerShell |
| No frontend/algorithm changes | Done | Only new files under `n8n/` and `docs/` |
| No secrets in the repo | Done | Gmail is connected through an n8n credential |
| Webhook and formats documented | Done | `docs/integrations/GMAIL_N8N_INTEGRATION.md` |
| PR opened against main | Done | PR #13, reviewer requested |

## 1. What was built

An n8n workflow that receives a generated timetable, checks it, turns it into a readable email and sends it through Gmail.

```text
Webhook: Send Schedule
  → Validate & Format Email
  → Request Valid?
       false → Respond: Invalid Request (400)
       true  → Gmail: Send Timetable
                  success → Respond: Sent (200)
                  error   → Respond: Gmail Failed (502)
```

**Validate & Format Email** (Code node):

- checks that `recipient` is a valid email address (several addresses separated by commas are allowed)
- checks that `schedule` is a non-empty list and that every entry has `course`, `day`, `time` and `room`
- sorts the classes Monday to Sunday, then by time
- builds the HTML email (table grouped by day) and a plain-text version that follows the task example
- escapes all values so course titles with symbols display correctly

**Gmail: Send Timetable** sends the HTML email with the sender name "Group 4 Auto-Scheduler" and the n8n attribution footer turned off. It retries up to 3 times, 5 seconds apart, as taught in class. If Gmail still fails, the error is routed to its own response instead of stopping the workflow.

The email shows Time, Course, Title, Lecturer and Room. "Lecturer" is the scheduler's field name for what the database calls an instructor; the column is left out if a request has no lecturers.

## 2. Webhook contract

**Endpoint:** `POST http://localhost:5678/webhook/send-schedule`

**Request:**

```json
{
  "recipient": "student@example.com",
  "subject": "Your Course Timetable",
  "schedule": [
    { "course": "CSC101", "title": "Computer Science", "day": "Monday", "time": "09:00 - 11:00", "room": "CR101" }
  ]
}
```

`subject` is optional. Extra fields are ignored, so the scheduler's `placed` list can be sent as `schedule` without reshaping. The scheduler's short days and times with seconds (`Mon`, `09:00:00 - 10:00:00`) are shown in the email as `Monday` and `09:00 - 10:00`.

**Responses:**

| HTTP | When | Body |
|---|---|---|
| 200 | Email sent | `success: true`, `message`, `recipient`, `entries_sent`, `gmail_message_id` |
| 400 | Request invalid, nothing sent | `success: false`, `message`, `errors` (list) |
| 502 | Gmail could not send | `success: false`, `message`, `error`, `recipient` |

Formal schemas are in `n8n/schemas/`.

## 3. Setup completed

1. Created a dedicated test Gmail account to act as the sender, so no personal account is connected to n8n.
2. Created a Google Cloud project, enabled the Gmail API, set up the OAuth consent screen (External, Testing) and added the test account as a test user.
3. Created a Web application OAuth client with the redirect URI `http://localhost:5678/rest/oauth2-credential/callback`.
4. Imported the workflow into n8n 2.31.4, created a Gmail OAuth2 credential, signed in with the test account and published the workflow.

The Client ID and Client Secret are stored privately and are not in the repository.

## 4. Testing performed

Environment: Windows, n8n 2.31.4 in Docker, tested on 5 October 2026.

| Test | How | Result |
|---|---|---|
| Valid request | `send_schedule_valid.json` sent with `curl.exe` | HTTP 200, `success: true`, `entries_sent: 3`. Email received with Monday (2 classes) and Tuesday (1 class) in time order |
| Invalid request | `send_schedule_invalid.json` (bad email, missing room) | HTTP 400 with both errors listed. No email sent |
| n8n execution record | Executions tab | Run #29 followed the Gmail → Sent path. Run #30 followed the Invalid Request path |
| Gmail failure path | Workflow run without a Gmail credential (pre-check) | HTTP 502 with the Gmail error message |
| Project seed data | Real scheduler output from `database/seed_data.sql` (21 placed classes) sent with `curl.exe` | HTTP 200, `entries_sent: 21`. Email received with Monday (16 classes) and Tuesday (5 classes), times shown as 09:00 - 10:00 |
| Lecturer column | Scheduler output with lecturers; payload without lecturers | Lecturer column shown with the right names; left out when no lecturers are sent |
| Gmail retries | Workflow with no Gmail credential | Retried 3 times, then HTTP 502 with the Gmail error |
| Import check | Fresh import on n8n 2.31.4 | All 7 nodes recognised, no unknown nodes |

Screenshots of the email, the PowerShell responses and the n8n executions are attached to PR #13.

## 5. Decisions and things to know

- **Separate test Gmail account.** Google's permission screen for the n8n Gmail node allows reading and sending mail, so a dedicated account keeps personal email out of the project.
- **Sign-in expires about every 7 days.** While the Google app is in Testing mode, the Gmail sign-in in n8n has to be renewed weekly. Before any demo, open the Gmail credential in n8n and click Sign in with Google again.
- **Test URL vs live URL.** `/webhook-test/send-schedule` only works while Execute workflow is listening in the editor. `/webhook/send-schedule` works once the workflow is published, and its runs show under the Executions tab instead of on the canvas.
- **PowerShell.** Use `curl.exe` (not `curl`) and send the JSON as a file with `--data-binary "@path\to\file.json"`. Typing JSON inline in Windows PowerShell breaks because the quotes get stripped.
- **No webhook authentication yet.** This is fine on localhost. If the webhook is ever exposed beyond the laptop, Header Auth should be added with the secret kept in `.env` and an n8n credential.

## 6. Files added

- `n8n/Gmail_Timetable_Sender.json`
- `n8n/samples/send_schedule_valid.json`
- `n8n/samples/send_schedule_seed_data.json`
- `n8n/samples/send_schedule_invalid.json`
- `n8n/schemas/send_schedule.request.schema.json`
- `n8n/schemas/send_schedule.response.schema.json`
- `docs/integrations/GMAIL_N8N_INTEGRATION.md`

## 7. How to reproduce

Follow sections 6 and 7 of `docs/integrations/GMAIL_N8N_INTEGRATION.md`. Each person connects their own Gmail credential in n8n; credentials are never shared.

## 8. Next steps for the team

1. **Second tester:** run the guide on another laptop, including a live Gmail failure test (revoke the app at myaccount.google.com/permissions, send the valid sample, expect HTTP 502, then reconnect). Post results on PR #13.
2. **Review and merge:** PR #13 to be reviewed and merged into `main`.
3. **Streamlit connection:** add an "Email this timetable" option in the Streamlit app that calls the webhook (snippet in section 8 of the integration doc). This needs its own branch and PR because it changes `frontend/`.
4. **Demo backup:** screenshots of the email flow ready in case the live demo cannot run.
5. **Optional:** PDF attachment through Gotenberg, only if the team decides it is in scope.
