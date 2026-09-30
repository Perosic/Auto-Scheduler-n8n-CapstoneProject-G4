# 04 — Gotenberg verification

**Owner:** Data Engineer / Output track (Person A + C)  
**Depends on:** `01_docker_stack.md`  
**Goal:** Gotenberg container is up and responds to a simple health/convert request.

## Steps

```bash
docker compose ps gotenberg
```

Browser or curl:

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/health
```

(Endpoint may vary by Gotenberg version; `/health` or root is typical.)

Optional smoke convert (HTML → PDF) when wiring n8n later — document the exact curl here when the team standardizes it.

## Pass criteria

- [ ] Container `scheduler_gotenberg` is **Up**
- [ ] Health endpoint returns success (2xx) *or* team documents the chosen smoke test

## Notes

PDF export via n8n is **P1**. This check only proves the service is available for later wiring.

## Result

- Date run: __________
- Run by: __________
- Outcome: Pass / Fail
- Notes: __________
