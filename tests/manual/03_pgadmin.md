# 03 — pgAdmin verification

**Owner:** Data Engineer  
**Depends on:** `01_docker_stack.md`  
**Goal:** pgAdmin UI is reachable and can connect to PostgreSQL.

## Steps

1. Confirm container is up:
   ```bash
   docker compose ps pgadmin
   # or: docker ps --filter name=scheduler_pgadmin
   ```

2. Open browser: http://localhost:5050

3. Log in with values from `docker-compose.yml`:
   - Email: `admin@example.com`
   - Password: `admin`

4. Register a server (if not auto-discovered):
   - Host: `postgres` (Docker network name) **or** `host.docker.internal` / `scheduler_db` depending on setup
   - Port: `5432`
   - Username: `postgres`
   - Password: `postgrespassword` (or value from `.env`)
   - Database: `auto_scheduler`

## Pass criteria

- [ ] Page loads (no ERR_CONNECTION_REFUSED)
- [ ] Login succeeds
- [ ] Can expand `auto_scheduler` and see tables (`courses`, `sections`, `course_allowed_timeslot`, …)

## Common failure

```
admin@scheduler.local does not appear to be a valid email address
```

**Fix:** set `PGADMIN_DEFAULT_EMAIL` to a normal domain (e.g. `admin@example.com`), then:

```bash
docker compose up -d --force-recreate pgadmin
```

## Result

- Date run: __________
- Run by: __________
- Outcome: Pass / Fail
- Notes: __________
