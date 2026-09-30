# 06 — n8n workflow verification (placeholder)

**Owner:** Person C  
**Status:** Not implemented yet  
**Depends on:** algorithm contract + Postgres

## Intended checks

- [ ] Workflow imports without error
- [ ] DB node reads required tables
- [ ] Code / algorithm step emits locked JSON shape
- [ ] IF branch routes on `unplaced` / `violations_count`
- [ ] P0 HTML timetable renders for `placed[]`
- [ ] Conflict path reachable with seed fixtures

## Port note

If `scheduler_n8n` cannot bind 5678, free the port or change `N8N_PORT` in `.env` and document the new URL.

## Result

- Date run: __________
- Run by: __________
- Outcome: Pass / Fail / Not started
