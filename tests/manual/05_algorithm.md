# 05 — Algorithm verification (placeholder)

**Owner:** Person B  
**Status:** Not implemented yet  
**Depends on:** `02_postgres_schema_seed.md` passed

## Intended checks (to be filled when DSATUR v1 exists)

- [ ] Reads normalized data from Postgres (or agreed adapter)
- [ ] Respects `course_allowed_timeslot`, co-enrolment, capacity, lab, instructor hours
- [ ] Output matches locked contract in `contracts/algo_output.example.json`
- [ ] CSC999 appears in `unplaced` with `ROOM_CAPACITY` (or equivalent)
- [ ] At least one of CSC351/CSC352 unplaced (lab / instructor / timeslot contention)
- [ ] At least one of MTH401/402/403 unplaced (clique + allowed slots)
- [ ] `violations_count` matches length of meaningful unplaced set

## How to run

_TBD — document CLI or n8n Code node entrypoint_

## Result

- Date run: __________
- Run by: __________
- Outcome: Pass / Fail / Not started
