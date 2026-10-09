# Data Contracts (Locked)

These contracts are the project's most important collaboration boundary.
**Do not change field names, nesting, or reason_code values without team approval.**

## Algorithm Output (Person B → Person C / n8n / Streamlit)

See `algo_output.example.json` for a full example of the **runtime** shape returned by `POST /schedule`.

### Required fields used by n8n routing

| Field | Type | Notes |
|---|---|---|
| `placed` | array | Successfully assigned classes |
| `unplaced` | array | Could not be placed; each has `reason_code` + `detail` |
| `violations_count` | number | Residual hard-constraint violations on the *placed* set (should be 0) |
| `verification_errors` | array | Human-readable verifier messages |

### Rich `placed[]` fields (UI / email)

The scheduler also returns display fields used by Streamlit and the Gmail workflow:

`course`, `title`, `lecturer`, `day`, `time`, `timeslot_label`, `room`, `room_capacity`, plus internal ids (`course_id`, `section_id`, `room_id`, `instructor_id`, `timeslot_id`).

### `unplaced[]` shape

```json
{
  "course_id": 23,
  "code": "CSC999",
  "reason_code": "ROOM_CAPACITY",
  "detail": "Expected enrolment 150 exceeds largest available room capacity 80"
}
```

### reason_code enum (fixed)

- `ROOM_CAPACITY`
- `ROOM_EQUIPMENT`
- `CO_ENROLMENT`
- `INSTRUCTOR_CLASH`
- `OTHER`
- `COURSE_NOT_FOUND` (CSV code not in the scheduling database; does not enter the P0 engine)

## AI Context (Person C → Person D)

Only the `unplaced` array (+ optional room open-slot inventory) is passed to the AI Agent.

## Verifier

Independently re-checks the final `placed` array for room / instructor / timeslot clashes.
Contributes to `violations_count` and `verification_errors`.
