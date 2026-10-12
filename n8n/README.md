# n8n workflows (import these)

**This folder is the source of truth** for workflow JSON used in local setup and demos.

| File | Purpose |
|---|---|
| `n8n_streamlit_integration_v2.json` | Scheduling + conflict routing (Streamlit → Python API) |
| `Gmail_Timetable_Sender.json` | Optional email delivery of the timetable |
| `Auto_scheduler_n8n_Orchestrator.json` | Earlier orchestrator export (reference only) |
| `samples/` | Example webhook payloads for manual testing |
| `schemas/` | Request/response schemas for the Gmail webhook |
| `archive/` | Historical workflow exports (do not import for a new setup) |

Import only the two **active** workflows (`n8n_streamlit_integration_v2.json` and `Gmail_Timetable_Sender.json`). Older exports live under [`archive/`](archive/).

See `user-guide/START_SCHEDULER.md` for import and activation steps.
