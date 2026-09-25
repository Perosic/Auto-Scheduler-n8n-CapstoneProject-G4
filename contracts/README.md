# Data Contracts (Locked)

These contracts are the project's most important collaboration boundary.
**Do not change field names, nesting, or reason_code values without team approval.**

## Algorithm Output (Person B → Person C / n8n)

See `algo_output.example.json`.

```json
{
  "placed": [
    { "course_id": number, "section_id": number, "room_id": number, "timeslot": string, "instructor_id": number }
  ],
  "unplaced": [
    { "course_id": number, "reason_code": string, "detail": string }
  ],
  "violations_count": number
}
```

### reason_code enum (fixed)
- `ROOM_CAPACITY`
- `ROOM_EQUIPMENT`
- `CO_ENROLMENT`
- `INSTRUCTOR_CLASH`
- `OTHER`

## AI Context (Person C → Person D)
Only the `unplaced` array + room open-slot inventory is passed to the AI Agent.

## Verifier
Independently re-checks the final `placed` array for room / instructor / timeslot clashes.
Outputs: `{ "pass": boolean, "clashes": [...] }`
