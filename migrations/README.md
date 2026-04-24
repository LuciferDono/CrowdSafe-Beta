# Migrations

Alembic-managed schema migrations. Works against SQLite (dev) and Postgres + TimescaleDB (prod).

## Commands

```bash
# Generate a new migration from model changes
alembic revision --autogenerate -m "description"

# Apply all pending migrations
alembic upgrade head

# Roll back one revision
alembic downgrade -1

# Show current head
alembic current
```

## Notes

- The `DATABASE_URL` env var controls which DB alembic talks to (see `migrations/env.py`).
- Postgres-only SQL (TimescaleDB `create_hypertable`, triggers) is guarded by `dialect.name == 'postgresql'` inside each migration — the same files apply cleanly to SQLite dev instances.
- Do **not** hand-edit applied migrations. Generate a new revision instead.
