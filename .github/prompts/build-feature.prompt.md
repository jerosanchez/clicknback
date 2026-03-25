# Prompt: Implement a New Feature

Use this prompt to implement a single feature (one endpoint) inside an existing module. If the module does not exist yet, scaffold it first with `create-module.prompt.md`.

## Context

- Read `AGENTS.md` for project context, architecture, module anatomy, conventions, and quality gates.
- Read `docs/guidelines/functional-specification.md` to validate the spec before starting.
- Read `docs/guidelines/api-contracts.md` to validate the API contract before starting.
- Read the functional spec for this feature — it is the source of truth for endpoints, auth, business rules, and acceptance scenarios.
- Read all relevant ADRs under `docs/design/adr/` — check the index first.

## Constraints

- Do not modify files under `alembic/versions/` to add application logic.
- Do not create a new migration to fix an unreleased one — edit the unreleased file in place instead.
- Do not add dependencies to `pyproject.toml` without flagging for human review.
- Do not place business logic in `api.py` — it belongs in `services.py` or `policies.py`.
- Do not raise `HTTPException` in services or repositories — use domain exceptions from `exceptions.py`.
- Do not use wildcard CORS origins and do not log passwords, tokens, or secrets.
- Do not modify `app/core/errors/handlers.py` or the global error response shape.
- Do not import ORM models from other modules into services, policies, or repositories — use `clients/` and DTOs.
- Repositories flush with `await db.flush()`, never `db.commit()`.
- Write service methods accept `uow: UnitOfWorkABC` and call `await uow.commit()` once; read-only methods accept `db: AsyncSession` directly.
- Small infrastructure modules (broker, scheduler) keep ABC and implementation in the same file under `app/core/`; promote to sub-package only when the component grows to encompass its own model, repository, and service.
- Critical state-changing operations must call `AuditTrail.record(...)` after success — see ADR-015.
- Domain-specific background jobs live under `app/<domain>/jobs/<job_name>/` following Fan-Out Dispatcher + Per-Item Runner — see ADR-016 and `docs/guidelines/background-jobs.md`.
- Feature flags follow the `clients/feature_flags.py` client pattern; resolution is fail-open; seed the key in `seeds/all.sql` with `enabled = true` — see ADR-018.

---

## Steps

### Step 0 — Review the functional spec and API contract

- Confirm a functional spec file exists; if not, ask the user for the path.
- Verify the spec has all mandatory sections per `docs/guidelines/functional-specification.md`: Title + Preamble, User Story, Constraints, BDD Acceptance Criteria, Use Cases, API Contract link.
- Fix any incomplete or malformed sections.
- Extract all error codes from the spec's Use Cases.
- For each endpoint in the spec, read the corresponding API contract and cross-check: constraints map to failure responses, error codes match, BDD scenarios map to responses, success status codes match intent, and 401/403 failures match authorization constraints.
- Fix any inconsistencies between spec and contract before starting implementation.

### Step 1 — `schemas.py`

- Add `<Entity>Create`, `<Entity>Update` (all-optional fields), and `<Entity>Out` (`model_config = {"from_attributes": True}`) as needed.
- Add `Paginated<Entity>Out` with `items`, `total`, `page`, `page_size` for listing endpoints.
- Add `@field_validator` for every ORM constraint not expressible via Pydantic field arguments (e.g., decimal scale, cross-field invariants).
- Test every `@field_validator` in `tests/<module>/test_<module>_schemas.py`.

### Step 2 — `exceptions.py` and `errors.py`

- Add one exception class per new failure mode; carry context as instance attributes (e.g., `self.merchant_id`).
- Add corresponding `ErrorCode` string enum entries to `errors.py`.

### Step 3 — `policies.py`

- Add one pure function per business rule; raise on violation, return `None` on success.
- No DB access, no HTTP knowledge, no side effects.

### Step 4 — `repositories.py`

- Add query methods to `<Entity>RepositoryABC` and `<Entity>Repository`.
- Use `AsyncSession` and `async def` with SQLAlchemy 2.0 `select()` — do not use `session.query()`.
- Use `list[ColumnElement[bool]]` for dynamic filter conditions.
- For listing endpoints that need foreign data, use batch loading — never per-item lookups inside a loop.

### Step 4a — `clients/` (only if this feature reads or writes data owned by another module)

- Create `clients/<foreign>.py` with a DTO `@dataclass`, `<Foreign>ClientABC`, and `<Foreign>Client`.
- The concrete client queries the shared DB and returns DTOs — never foreign ORM models.
- Re-export all symbols from `clients/__init__.py`; import from the package root, never from sub-modules.
- Inject clients into the service via `__init__()` and wire in `composition.py`.

### Step 5 — `services.py`

- Add one method per endpoint; orchestrate policy checks, repository calls, and client calls.
- Write methods: accept `uow: UnitOfWorkABC`, access session via `uow.session`, call `await uow.commit()` once at the end.
- Read methods: accept `db: AsyncSession` directly.
- Call `AuditTrail.record(...)` after every critical state-changing operation.
- Log `INFO` for successful state mutations; `DEBUG` for expected negative paths; no logging for reads.

### Step 6 — `composition.py`

- Update `get_<entity>_service()` to inject any new repositories, clients, or audit trail.
- Add `get_unit_of_work()` if this feature introduces a write endpoint.

### Step 7 — `api.py`

- Add one route handler per endpoint; declare request/response schemas and status codes.
- Write handlers inject `uow: UnitOfWorkABC = Depends(get_unit_of_work)`; read handlers inject `db: AsyncSession = Depends(get_async_db)`.
- Catch each domain exception with the appropriate `core/errors/builders.py` factory.
- Catch bare `Exception` last, log at `ERROR`, and raise `internal_server_error()`.
- No business logic in handlers.
- Split `api.py` into an `api/` package if it exceeds ~200 lines or gains a distinct role boundary — see `docs/guidelines/code-organization.md`.
- For list responses with nested items, use explicit `model_validate()` conversion on each item.

### Step 8 — `http/<module>/`

- Create one `.http` file per new route following `docs/guidelines/http-requests-file.md`.
- Include `@baseUrl`, resource ID variables, expired placeholder tokens, and helper login requests.
- Cover happy paths first, then 401 → 403 → 422 → 400/409 → 404.
- Never commit real tokens, API keys, or production credentials.

### Step 9 — Alembic migration (only if models changed)

- Follow `add-migration.prompt.md` for all migration steps.

### Step 10 — `seeds/all.sql`

- Add realistic seed rows covering the happy path and important negative states.
- Add enough rows to cover pagination (at least `page_size + 1`) for listing endpoints.

### Step 11 — Tests

- Follow `write-tests.prompt.md` to write the full test suite for this feature.
- This includes both unit tests (Steps 1–5 of `write-tests.prompt.md`) **and** integration
  tests (Step 6) — both are required for every new endpoint.
- Place unit tests under `tests/unit/<module>/` and integration tests under `tests/integration/<module>/`.
- When testing schedulers or brokers, observe only public-contract behavior — do not assert on private attributes or call internal methods directly.

### Step 12 — Quality gates

- Run `make lint && make test && make coverage && make security` — all must pass.
- Confirm the coverage grade is at least ✅ Approved.
