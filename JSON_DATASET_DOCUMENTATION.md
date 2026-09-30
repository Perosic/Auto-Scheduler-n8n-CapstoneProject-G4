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
university-timetable-auto-scheduler/
│
├── data/
│   └── timetable_test_dataset.json
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

`data/timetable_test_dataset.json`

```json
{
  "dataset_name": "University Course Timetable Auto-Scheduler",
  "version": "1.0",
  "purpose": "Test dataset for Adjacency List, DSATUR scheduling, and timetable verification",

  "courses": [
    {
      "course_id": "C01",
      "course_name": "CSC101 - Introduction to Computing",
      "lecturer_id": "L01",
      "expected_students": 35,
      "required_equipment": ["Projector"]
    },
    {
      "course_id": "C02",
      "course_name": "MTH101 - Mathematics I",
      "lecturer_id": "L02",
      "expected_students": 40,
      "required_equipment": []
    },
    {
      "course_id": "C03",
      "course_name": "PHY101 - Physics I",
      "lecturer_id": "L03",
      "expected_students": 30,
      "required_equipment": ["Projector"]
    },
    {
      "course_id": "C04",
      "course_name": "STA101 - Statistics I",
      "lecturer_id": "L04",
      "expected_students": 35,
      "required_equipment": ["Projector"]
    },
    {
      "course_id": "C05",
      "course_name": "CSC102 - Programming Fundamentals",
      "lecturer_id": "L01",
      "expected_students": 30,
      "required_equipment": ["Computer Lab"]
    },
    {
      "course_id": "C06",
      "course_name": "MTH102 - Mathematics II",
      "lecturer_id": "L02",
      "expected_students": 30,
      "required_equipment": []
    },
    {
      "course_id": "C07",
      "course_name": "PHY102 - Physics II",
      "lecturer_id": "L03",
      "expected_students": 25,
      "required_equipment": ["Projector"]
    },
    {
      "course_id": "C08",
      "course_name": "ENG101 - Communication Skills",
      "lecturer_id": "L05",
      "expected_students": 45,
      "required_equipment": ["Projector"]
    },
    {
      "course_id": "C09",
      "course_name": "BUS101 - Introduction to Business",
      "lecturer_id": "L06",
      "expected_students": 40,
      "required_equipment": []
    },
    {
      "course_id": "C10",
      "course_name": "CSC201 - Data Structures",
      "lecturer_id": "L01",
      "expected_students": 25,
      "required_equipment": ["Computer Lab"]
    }
  ],

  "students": [
    {"student_id": "S01", "courses": ["C01", "C02", "C03"]},
    {"student_id": "S02", "courses": ["C01", "C02", "C04"]},
    {"student_id": "S03", "courses": ["C01", "C05", "C06"]},
    {"student_id": "S04", "courses": ["C02", "C03", "C07"]},
    {"student_id": "S05", "courses": ["C02", "C04", "C08"]},
    {"student_id": "S06", "courses": ["C03", "C07", "C09"]},
    {"student_id": "S07", "courses": ["C04", "C08", "C09"]},
    {"student_id": "S08", "courses": ["C05", "C06", "C10"]},
    {"student_id": "S09", "courses": ["C01", "C05", "C10"]},
    {"student_id": "S10", "courses": ["C06", "C08", "C09"]},
    {"student_id": "S11", "courses": ["C01", "C02", "C03"]},
    {"student_id": "S12", "courses": ["C02", "C04", "C08"]},
    {"student_id": "S13", "courses": ["C03", "C07", "C09"]},
    {"student_id": "S14", "courses": ["C05", "C06", "C10"]},
    {"student_id": "S15", "courses": ["C01", "C05", "C10"]},
    {"student_id": "S16", "courses": ["C06", "C08", "C09"]},
    {"student_id": "S17", "courses": ["C01", "C02", "C04"]},
    {"student_id": "S18", "courses": ["C02", "C03", "C07"]},
    {"student_id": "S19", "courses": ["C04", "C08", "C09"]},
    {"student_id": "S20", "courses": ["C05", "C06", "C10"]}
  ],

  "lecturers": [
    {
      "lecturer_id": "L01",
      "lecturer_name": "Dr. Ahmed",
      "available_slots": ["T01", "T02", "T03", "T05", "T06", "T07"]
    },
    {
      "lecturer_id": "L02",
      "lecturer_name": "Dr. Fatima",
      "available_slots": ["T01", "T02", "T04", "T05", "T06", "T08"]
    },
    {
      "lecturer_id": "L03",
      "lecturer_name": "Dr. Yusuf",
      "available_slots": ["T02", "T03", "T04", "T06", "T07", "T08"]
    },
    {
      "lecturer_id": "L04",
      "lecturer_name": "Dr. Aisha",
      "available_slots": ["T01", "T03", "T04", "T05", "T07", "T08"]
    },
    {
      "lecturer_id": "L05",
      "lecturer_name": "Dr. Ibrahim",
      "available_slots": ["T01", "T02", "T03", "T04", "T05", "T06", "T07", "T08"]
    },
    {
      "lecturer_id": "L06",
      "lecturer_name": "Dr. Maryam",
      "available_slots": ["T02", "T03", "T05", "T06", "T07", "T08"]
    }
  ],

  "rooms": [
    {
      "room_id": "R01",
      "room_name": "Lecture Hall A",
      "capacity": 50,
      "equipment": ["Projector"]
    },
    {
      "room_id": "R02",
      "room_name": "Lecture Hall B",
      "capacity": 40,
      "equipment": ["Projector"]
    },
    {
      "room_id": "R03",
      "room_name": "Lecture Room C",
      "capacity": 30,
      "equipment": []
    },
    {
      "room_id": "R04",
      "room_name": "Computer Lab",
      "capacity": 35,
      "equipment": ["Computer Lab", "Projector"]
    }
  ],

  "time_slots": [
    {"slot_id": "T01", "day": "Monday", "start_time": "08:00", "end_time": "10:00"},
    {"slot_id": "T02", "day": "Monday", "start_time": "10:00", "end_time": "12:00"},
    {"slot_id": "T03", "day": "Monday", "start_time": "13:00", "end_time": "15:00"},
    {"slot_id": "T04", "day": "Monday", "start_time": "15:00", "end_time": "17:00"},
    {"slot_id": "T05", "day": "Tuesday", "start_time": "08:00", "end_time": "10:00"},
    {"slot_id": "T06", "day": "Tuesday", "start_time": "10:00", "end_time": "12:00"},
    {"slot_id": "T07", "day": "Tuesday", "start_time": "13:00", "end_time": "15:00"},
    {"slot_id": "T08", "day": "Tuesday", "start_time": "15:00", "end_time": "17:00"}
  ],

  "expected_adjacency": {
    "C01": ["C02", "C03", "C04", "C05", "C06", "C10"],
    "C02": ["C01", "C03", "C04", "C05", "C06", "C07", "C08"],
    "C03": ["C01", "C02", "C04", "C07", "C09"],
    "C04": ["C01", "C02", "C03", "C08", "C09"],
    "C05": ["C01", "C06", "C10"],
    "C06": ["C01", "C02", "C05", "C08", "C09", "C10"],
    "C07": ["C02", "C03", "C09"],
    "C08": ["C02", "C04", "C06", "C09"],
    "C09": ["C03", "C04", "C06", "C07", "C08"],
    "C10": ["C01", "C05", "C06"]
  },

  "hard_constraints": [
    "Courses sharing at least one student cannot have the same time slot",
    "A lecturer must be available during the assigned time slot",
    "A lecturer cannot teach two courses at the same time",
    "A room cannot host two courses at the same time",
    "Room capacity must be greater than or equal to expected students",
    "The room must contain all equipment required by the course"
  ],

  "dsatur_configuration": {
    "algorithm": "DSATUR",
    "color_represents": "time_slot",
    "color_mapping": {
      "1": "T01",
      "2": "T02",
      "3": "T03",
      "4": "T04",
      "5": "T05",
      "6": "T06",
      "7": "T07",
      "8": "T08"
    }
  }
}
```

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

For example:

```text
S01 → C01, C02, C03
```

creates:

```text
C01 ↔ C02
C01 ↔ C03
C02 ↔ C03
```

### Lecturers

Provides lecturer availability.

This is mainly used by the **Verifier** and later by the scheduling engine.

### Rooms

Provides:

- room capacity
- room equipment
- room identity

This allows the verifier to detect invalid room assignments.

### Time Slots

These are the available scheduling periods.

DSATUR uses these as the available "colours".

### Expected Adjacency

This is the expected output from the adjacency-building logic.

It is included so you can compare your n8n Code Node output against a known result.

### Hard Constraints

These are rules that must never be violated.

### DSATUR Configuration

Defines how colours map to time slots.

---

# 5. Testing Strategy

Do not build the entire scheduler at once.

Test it in this order:

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

The first milestone is simply:

> **Can the n8n Code Node generate the expected adjacency list from the student enrolment data?**

Once that works, move to DSATUR.

---

# 6. Important Note About GitHub

Do **not** put passwords, API keys, database credentials, `.env` files, or other secrets into this repository.

For this test dataset, the JSON contains only fictional/sample data, so it is suitable for a public portfolio repository.

---

# 7. Recommended GitHub Repository

Suggested repository name:

`university-timetable-auto-scheduler`

Suggested description:

> An n8n-based university course timetable automation project using conflict graphs, DSATUR scheduling, constraint verification, and AI-assisted exception handling.

