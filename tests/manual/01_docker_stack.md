# 01 — Docker stack verification

**Owner:** Data Engineer / anyone setting up the environment  
**Depends on:** Docker Desktop running  
**Goal:** All required services start and stay healthy.

## Preconditions

- [ ] Docker Desktop is running
- [ ] You are in the repository root
- [ ] Ports 5432, 5050, 5678, 3000 are free (or you accept conflicts)

## Steps

```bash
docker compose down
docker compose up -d
docker compose ps
```

## Expected containers

| Container            | Image                      | Port(s)     | Expected status |
|----------------------|----------------------------|-------------|-----------------|
| `scheduler_db`       | postgres:16                | 5432        | Up (healthy)    |
| `scheduler_pgadmin`  | dpage/pgadmin4             | 5050 → 80   | Up              |
| `scheduler_n8n`      | n8nio/n8n                  | 5678        | Up (or note port conflict) |
| `scheduler_gotenberg`| gotenberg/gotenberg:8      | 3000        | Up              |

## Pass criteria

- [ ] `scheduler_db` shows **healthy**
- [ ] `scheduler_pgadmin` is **Up** (not Restarting)
- [ ] `scheduler_gotenberg` is **Up**
- [ ] `scheduler_n8n` is **Up** *or* failure is documented as known port conflict (see notes)

## If something fails

```bash
docker compose logs postgres --tail 40
docker compose logs pgadmin --tail 40
docker compose logs n8n --tail 40
docker compose logs gotenberg --tail 40
```

### Known issues

- **pgAdmin email:** must be a real-looking address (e.g. `admin@example.com`), not `*.local`.
- **n8n port 5678:** if another local n8n is already running, this container may fail. That is an integration concern for the workflow role; it does not block database verification.

## Result

- Date run: __________
- Run by: __________
- Outcome: Pass / Fail
- Notes: __________
