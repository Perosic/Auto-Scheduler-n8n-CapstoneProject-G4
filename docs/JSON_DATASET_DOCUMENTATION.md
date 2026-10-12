# University Course Timetable Auto-Scheduler
## JSON Test Dataset Documentation

**Version:** 1.0  
**Purpose:** Test dataset for the Adjacency List, DSATUR scheduling algorithm, and timetable verification logic in n8n.

---

## 1. Overview

This dataset represents a small university timetable scenario.

It contains:

- 10 courses
- 20 students
- 6 lecturers
- 4 rooms
- 8 time slots
- Expected course adjacency
- Hard scheduling constraints
- DSATUR configuration

The dataset is intentionally small so that the results can be manually checked while developing the n8n workflow.

---

## 2. Recommended Project Structure

```text
Auto-Scheduler-n8n-CapstoneProject-G4/
│
├── data/
│   └── timetable_dataset.json
│
├── docs/
│   └── JSON_DATASET_DOCUMENTATION.md
│
├── README.md
└── .gitignore
```

---

# 3. JSON Dataset

Save the following content as:

`data/timetable_dataset.json`

(See repository `data/timetable_dataset.json` for the checked-in dataset used with the PostgreSQL pipeline. The embedded historical example below remains useful for isolated adjacency / DSATUR experiments.)

For the full historical JSON example body and field descriptions, see the version of this document previously at the repository root; the structure and testing strategy sections below still apply.

---

# 4. What Each Dataset Section Does

### Courses

Contains the courses that need to be scheduled.

The scheduler uses:

- `course_id`
- `lecturer_id`
- `expected_students`
- `required_equipment`

### Students

This is the primary input for the **Adjacency Builder**.

If two students take the same course, those courses become neighbours in the conflict graph.

### Lecturers

Provides lecturer availability.

This is mainly used by the **Verifier** and later by the scheduling engine.

### Rooms

Provides room capacity, equipment, and identity for verifier checks.

### Time Slots

Available scheduling periods; DSATUR uses these as colours.

### Expected Adjacency

Expected output from adjacency-building logic for comparison.

### Hard Constraints

Rules that must never be violated.

### DSATUR Configuration

Defines how colours map to time slots.

---

# 5. Testing Strategy

Do not build the entire scheduler at once.

Test in this order:

```text
JSON Dataset
     ↓
Read Dataset
     ↓
Build Adjacency
     ↓
Check Adjacency
     ↓
Run DSATUR
     ↓
Generate Time Assignments
     ↓
Assign Rooms
     ↓
Run Verifier
     ↓
Valid?
  ↙     ↘
YES     NO
 ↓       ↓
Output  Exception
```

First milestone: **Can the n8n Code Node generate the expected adjacency list from the student enrolment data?**

---

# 6. Important Note About GitHub

Do **not** put passwords, API keys, database credentials, `.env` files, or other secrets into this repository.

---

# 7. Recommended GitHub Repository

Suggested description:

> An n8n-based university course timetable automation project using conflict graphs, DSATUR scheduling, constraint verification, and AI-assisted exception handling.
