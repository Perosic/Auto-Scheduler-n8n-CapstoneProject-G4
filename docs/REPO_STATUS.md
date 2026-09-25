# Repository Sync & Integration Status

_Last checked: 2026-09-25_

## Current state

The repository is a **Day-1 scaffold**, not yet a complete implementation of the P0 scheduler.

### Present

- PostgreSQL schema and seed data.
- Docker Compose for PostgreSQL, pgAdmin, n8n and Gotenberg.
- Locked algorithm → n8n output contract.
- Streamlit P1 placeholder.
- n8n workflow file placeholder.
- Environment example and secret-oriented .gitignore.

### Not yet implemented

- Scheduling algorithm / DSATUR implementation.
- Standalone verifier.
- Real n8n nodes and orchestration.
- P0 timetable generation.
- Streamlit CSV processing/calendar.
- AI conflict workflow.
- Slack integration.
- PDF/email integration.

## Important validation findings

The current seed-data comments and README claim **25 courses**, but the SQL currently creates **28 courses**: 22 normal courses plus 6 courses used for the described failure scenarios.

The current data also does not, by itself, guarantee that all described failure scenarios are unplaceable:

- CSC999 is genuinely impossible because its required capacity is 150 while the largest room is 80.
- CSC351 and CSC352 share an instructor and compete for LAB1, but they can still be placed in different timeslots unless another constraint makes them simultaneous.
- MTH401/MTH402/MTH403 are a co-enrolment clique, but the current schema provides 25 timeslots and no per-course allowed-timeslot restriction, so the clique can be assigned to three different timeslots.

Therefore the failure fixtures must be corrected or the constraint model must explicitly represent the intended restrictions before the project can claim that the three conflict paths are proven.

## Integration contract

The P0 pipeline remains:

PostgreSQL → scheduling algorithm → locked JSON contract → n8n → HTML timetable.

Downstream contributors should use `contracts/algo_output.example.json` as the temporary upstream fixture until the real algorithm exists.

## Recommended next implementation order

1. Validate/finalize the database fixtures and constraint model.
2. Build the algorithm input adapter.
3. Implement DSATUR/greedy scheduling.
4. Implement the independent verifier.
5. Validate algorithm output against the contract.
6. Build the n8n DB → algorithm → validation → HTML path.
7. Add P1 features only after P0 works end-to-end.
