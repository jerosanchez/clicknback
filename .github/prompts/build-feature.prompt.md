# Prompt: Implement a New Feature

Use this prompt to implement a single feature (one or more related endpoints) inside an **existing module**. If the module does not exist yet, scaffold it first with `create-module.prompt.md`, then return here.

## Context Files (Read First)

Before writing any code, read the following files in full:

- `docs/agents/project-context.md` — domain model and system purpose
- `docs/agents/feature-guide.md` — module anatomy, layer responsibilities, coding conventions
- `docs/agents/testing-guidelines.md` — test structure, patterns, and what to test at each level
- `docs/agents/quality-gates.md` — mandatory quality gate sequence
- `docs/design/architecture-overview.md` — system structure and module boundaries
- `docs/design/data-model.md` — entity relationships and field conventions
- `docs/design/error-handling-strategy.md` — error response shape, exception hierarchy, handler rules
- `docs/design/security-strategy.md` — auth model, token handling, secrets rules
- All ADR files under `docs/design/adr/` — rationale behind conventions; read these to understand *why* rules exist before deciding how to apply them
- The functional spec referenced in the **Feature Specification** section below — this is the source of truth for endpoints, auth, business rules, constraints, and all acceptance scenarios

## Known Constraints

- Do not modify files under `alembic/versions/` — migrations are generated via `alembic revision --autogenerate`, never hand-edited.
- Do not add dependencies to `pyproject.toml` without flagging the addition for human review before proceeding.
- Do not place business logic in `api.py` — it belongs in `services.py` or `policies.py`.
- Do not raise `HTTPException` in services or repositories — raise domain exceptions from `exceptions.py` only.
- Do not use allow-all CORS or wildcard origins in any configuration.
- Do not log passwords, tokens, or secrets at any log level.
- Do not modify `app/core/errors/handlers.py` or the global error response shape.

## Commit Protocol

Each step that produces code or files is a **separate commit**. Do not begin the next step until the current step's commit is approved and executed by the human.

To close a step:
1. Run `make lint && make format && make test` — all must pass.
2. Stage the changes and output `git diff --staged`.
3. Propose a commit message.
4. **Wait for explicit human approval before executing `git commit`.**

---

## Feature Specification

> **Fill this section in before handing to the AI.**

- **Functional spec:** `docs/specs/functional/<!-- e.g. purchases/PU-01-purchase-ingestion.md -->`
- **Domain module:** `app/<!-- e.g. purchases -->/` *(must already exist; run `create-module.prompt.md` first if not)*
- **Model changes (if any):** `<!-- e.g. none / add nullable column X to the existing table -->`
- **Notes:** `<!-- Anything not covered by the FR or that overrides it -->`

Read the functional spec in full before proceeding. Derive endpoints, HTTP methods, auth requirements, business rules, constraints, and all acceptance scenarios from it. The BDD scenarios in the spec map directly to the tests in Step 11 — every Given/When/Then must have a corresponding test case.

---

## Implementation Steps

Follow these steps in order. Complete and commit each one before moving to the next.

### Step 1 — `schemas.py`: Pydantic schemas

Add or extend `<Entity>Create` (POST body), `<Entity>Update` (PATCH body, all-optional fields), and `<Entity>Out` (response) as needed for this feature. `<Entity>Out` must set `model_config = {"from_attributes": True}`. Add `Paginated<Entity>Out` with `items`, `total`, `page`, `page_size` fields if this feature includes a listing endpoint.

### Step 2 — `exceptions.py` and `errors.py`: domain exceptions and error codes

Add one exception class per failure mode introduced by this feature to `exceptions.py`. Each exception must carry context as instance attributes (e.g., `self.merchant_id = merchant_id`). Add corresponding `ErrorCode` string enum entries to `errors.py`.

### Step 3 — `policies.py`: business rule functions

One pure function per business rule introduced by this feature. Each function raises the appropriate domain exception on violation and returns `None` on success. No DB access, no HTTP knowledge, no side effects.

### Step 4 — `repositories.py`: data access layer

Add the query methods needed by this feature to `<Entity>RepositoryABC` (abstract) and `<Entity>Repository` (SQLAlchemy). Repositories only query the DB — no business logic.

### Step 5 — `services.py`: business logic orchestration

Add the method(s) for this feature to `<Entity>Service`. Orchestrate policy checks and repository calls. Raise domain exceptions on failures. Log `INFO` for successful state-mutating operations, `DEBUG` for expected negative paths. Do not log read-only operations.

### Step 6 — `composition.py`: dependency wiring

Update `get_<entity>_service()` if new dependencies (e.g., a second repository or an external client) are required by this feature. No changes needed if the existing factory already covers it.

### Step 7 — `api.py`: HTTP router

Add one route handler per endpoint. Each handler: declares request/response schemas and status codes; resolves dependencies via `Depends()`; calls the service; catches each domain exception and converts it with the appropriate `core/errors/builders.py` factory; catches bare `Exception` last, logs at `ERROR`, and raises `internal_server_error()`. Never put business logic here.

For list responses with nested items, use explicit `model_validate()` conversion:

```python
return Paginated<Entity>Out(
    items=[<Entity>Out.model_validate(item) for item in items],
    total=total,
    page=page,
    page_size=page_size,
)
```

### Step 8 — `api-requests/`: manual HTTP test files

Create one `.http` file per new route inside `app/<module>/api-requests/`, named `<verb>-<resource>.http` (e.g., `create-purchase.http`). Each file must cover every distinct HTTP response the endpoint can return — one `###` request per response code. Define `@baseUrl` at the top. Include a login request for authenticated endpoints. Never commit real tokens.

### Step 9 — Alembic migration (only if model changed)

If this feature required changes to the ORM model (new columns, constraints, etc.), run `alembic revision --autogenerate -m "<describe change>"`. Inspect the generated file under `alembic/versions/`. Run `alembic upgrade head`, then `alembic downgrade -1` followed by `alembic upgrade head` to verify the round-trip. Skip this step entirely if no model changes were made.

### Step 10 — Update `seeds/all.sql`

Add realistic seed rows to exercise this feature. Use valid UUIDs. Add enough rows to cover pagination (at least `page_size + 1`) if a listing endpoint is included. Seed both states for any status/flag fields. Group inserts with short SQL comments.

### Step 11 — Write tests

Once all `.http` smoke tests are passing, use `write-tests.prompt.md` to write the test suite for this feature. Tests are a separate commit.

### Step 12 — Quality gates and commit

Run `make lint && make format && make test`. Fix all failures. Run `make coverage` and confirm the grade is at least ✅ Approved. Then stage all changes from this step, propose a commit message, and wait for human approval before executing `git commit`.
