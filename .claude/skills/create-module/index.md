---
name: create-module
type: skill
description: Scaffold a new domain module
---

# Skill: Create a Module

Scaffold a brand-new domain module (empty skeleton: stub files, ORM model, migration, router registered).

## What Gets Created

- Empty `__init__.py`, `models.py`, `schemas.py`, `repositories.py`, `services.py`, `policies.py`, `exceptions.py`, `errors.py`, `composition.py`, `api.py`
- Alembic migration for the module's tables
- Router stub registered in `main.py`
- **No business logic, no tests, no seed data**

## Workflow

### Step 1: Create Directory Structure

```bash
mkdir -p app/<module>
touch app/<module>/__init__.py
```

### Step 2: Stub Files

Create all files with imports but no implementations (see `template.md`).

### Step 3: Create ORM Model

Define `models.py` fully:
- UUID primary key (string type)
- `Mapped` and `mapped_column` annotations (SQLAlchemy 2.0)
- Nullable/non-nullable fields
- Default values (boolean with server defaults, timestamps with `utcnow`)

### Step 4: Register Model in app/models.py

```python
# app/models.py
from app.<module>.models import <Entity>

__all__ = [..., "<Entity>", ...]
```

Alembic's autogenerate reads `app/models.py` to detect schema changes.

### Step 5: Generate Migration

```bash
alembic revision --autogenerate -m "add <module> table"
alembic upgrade head
```

Verify migration is correct (inspect `upgrade()` and `downgrade()`).

### Step 6: Round-Trip Test

```bash
alembic downgrade -1 && alembic upgrade head
```

### Step 7: Register Router

```python
# app/main.py
from app.<module> import api as <module>_api

app.include_router(<module>_api.router)
```

### Step 8: Quality Gates

```bash
make lint && make test && make coverage && make security
```

All must pass before handoff.

---
