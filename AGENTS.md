# ClickNBack – Agent Instructions

> Read in full all referenced documents before working on any request.

---

## AI behaviour

- Do not ask for permission before running read-only or non-destructive shell commands (e.g., `ls`, `cat`, `tail`, `wc`, `grep`, `find`, `head`, `diff`, `stat`).
- Do not ask for permission before running Makefile targets, unless the target is destructive or deploys to production.
- Do not ask for permission before running shell commands that only change source code files (e.g., code generation, formatting, refactoring, or applying patches), but always summarize the change before and after.
- Never stage, commit, or push changes to version control; always leave the decision to commit or deploy to the human.
- Never execute commands that are not easily reversible or that could cause data loss (e.g., `rm`, `mv`, `dd`, `chmod` on critical files, database drops, or destructive migrations) without explicit human approval.
- Never run commands that affect production infrastructure, external services, or perform deployments without explicit human approval.
- Always prefer idempotent and reversible actions; if an action is not reversible, warn the user and require explicit approval.
- Never expose, print, or log secrets, credentials, or sensitive data at any time.
- Always validate the safety and intent of any command before execution; if in doubt, ask for clarification or escalate to the human.
- When generating or modifying files, always follow project conventions and summarize the change for review.
- When in doubt about the safety or reversibility of an action, default to asking for human approval.

---

## Product Context

- **ClickNBack** is a production-grade cashback platform backend demonstrating real-world financial correctness, idempotency, and concurrency safety.
- Users earn cashback on purchases at partner merchants; the platform tracks balances, manages rewards, and processes withdrawals.
- Roles: `user` (earns cashback) and `admin` (manages the platform).
- Domain entities: User, Merchant, Offer, Purchase, CashbackTransaction, Wallet, Payout.
- All monetary values use `Decimal`, never `float`.
- Offers define reward type (percentage or fixed), validity period, and optional per-user monthly caps.
- Purchases are idempotent by `external_id` (unique DB constraint); re-submission yields a conflict.
- State machines govern transitions: Purchase (`pending → confirmed | reversed`) and CashbackTransaction (mirrors purchase states).
- Wallet tracks three buckets per user: `pending`, `available`, `paid`; updated atomically within transactions.
- Wallet withdrawal uses `SELECT FOR UPDATE` row-level locking to prevent race conditions.
- Errors follow a standard JSON shape: `{ "error": { "code", "message", "details" } }`.
- Tech stack: FastAPI, SQLAlchemy (async), PostgreSQL, Alembic, pydantic-settings, python-jose, passlib+bcrypt, pytest; Python ≥ 3.13.

---

## Architecture

- Modular monolith: one deployable unit with well-bounded domain modules under `app/`.
- Each module owns its models, business logic, repositories, schemas, and API surface.
- Cross-module access is only through explicit client abstractions in the module's `clients/` package — never direct imports of another module's models or repositories.
- Strict layering: `api → services + policies → repositories → DB`; no layer skips or reverse dependencies.
- `app/core/` holds shared infrastructure: config, DB sessions, auth dependencies, error builders, logging, audit trail, scheduler, broker.
- `app/main.py` is the composition root: wires routers, schedules background jobs, registers global handlers.
- All ORM models must be imported in `app/models.py` for Alembic autogenerate to work.
- Migrations live in `alembic/versions/`; run via `alembic upgrade head`.
- See `docs/design/architecture-overview.md` and `docs/design/data-model.md` for system diagrams and entity details.

---

## Module Anatomy

- Every module lives in `app/<module>/` with a consistent set of layers; see `docs/guidelines/feature-architecture.md` for the full anatomy and layer responsibilities.
- `models.py` — SQLAlchemy ORM models; only source of truth for table structure.
- `schemas.py` — Pydantic input/output schemas; ORM models are never returned directly from the API.
- `repositories.py` — DB access only; defines `<Entity>RepositoryABC` (interface) and `<Entity>Repository` (concrete); never calls `db.commit()`.
- `services.py` — business logic orchestration; calls repositories and policies; never touches HTTP concepts.
- `policies.py` — pure functions enforcing exactly one business rule each; raise domain exceptions on violation; no side effects or I/O.
- `exceptions.py` — domain-specific exceptions with context attributes; no FastAPI or HTTP concepts.
- `errors.py` — module-scoped `ErrorCode` string enum for HTTP error codes; global codes live in `core/errors/codes.py`.
- `composition.py` — FastAPI `Depends()` factory functions; the only place where concrete implementations are wired.
- `api.py` (or `api/` package) — HTTP boundary; translates between HTTP and the domain; no business logic in route handlers.
- `clients/` — cross-module dependency package (DTOs as `@dataclass`, ABC, concrete impl); present only when the module reads or writes data owned by another module.

---

## Unit of Work Pattern

- Service methods that **commit** accept `uow: UnitOfWorkABC` (not a raw session) and call `await uow.commit()` as the transaction boundary.
- Read-only service methods accept `db: AsyncSession` directly.
- `uow.session` is the `AsyncSession` used to pass to repositories inside a write operation.
- See `core/unit_of_work.py` and `docs/design/adr/021-unit-of-work-pattern.md`.

---

## Async Database Layer

- All new modules use `AsyncSession` and `async def` repository methods (SQLAlchemy 2.0 Core `select()` style).
- Do not mix `get_db` (sync) and `get_async_db` (async) within the same module.
- Repositories flush with `await db.flush()`, never `db.commit()`.
- See `docs/design/adr/010-async-database-layer.md`.

---

## Code Organization and File Splitting

- Default: one file per layer; keep files under ~200 lines.
- Split `api.py` into an `api/` package when it exceeds ~200 lines or has distinct role-based concerns (`admin.py`, `public.py`).
- Split `services.py` into a `services/` package when it exceeds ~200 lines; re-export the main class from `services/__init__.py`.
- Split `schemas.py` or `repositories.py` into packages when they exceed ~150 lines; always re-export from `__init__.py` so existing imports are unchanged.
- Do not split preemptively; start flat and refactor when navigation becomes difficult.
- Full decision framework, thresholds, and naming conventions: `docs/guidelines/code-organization.md`.

---

## Unit Testing

- Test pyramid: many unit tests (all deps mocked), some integration tests (real DB), few E2E tests (Docker Compose).
- Test what matters: service logic, API response/error mapping, policies, utilities, collaborator integration (see `docs/design/adr/022-collaborator-integration-verification-in-unit-tests.md`).
- Do not test thin repository implementations or framework internals.
- Test name pattern: `test_{sut}_{result}_on_{condition}` — e.g., `test_create_user_raises_on_email_already_registered`.
- AAA structure with explicit `# Arrange`, `# Act`, `# Assert` (or `# Act & Assert`) comments.
- Tests are fully independent; no shared mutable state between tests.
- No magic values: extract literals into named variables.
- Full type hints on all fixtures and test functions.
- File naming: `tests/{module}/test_{module}_{layer}.py`; mirrors source layout exactly; see `docs/guidelines/unit-testing.md` §2.
- Service tests: one mock fixture per dependency; service fixture assembles the class; `db = AsyncMock()` created locally in each read-only test; `uow = _make_uow()` created locally in each write test.
- Mock ABCs with `create_autospec(TheABC)`; mock callables with `Mock()`; mock `UnitOfWorkABC` with a plain `Mock` (not `create_autospec`).
- API tests: assert every response field individually (not just status code); one parametrized test must enumerate every domain exception the endpoint can raise.
- Write tests must assert `uow.commit.assert_called_once()` on success and `uow.commit.assert_not_called()` when an exception prevents commit.
- Collaborator verification: assert dependencies are called with correct arguments and return values are correctly mapped.
- Read `tests/conftest.py` first before writing fixtures; reuse existing `{model}_factory` and `{model}_input_data` fixtures.
- Full testing guidelines: `docs/guidelines/unit-testing.md`.

---

## Background Jobs

- Jobs are domain-owned and live under `app/<domain>/jobs/<job_name>/`; never co-locate unrelated jobs.
- Each job follows the **Fan-Out Dispatcher + Per-Item Runner** pattern (see `docs/design/adr/016-background-job-architecture-pattern.md`).
- Each job exposes a `make_<job_name>_task(*, ...)` factory with keyword-only args; returns a zero-arg `ScheduledTask` closure.
- Inject `datetime_provider` as a factory parameter (default: `lambda: datetime.now(timezone.utc)`) so tests can freeze time.
- Extract core logic to an internal `_<job_name>(*, db, ...)` function for direct testing without mocking the session factory.
- Jobs open their own `AsyncSession` via the injected `db_session_factory`; they are not part of the request lifecycle.
- Every critical state-changing job records an audit row via `AuditTrail.record(actor_type=AuditActorType.system, ...)`.
- Wire jobs in two steps: `<domain>/composition.py` constructs the task; `app/main.py` schedules it before the `lifespan` block.
- Each job interval and behavioral knob must be a `Settings` field in `app/core/config.py`.
- Full guide: `docs/guidelines/background-jobs.md`.

---

## Quality Gates

- Run `make lint && make test && make coverage && make security` after every change; all four must exit 0.
- Never hand back to the user while any gate is failing; fix issues autonomously and re-run from the start.
- `make lint` runs `markdownlint`, `flake8`, `isort --check-only`, `black --check`.
- `make test` runs the full pytest suite with coverage; generates `htmlcov/`, `coverage.xml`, and terminal output.
- Coverage hard gate: 85% (CI fails below this); aspirational target: 80%.
- `make security` runs Bandit on `app/` at medium/high severity; do not suppress with `# nosec` without documented reason.
- Do not add `@pytest.mark.skip`, `@pytest.mark.xfail`, or stub implementations to make tests pass.
- Do not add `# noqa` suppressions without a documented inline reason.
- Import order (enforced by isort): stdlib → third-party → local (core/infrastructure first, then module under test).
- Full gate details and failure remedies: `docs/guidelines/quality-gates.md`.

---

## Feature Documentation

- Every feature requires three documentation layers: functional spec, API contract, and (if applicable) an ADR.
- Write docs before implementing; they are the contract the implementation must satisfy.
- Full feature documentation checklist: `docs/guidelines/feature-documentation.md`.

### Functional Specifications (`docs/specs/functional/<domain>/`)

- One spec per feature (one user-facing action, not a domain area).
- Naming: `XX-NN-short-name.md` (two-letter domain prefix, two-digit sequence, kebab-case).
- Mandatory sections in order: Title + Preamble, User Story, Domain Concepts (optional), Constraints, BDD Acceptance Criteria, Use Cases, API Contract link.
- Constraints must be exhaustive: list every authorization check, input rule, and data dependency.
- BDD scenarios must cover: happy path, auth failure, validation failure, business-rule failure.
- Never embed JSON or HTTP details in the spec; those go in the API contract.
- Authoring guide: `docs/guidelines/functional-specification.md`.

### API Contracts (`docs/design/api-contracts/<domain>/`)

- One contract per endpoint (one HTTP method + path).
- Naming: `<verb>-<resource>.md` (e.g., `set-feature-flag.md`, `list-merchants.md`).
- Mandatory sections in order: Title + Endpoint Declaration (method, path, roles), Request (path params, query params, body), Success Response, Failure Responses.
- Every failure mode from the functional spec must have a response entry with a specific error code.
- Error codes must be specific (e.g., `MERCHANT_NOT_FOUND`), not generic.
- Always include 401, 403 (if applicable), and 500 responses.
- Use realistic but fictional data: valid UUIDs, ISO 8601 timestamps, actual enum values.
- After creating, update `docs/design/api-contracts-index.md`.
- Authoring guide: `docs/guidelines/api-contracts.md`.

### Architecture Decision Records (`docs/design/adr/`)

- Write an ADR when a decision: affects multiple modules or the whole system, has meaningful tradeoffs, and shapes future work.
- Do not write ADRs for trivial or purely local decisions.
- Naming: `NNN-kebab-case-title.md` (sequential zero-padded number).
- Mandatory sections: Status, Context (with options), Decision, Consequences.
- After writing, add to `docs/design/adr-index.md` and update relevant guidelines/prompts.
- Authoring guide: `docs/guidelines/arch-decision-records.md`.

### Other Documentation Updates

- After documenting a feature, review and update: `docs/specs/product-overview.md`, `docs/specs/system-requirements.md`, `docs/specs/future-improvements.md`, `docs/specs/domain-glossary.md`, and the `README.md` roadmap table.

---

## Markdown Standards

- Every `.md` file starts with exactly one `#` heading; heading levels increment by one (no skipping).
- Surround every heading with a blank line above and below.
- No trailing punctuation in headings; no duplicate headings in the same file.
- Every fenced code block must declare a language (`python`, `bash`, `json`, `text`, etc.).
- Fenced code blocks must be surrounded by blank lines.
- Lists must be surrounded by blank lines.
- Lines must not exceed the configured length limit.
- Full Markdown conventions: `docs/guidelines/markdown-docs.md`.

---

## HTTP Request Files (`http/<module>/`)

- One `.http` file per endpoint; naming: `<verb>-<resource>.http`.
- Every file starts with a comment header describing the endpoint and relevant seed data.
- Declare `@baseUrl = http://localhost:8001/api/v1` as the first variable; never hardcode the base URL in requests.
- Include expired placeholder tokens as variables (`@adminToken`, `@userToken`) with helper login requests to refresh them.
- Use real UUIDs from `seeds/all.sql` for resource ID variables.
- Never commit real tokens, API keys, or production credentials.
- Full authoring guide: `docs/guidelines/http-requests-file.md`.

---

## Documentation Organization

- Project entry points: `README.md` (overview, quickstart) and `CONTRIBUTING.md` (setup, contribution process).
- Architecture and decisions: `docs/design/` (ADRs, architecture overview, data model, strategy docs, API contracts).
- Functional requirements: `docs/specs/` (functional specs by domain, non-functional specs, workflow docs).
- Developer guidelines: `docs/guidelines/` (how to implement, test, document, organize).
- Manual testing: `http/` (`.http` request files per endpoint).
- Full documentation structure and audience map: `docs/guidelines/docs-organization.md`.
