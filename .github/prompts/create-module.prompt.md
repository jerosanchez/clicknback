# Prompt: Scaffold a New Domain Module

Use this prompt to create the empty skeleton of a brand-new domain area (e.g., `offers/`, `wallets/`, `payouts/`) **before any feature is implemented**. The goal is a clean, importable module — stub files wired together, ORM model migrated, empty router registered — with **no business logic, no route handlers, no tests, and no seed data**. Once this scaffold is committed, the developer will implement features inside it using `build-feature.prompt.md`.

## Context Files (Read First)

Before writing any code, read the following files in full:

- `docs/agents/project-context.md` — domain model and system purpose
- `docs/agents/feature-guide.md` — module anatomy, layer responsibilities, coding conventions

Also read at least one existing module for structural reference:

- `app/merchants/` — models, schemas, repositories, services, policies, exceptions, errors, composition, api

## Known Constraints

- **Stubs only** — no business logic, no policy functions, no service methods beyond `__init__`, no route handlers.
- **No tests** — there is nothing to test in a stub-only module.
- **No seed data** — seeds follow the first feature commit.
- The router (`api.py`) must be registered in `main.py` but must have no routes.
- Do not modify files under `alembic/versions/` — migrations are generated via `alembic revision --autogenerate`, never hand-edited.
- Do not add dependencies to `pyproject.toml` without flagging for human review.
- All new ORM models must be registered in `app/models.py`.

## Commit Protocol

Complete all steps, then commit once. Stage all changes and show a `git diff --staged` summary. Propose a single commit message for the entire scaffold but do not execute `git commit` until the human explicitly approves.

---

## Module Specification

> **Fill this section in before handing to the AI.**

- **Module name:** `<!-- e.g. offers -->`
- **Module path:** `app/<!-- e.g. offers -->/`
- **Description:** `<!-- What domain problem does this module solve? -->`
- **Entities and their fields:**

  ```
  <!-- e.g.
  Offer:
    id: UUID (PK)
    merchant_id: UUID (FK → merchants.id)
    title: str
    cashback_percentage: float
    active: bool (default true)
    created_at: datetime (server default)
  -->
  ```

- **Planned endpoints (names only, for stub file naming):**

  ```
  <!-- e.g.
  POST   /api/v1/offers
  GET    /api/v1/offers
  GET    /api/v1/offers/{id}
  PATCH  /api/v1/offers/{id}
  DELETE /api/v1/offers/{id}
  -->
  ```

- **Relations:** `<!-- FK constraints, cascade rules -->`
- **Open questions:** `<!-- Anything unresolved that requires human input before the AI can proceed -->`

---

## Scaffolding Steps

Complete all steps, then propose a single commit.

### Step 1 — Directory and stub files

Create `app/<module>/` with the following files:

- `__init__.py` — empty
- `models.py` — imports only (`from sqlalchemy import ...`)
- `schemas.py` — imports only (`from pydantic import ...`)
- `repositories.py` — stub: `<Entity>RepositoryABC(ABC)` with no abstract methods yet; `<Entity>Repository(<Entity>RepositoryABC)` with no methods yet
- `services.py` — stub: `<Entity>Service` class with `__init__(self, repository: <Entity>RepositoryABC)` and no other methods
- `policies.py` — empty
- `exceptions.py` — empty
- `errors.py` — stub: `class ErrorCode(str, Enum): pass`
- `composition.py` — stub: `get_<entity>_service()` factory that instantiates `<Entity>Service` with a concrete `<Entity>Repository()`
- `api.py` — stub: `router = APIRouter(prefix="/api/v1")` with no registered routes
- `api-requests/.gitkeep` — empty file to track the directory in git

### Step 2 — ORM model

Implement `models.py` fully. Use UUID string PKs with `default=lambda: str(uuid.uuid4())`. Use `Mapped` and `mapped_column` annotations throughout. Use `server_default=text("true")` for boolean DB defaults. Register the model in `app/models.py`.

### Step 3 — Alembic migration

Run `alembic revision --autogenerate -m "add <module> table"`. Inspect the generated file under `alembic/versions/` to confirm it captures only the intended schema changes. Run `alembic upgrade head`. Then run `alembic downgrade -1` followed by `alembic upgrade head` to verify the round-trip is clean.

### Step 4 — Register router in `main.py`

Add:

```python
from app.<module> import api as <module>_api
app.include_router(<module>_api.router)
```

### Step 5 — Quality gates

Run `make lint && make format && make test`. The scaffold must pass with zero failures. Fix any import or style issues before proposing the commit.
