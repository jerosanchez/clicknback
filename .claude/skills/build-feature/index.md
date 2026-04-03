---
name: build-feature
type: skill
description: Implement a single feature or endpoint
---

# Skill: Build a Feature

Implement a single feature (one endpoint) inside an existing module. If the module doesn't exist, scaffold it first with the `create-module` skill.

## Before You Start

1. **Confirm functional spec exists** — Read `docs/specs/functional/<domain>/<spec-file>.md`
   - Verify: Title, User Story, Constraints, BDD Acceptance Criteria, Use Cases, API Contract link
   - Fix any incomplete sections

2. **Confirm API contract exists** — Read `docs/design/api-contracts/<domain>/<contract-file>.md`
   - Cross-check: Constraints map to failure responses, error codes match, BDD scenarios map to responses
   - Verify: 401, 403 (if applicable), 500 responses exist
   - Fix any inconsistencies with the spec

3. **Review relevant ADRs** — Check `docs/design/adr-index.md` for decisions affecting this feature
   - Example: ADR-010 (async database), ADR-021 (Unit of Work), ADR-023 (event-driven audit logging)

## Implementation Workflow

### Step 1: Schemas

Add Pydantic schemas to `schemas.py`:

- `<Entity>Create` — Input schema for POST/PUT
- `<Entity>Update` — Input schema (all fields optional)
- `<Entity>Out` — Output schema with `model_config = {"from_attributes": True}`
- `Paginated<Entity>Out` — Paginated response (for list endpoints)

Add validators:
- `@field_validator` for every ORM constraint not expressible via Pydantic fields
- Test validators in `tests/unit/<module>/test_<module>_schemas.py`

**See:** `template.md` for schema examples

### Step 2: Exceptions & Errors

Add to `exceptions.py`:
- One exception class per failure mode
- Carry context as instance attributes (e.g., `self.merchant_id`)

Add to `errors.py`:
- Corresponding `ErrorCode` string enum entries

**See:** `template.md` for exception/error examples

### Step 3: Policies

Add to `policies.py`:
- One pure function per business rule
- Raise domain exception on violation, return `None` on success
- No DB access, no HTTP knowledge, no side effects

**See:** `examples.md` for policy examples

### Step 4: Repositories

Add to `repositories.py`:
- Query methods to `<Entity>RepositoryABC` and `<Entity>Repository`
- Use `AsyncSession` and `select()` (SQLAlchemy 2.0 style)
- Use `list[ColumnElement[bool]]` for dynamic filters
- Use batch loading for foreign data (never per-item loops)

**See:** `template.md` for repository examples

### Step 4a: Clients (If Reading Another Module's Data)

Create `clients/<foreign>.py`:
- DTO `@dataclass`
- `<Foreign>ClientABC` interface
- `<Foreign>Client` concrete implementation (queries shared DB, returns DTOs)
- Re-export from `clients/__init__.py`

**See:** `examples.md` for client examples

### Step 5: Services

Add to `services.py`:
- One method per endpoint
- Orchestrate: policy checks → repository calls → client calls
- Write methods: accept `uow: UnitOfWorkABC`, call `await uow.commit()` once at end
- Read methods: accept `db: AsyncSession` directly
- Publish domain event after critical state-changing operations

**See:** `template.md` and `examples.md` for service patterns

### Step 6: API Routes

Add to `api.py` (or `api/<public|admin>.py` if split):
- One route per endpoint
- HTTP boundary only: translate HTTP request → service call → HTTP response
- Map domain exceptions to HTTP error responses
- No business logic in route handlers

**See:** `template.md` and `examples.md` for API endpoint patterns

### Step 7: HTTP Request File (Manual Testing)

Create `http/<module>/<verb-resource>.http`:
- Comment header describing endpoint and seed data
- Variables for token refresh and resource IDs
- Example requests ready to execute

**See:** HTTP file skill for details

## Constraints (Never Violate)

- ✅ Do not modify files under `alembic/versions/` for application logic
- ✅ Do not place business logic in `api.py` — belongs in `services.py` or `policies.py`
- ✅ Do not raise `HTTPException` in services/repositories — use domain exceptions
- ✅ Do not use wildcard CORS origins; do not log passwords, tokens, or secrets
- ✅ Do not import ORM models from other modules into services/policies/repositories — use clients/DTOs
- ✅ Repositories flush with `await db.flush()`, never `db.commit()`
- ✅ Write service methods call `await uow.commit()` exactly once per method
- ✅ Critical state-changing operations must publish a domain event (see ADR-023)
- ✅ Features using feature flags must seed the key in `seeds/dev.sql` with `enabled = true`

## Quality Criteria

Before submitting for review:

- [ ] Functional spec is correct and accessible
- [ ] API contract is correct and accessible
- [ ] All BDD scenarios map to implemented logic
- [ ] All error codes from spec are in `errors.py`
- [ ] All exceptions are domain exceptions (not HTTPException)
- [ ] No business logic in `api.py`
- [ ] All write services use `UnitOfWorkABC` and call `uow.commit()`
- [ ] All monetary values are `Decimal` (not `float`)
- [ ] All repository methods are `async def` using `select()`
- [ ] All domain events published for critical operations
- [ ] HTTP file created for manual testing
- [ ] `make lint && make test && make coverage && make security` all pass

---
