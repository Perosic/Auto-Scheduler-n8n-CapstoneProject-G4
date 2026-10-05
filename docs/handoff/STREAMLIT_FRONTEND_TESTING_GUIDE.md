# Streamlit Frontend — Testing Guide

## Purpose

This guide explains how another team member can run and test the current P1 Streamlit frontend without changing the scheduler or n8n workflow.

The current frontend flow is:

1. Upload a course CSV.
2. Detect/map supported CSV columns.
3. Validate and normalize course data.
4. Select courses to schedule.
5. Override enrollment values when needed.
6. Generate a timetable using the existing scheduler.
7. Review placed and unplaced courses.
8. Review independent verification results.
9. Export the generated timetable as CSV.

The frontend calls the existing scheduler through `algorithm/frontend_scheduler.py`; it does not replace the P0 scheduling algorithm.

---

## 1. Prerequisites

Use the project repository:

`Auto-Scheduler-n8n-CapstoneProject-G4`

Recommended environment:

- Windows PowerShell
- Python virtual environment already created as `.venv`
- PostgreSQL scheduling database running and seeded
- Project dependencies installed
- Git checkout on the P1 frontend branch when testing the current work

The P0 repository status confirms that the scheduling pipeline depends on PostgreSQL and the Python scheduling/verification components. The seeded database also contains deliberate failure fixtures, so an unplaced course is not automatically a frontend defect.

---

## 2. Start the Python environment

Open PowerShell in the repository root:

```powershell
cd C:\Users\hp\Auto-Scheduler-n8n-CapstoneProject-G4
```

Activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks the activation script for the current session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

You should see `(.venv)` at the beginning of the PowerShell prompt.

---

## 3. Start Streamlit

From the repository root:

```powershell
streamlit run frontend/app.py
```

The app should normally be available at:

`http://localhost:8506`

Open that address in a browser.

Keep the Streamlit terminal running while testing.

---

## 4. Recommended first test — standard CSV

Use the checked-in fixture:

`frontend/test_courses.csv`

It uses the standard column names:

```text
course_id,course_code,course_name,instructor,students
```

The fixture contains eight valid course rows, including CSC101, CSC102, CSC201, MTH101, MTH201, PHY101, STA201, and GST101.

### Steps

1. Open the Streamlit app.
2. In **1. Upload Course CSV**, upload `frontend/test_courses.csv`.
3. Confirm that the upload succeeds.
4. Review the CSV preview.
5. Confirm that the column mapping identifies all required fields.
6. Continue to course selection.
7. Select one or more courses.
8. Check the enrollment values.
9. Optionally change an enrollment value.
10. Click **Generate Schedule**.
11. Wait for timetable generation to finish.
12. Review the schedule result metrics.
13. Review the timetable table.
14. Review any unplaced courses.
15. Confirm the **Verification** section.
16. If courses were placed, test the timetable CSV download.

---

## 5. Test flexible CSV column names

Use:

`frontend/test_courses_alt.csv`

This fixture intentionally uses alternate headers:

```text
ID,Course Code,Title,Lecturer,Enrollment
```

The frontend is expected to recognize these aliases and map them to its internal fields.

### Pass condition

The file should upload and the column-mapping section should correctly identify:

| Internal field | Expected CSV column |
|---|---|
| course_id | ID |
| course_code | Course Code |
| course_name | Title |
| instructor | Lecturer |
| students | Enrollment |

The scheduler should then be able to process the selected valid courses.

---

## 6. Test the full scheduler fixture

Use:

`frontend/test_scheduler_courses.csv`

This is the larger scheduler test fixture with 11 courses:

- CSC101
- CSC201
- CSC301
- CSC302
- CSC401
- MTH101
- MTH201
- MTH301
- PHY101
- PHY201
- ENG101

### What to check

After generation, check all four result metrics:

- **Requested** — number of selected courses.
- **Placed** — courses successfully assigned a timeslot and room.
- **Unplaced** — courses that could not be assigned.
- **Verification Issues** — independent verification failures.

An unplaced count can be greater than zero when the scheduler cannot find a valid resource combination. This is a scheduler outcome, not necessarily a frontend failure.

A particularly important pass condition is that **Verification Issues can remain at zero even when some courses are unplaced**. In that situation the verifier is confirming that the courses that were placed are valid.

---

## 7. Test enrollment overrides

After selecting courses, change one or more enrollment values before generating the schedule.

For example:

```text
CSC101 → 40
CSC201 → 50
```

Click **Generate Schedule** again.

### Pass condition

The scheduler accepts the updated enrollment values instead of always using the CSV defaults. Room assignment should reflect the updated capacity requirement where applicable.

---

## 8. Test invalid course handling

An invalid-course fixture is also available:

`invalid_course_test.csv`

It intentionally contains `INVALID999`.

This is an exception-handling test, not a successful scheduling fixture.

### Expected behavior

When `INVALID999` is selected, the frontend should clearly report that the course is not available in the scheduling database. It should not silently create a timetable entry for that course.

The current scheduler intentionally exposes missing database courses as an explicit result/error so that users can identify bad CSV course codes.

---

## 9. Test the results sections

After generating a schedule, verify the following UI areas.

### Schedule Results

Confirm the requested, placed, unplaced, and verification counts are displayed.

### Timetable

For placed courses, confirm that the table can display fields such as:

- course code
- title
- lecturer
- day
- time
- room
- room capacity
- timeslot label

### Unplaced Courses

If any course cannot be scheduled, confirm that the UI identifies it and provides the scheduler's reason/detail where available.

### Verification

Confirm that independent verification status is visible. A green verification result means the verifier found no errors in the placed schedule.

### Export

When there are placed courses, click **Download Timetable CSV** and confirm that a CSV file is downloaded.

---

## 10. What counts as a frontend failure?

Report the issue if any of these occur:

- Streamlit does not start.
- The CSV uploader rejects a valid `.csv` file unexpectedly.
- Valid supported column names are not detected.
- Valid course rows disappear or are corrupted during normalization.
- Course selection cannot be performed.
- Enrollment overrides are ignored or cause an unexpected exception.
- A valid scheduling request crashes the Streamlit app.
- A timetable is generated but the displayed fields are incorrect or missing.
- Export fails when placed courses exist.
- The frontend reports verification errors that contradict the scheduler/verifier output.

Do **not** report an unplaced course by itself as a frontend bug. The scheduler can legitimately leave courses unplaced when constraints/resources prevent placement.

---

## 11. What should not be changed during this test

Do not modify these files just to make a test pass:

- `algorithm/dsatur.py`
- `algorithm/room_assigner.py`
- `algorithm/graph.py`
- `algorithm/verifier.py`
- `algorithm/db_loader.py`
- PostgreSQL seed data
- n8n workflows

If the test exposes a real issue in one of those components, record the exact error and test input instead of changing the component during frontend testing.

---

## 12. Quick smoke-test checklist

Use this checklist for a fast review:

- [ ] Virtual environment activated.
- [ ] PostgreSQL database available.
- [ ] `streamlit run frontend/app.py` starts successfully.
- [ ] App opens on `localhost:8506`.
- [ ] `frontend/test_courses.csv` uploads.
- [ ] Required columns are detected.
- [ ] Courses can be selected.
- [ ] Enrollment values can be changed.
- [ ] Schedule generation completes.
- [ ] Timetable appears when courses are placed.
- [ ] Unplaced courses are reported clearly when applicable.
- [ ] Verification status is displayed.
- [ ] Timetable CSV downloads successfully.
- [ ] `frontend/test_courses_alt.csv` tests column aliases successfully.
- [ ] Invalid-course handling is clear for `INVALID999`.

---

## 13. Reporting a failed test

When reporting a problem, include:

1. The CSV filename used.
2. The selected course codes.
3. Any enrollment overrides.
4. The exact error message.
5. The Requested / Placed / Unplaced / Verification Issues counts.
6. A screenshot if the problem is visual.
7. The terminal traceback if one appears.
8. The Git branch/commit being tested.

Do not paste credentials, database passwords, Gmail credentials, API keys, or webhook secrets into an issue or handoff message.

---

## Current handoff state

The P1 Streamlit frontend is being developed on:

`feat/p1-frontend-ux`

The frontend currently exercises the existing scheduler rather than replacing the P0 scheduling pipeline. The n8n/Gmail integration is a separate workstream and should remain isolated from frontend changes until the webhook contract is ready.

For the current collaboration boundary, the Gmail/n8n task must not modify `frontend/app.py` or the scheduler algorithm files. The integration should consume the timetable through the agreed webhook contract after the frontend work is ready for connection.
