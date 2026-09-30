# Tests & Verification

This folder holds **verification procedures** for each project component.

It is **not** a full automated test suite yet. Most Day-1 checks are manual runbooks that anyone can execute after `docker compose up`. Automated unit/integration tests will be added later (algorithm, verifier, n8n).

## Purpose

- Prove each layer works before the next role builds on it
- Give every contributor the same checklist (no tribal knowledge)
- Capture evidence that deliberate conflict fixtures actually constrain the schedule
- Support the Definition of Done in `CONTRIBUTING.md`

## Folder layout

```
tests/
├── README.md                 ← this file
├── manual/                   ← step-by-step verification (Markdown)
│   ├── 01_docker_stack.md
│   ├── 02_postgres_schema_seed.md
│   ├── 03_pgadmin.md
│   ├── 04_gotenberg.md
│   ├── 05_algorithm.md       (placeholder – Person B)
│   ├── 06_n8n_workflow.md    (placeholder – Person C)
│   └── 07_verifier.md        (placeholder – Person B)
└── fixtures/                 ← optional expected outputs / sample JSON
    └── README.md
```

## File type conventions

| Type | Use for |
|------|--------|
| **`.md`** | Manual checklists, runbooks, expected results (preferred for humans + LLMs) |
| **`.json`** | Expected algorithm output samples, contract fixtures, API response examples |
| **`.sql`** | One-off verification queries (optional) |
| **`.pdf`** | Work summaries / handoff reports only — put those under `docs/handoffs/`, not here |

**Rule:** Put *how to verify* in `tests/`. Put *what we did and why* in `docs/handoffs/`.

## How to run Day-1 verification

```bash
# From repo root
docker compose down -v    # clean slate (optional)
docker compose up -d
# wait ~20s

# Then follow the numbered files in tests/manual/
```

## Status legend (use in each checklist)

- `[ ]` not run
- `[x]` passed
- `[!]` failed / blocked — note the error
