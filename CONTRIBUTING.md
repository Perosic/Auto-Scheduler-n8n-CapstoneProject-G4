# Contributor & AI Collaboration Guide

## 1. Source of truth

Before changing code, read these files in this order:

1. `README.md` — project scope, architecture, roles and priority tiers.
2. `contracts/README.md` — locked interfaces between components.
3. `database/schema.sql` and `database/seed_data.sql` — current data model and fixtures.
4. The task/issue assigned to you.

Do not infer a new architecture from a prompt or from another contributor's implementation.

## 2. Component ownership

| Role | Owns | Must coordinate with |
|---|---|---|
| A | Database, seed data, Docker/Gotenberg, setup docs | B, C |
| B | Scheduling algorithm, graph/DSATUR logic, verifier | A, C |
| C | n8n orchestration, contract validation, timetable HTML | B, D |
| D | AI conflict explanation and Slack messaging | C |
| E | Streamlit CSV upload and calendar view | C |

Ownership means a contributor may implement inside their component. It does **not** mean they may change another component's interface without review.

## 3. Locked boundaries

Do not change these without team approval:

- Algorithm output JSON field names or nesting.
- `reason_code` values.
- PostgreSQL table/column names used by the algorithm or n8n.
- P0 architecture: PostgreSQL → scheduling algorithm → contract → n8n → HTML timetable.
- The P0/P1/P2 scope ladder.
- Intentional conflict fixtures once they are validated.

If a change is necessary, document the reason in the PR and update all affected consumers.

## 4. Branch and PR workflow

Never work directly on `main`.

Recommended branch names:

- `feat/db-...`
- `feat/alg-...`
- `feat/n8n-...`
- `feat/ai-...`
- `feat/ui-...`
- `fix/...`
- `docs/...`

Each PR should state:

1. What changed.
2. Which project requirement/task it satisfies.
3. Which files/interfaces it touches.
4. How another contributor can test it.
5. Whether any contract or schema changed.

Keep PRs focused. Do not combine unrelated refactors with feature work.

## 5. AI/LLM workflow

When using an LLM to write code:

1. Give it the relevant repository files or the exact excerpts it needs.
2. State the contributor role and the task.
3. State the locked contracts.
4. Tell it not to modify files outside the assigned component unless explicitly requested.
5. Ask it to explain assumptions before making schema/contract changes.
6. Review and test the generated code before committing.

An LLM must not invent database fields, API fields, workflow inputs, or conflict rules that are not present in the project specification.

## 6. Integration order

The intended integration sequence is:

1. Database schema + deterministic seed data.
2. Algorithm input queries/data adapter.
3. Algorithm + verifier.
4. Validate algorithm output against the locked contract.
5. n8n orchestration using the validated output.
6. P0 HTML timetable.
7. P1 AI/Slack, PDF/email and Streamlit.
8. P2 interactive Slack controls.

Do not build downstream components against an imaginary upstream interface. Use the contract/example fixtures while the upstream component is still under development.

## 7. Definition of done

A component is not "done" merely because the code exists.

It must have:

- documented input/output;
- a reproducible local test or verification step;
- no secrets committed;
- no unexplained contract changes;
- compatibility with the current schema and seed data;
- a PR that another contributor can review.

## 8. Local environment

Copy `.env.example` to `.env`. Never commit `.env`, API keys, credentials, tokens or private webhook URLs.

Use Docker Compose for the shared local stack. Do not replace PostgreSQL or n8n with another platform without team approval.

## 9. Conflict fixture rule

The seed data is a test fixture, not production data. Its failure cases must be **provably unplaceable under the implemented constraint model**. If a fixture is described as impossible but the current schema/constraints allow a valid schedule, fix the fixture or the constraint model before treating the integration as complete.

## 10. Integration checklist

Before merging:

- [ ] I worked on a feature/fix branch.
- [ ] I read the README and relevant contract.
- [ ] I did not silently change an interface.
- [ ] I tested my component locally.
- [ ] I tested the affected integration boundary.
- [ ] I did not commit secrets.
- [ ] I documented any intentional contract/schema change.
- [ ] The PR is small enough to review.
