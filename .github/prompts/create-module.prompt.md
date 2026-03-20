# Prompt: Scaffold a New Domain Module

Use this prompt to create the empty skeleton of a brand-new domain module before any feature is implemented. The goal is a clean, importable module — stub files wired together, ORM model migrated, empty router registered — with no business logic, no route handlers, no tests, and no seed data. Implement features afterward with `build-feature.prompt.md`.

## Context

- Read `AGENTS.md` for project context, architecture, module anatomy, and quality gates.
- Read `app/merchants/` as a structural reference for an existing module.

## Constraints

- Stubs only — no business logic, no policy functions, no service methods beyond `__init__`, no route handlers.
- No tests — there is nothing to test in a stub-only module.
- No seed data — seeds follow the first feature commit.
- Register the router in `main.py` but add no routes.
- Do not modify files under `alembic/versions/` — generate migrations with `alembic revision --autogenerate`.
- Do not add dependencies to `pyproject.toml` without flagging for human review.
- Register all new ORM models in `app/models.py`.
- All new modules must use the async database stack — `AsyncSession`, `async def` methods, `get_async_db`; do not use `Session` or `get_db()`.

---

## Steps

1. Create `app/<module>/` with: `__init__.py` (empty), `models.py`, `schemas.py`, `repositories.py` (stub ABC and concrete with no methods, import `AsyncSession`), `services.py` (stub with `__init__` only), `policies.py` (empty), `exceptions.py` (empty), `errors.py` (stub `ErrorCode` enum), `composition.py` (stub factory), `api.py` (stub router with no routes).
2. Implement `models.py` fully: UUID string PKs with `default=lambda: str(uuid.uuid4())`, `Mapped`/`mapped_column` annotations, `server_default=text("true")` for boolean DB defaults.
3. Register the model in `app/models.py`.
4. Confirm exactly one Alembic head (`alembic heads`), then generate the migration (`alembic revision --autogenerate -m "add <module> table"`).
5. Inspect the generated migration — verify `upgrade()` and `downgrade()` are correct and `down_revision` matches the head.
6. Apply the migration (`alembic upgrade head`), then verify the round-trip (`alembic downgrade -1 && alembic upgrade head`).
7. Register the router in `app/main.py`.
8. Run `make lint && make test && make coverage && make security` — all must pass.
