# n8n workflows (import these)

**This folder is the source of truth** for workflow JSON used in local setup and demos.

| File | Purpose |
|---|---|
| `n8n_streamlit_integration_v2.json` | Scheduling + conflict routing (Streamlit → Python API) |
| `Gmail_Timetable_Sender.json` | Optional email delivery of the timetable |
| `Auto_scheduler_n8n_Orchestrator.json` | Earlier orchestrator export (reference) |
| `samples/` | Example webhook payloads for manual testing |
| `schemas/` | Request/response schemas for the Gmail webhook |

The top-level `workflows/` directory is **historical / archive**. Prefer importing from **`n8n/`** for a new machine setup.

See `user-guide/START_SCHEDULER.md` for import and activation steps.
