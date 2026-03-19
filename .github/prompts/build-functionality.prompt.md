# Prompt: Build Cross-Cutting Functionality

Use this prompt when implementing logic that **spans multiple existing modules** or **adds significant behavior without a new HTTP endpoint** — for example, a cashback calculation job, a reconciliation process, payout settlement, or any domain operation that coordinates data across module boundaries.

- If the work introduces a **brand-new module** with its own API, use `create-module.prompt.md` first, then `build-feature.prompt.md` for individual endpoints.
- If the work adds a **new endpoint** to an existing module, use `build-feature.prompt.md`.
- If the **only change is a schema addition** independent of new behavior, use `add-migration.prompt.md`.

## Context Files (Read First)

Before writing any code, read the following files in full:

- `docs/guidelines/project-context.md` — domain model and system purpose
- `docs/guidelines/feature-architecture.md` — module anatomy, layer responsibilities, coding conventions
- `docs/guidelines/code-organization.md` — when and how to split large files; naming conventions for split packages and their tests
- `docs/guidelines/unit-testing.md` — test structure, patterns, and what to test at each level
- `docs/guidelines/quality-gates.md` — mandatory quality gate sequence
- `docs/design/architecture-overview.md` — system structure and module boundaries
- `docs/design/data-model.md` — entity relationships and field conventions
- `docs/design/error-handling-strategy.md` — error response shape, exception hierarchy, handler rules
- `docs/guidelines/arch-decision-records.md` — how to read and understand ADRs
- All ADR files under `docs/design/adr/` — read the index first to find relevant decisions for the functionality being implemented
- `docs/guidelines/background-jobs.md` — if this functionality is triggered by a scheduler or runs as a background job

## Known Constraints

- Do not modify files under `alembic/versions/` to add application logic — migrations are generated via `alembic revision --autogenerate`, never hand-edited (see `add-migration.prompt.md`).
- **Do not create a new migration to fix a schema change introduced by an unreleased (non-committed) migration.** If the unreleased head migration needs correction, `alembic downgrade base`, edit the migration file in place, then `alembic upgrade head` again. Adding a follow-up migration for an in-flight change bloats the chain and obscures intent.
- Do not add dependencies to `pyproject.toml` without flagging the addition for human review before proceeding.
- Do not place business logic in `api.py` — it belongs in `services.py` or `policies.py`.
- Do not raise `HTTPException` in services or repositories — raise domain exceptions from `exceptions.py` only.
- Do not log passwords, tokens, or secrets at any log level.
- Do not import ORM models from other modules into `repositories.py`, `policies.py`, or `services.py` — use a `clients/` package and DTOs instead (see Step 4a).
- **Repositories never commit.** Repository methods must call `await db.flush()` (not `db.commit()`) so writes can be batched atomically with other operations. Committing is the caller's responsibility, delegated through the Unit of Work.
- **Services never call `db.commit()` or `db.rollback()` directly.** Any service method that must commit must accept `uow: UnitOfWorkABC` (from `app.core.unit_of_work`) and call `await uow.commit()`. Read-only methods continue to accept `db: AsyncSession`. See [ADR-021](../../docs/design/adr/021-unit-of-work-pattern.md) and `docs/guidelines/feature-architecture.md` §2 (`core/unit_of_work.py`).
- **Small infrastructure/support modules** (broker, scheduler, token provider, etc.) must keep the ABC and the default in-memory/simple implementation in the **same file** under `app/core/`. Promote to a sub-package only when the component grows to encompass its own model, repository, service, and factory (as `app/core/audit/` does).
- Critical state-changing operations (purchase confirmation/rejection, cashback crediting, withdrawal processing, payout settlement, admin overrides) **must** call `AuditTrail.record(...)` in the service method, after the operation succeeds. Inject `AuditTrail` via `__init__()` and wire it in `composition.py`. See [ADR-015: Persistent Audit Trail](../../docs/design/adr/015-persistent-audit-trail.md).
- **Domain-specific background jobs** belong under `app/<domain>/jobs/<job_name>/`, following the Fan-Out Dispatcher + Per-Item Runner pattern documented in [ADR-016](../../docs/design/adr/016-background-job-architecture-pattern.md). Use `app/core/jobs/` only for cross-cutting jobs with no clear domain owner. Wire the task in the domain's `composition.py`, then schedule it in `app/main.py`. Tests live under `tests/<domain>/jobs/`. See `docs/guidelines/background-jobs.md` for the full checklist.
- **Feature flags:** If this functionality should be controllable at runtime (e.g., a background job or experimental behavior), gate it behind a feature flag using the `clients/feature_flags.py` pattern. Resolution is fail-open: if no record exists, `is_enabled()` returns `True`. Seed the flag key in `seeds/all.sql` with `enabled = true`. See [ADR-018](../../docs/design/adr/018-feature-flag-system.md).

## Commit Protocol

Each step that produces code or files is a **separate commit**. Do not begin the next step until the current step's commit is approved and executed by the human.

To close a step:
1. Run `make lint && make test && make coverage && make security` — all must pass.
2. Stage the changes and output `git diff --staged`.
3. Propose a commit message.
4. **Wait for explicit human approval before executing `git commit`.**

**Commit message style:** Write a single summary line. Add a body only when it carries genuine value — a non-obvious rationale, a constraint that isn't self-evident from the diff, or a trade-off worth preserving. Never list files or restate what the diff already shows.

---

## Scope Definition (Fill Before Starting)

> Describe the functionality to be implemented before handing to the AI.

- **What it does:** `<!-- e.g. When a purchase is confirmed, calculate cashback_amount based on the offer's cashback_rate and credit it as pending balance to the user's wallet -->`
- **Trigger:** `<!-- e.g. called directly by PurchaseService.confirm(), OR a background job polling confirmed purchases, OR a scheduled cron -->`
- **Modules touched:** `<!-- list each module and whether it is read-only or written to, e.g. purchases (read), offers (read), wallets (write) -->`
- **Schema changes required:** `<!-- yes/no — if yes, describe which tables and columns -->`
- **New background job required:** `<!-- yes/no — if yes, describe the trigger and the Fan-Out Dispatcher + Per-Item Runner split -->`
- **Feature flag required:** `<!-- yes/no — if yes, provide a flag key -->`
- **Audit trail required:** `<!-- yes/no — list each critical operation that must produce an audit row -->`

---

## Implementation Steps

Follow these steps in order. Complete and commit each one before moving to the next. **Skip any step that produces no code for this specific functionality** — not every step applies to every task.

### Step 0 — Trace the data flow

Before writing any code, map out the full data flow in a short written summary (a scratch note, not a committed file):

1. What triggers this functionality — a caller, an event, or a schedule?
2. Which module owns each piece of data that must be read? Which owns the data that must be written?
3. Does the triggering module already expose a service method that should call into this functionality, or is a new entry point needed?
4. Does any cross-module data access require a new client or a new method on an existing client?
5. What does the happy path look like, step by step? What are the failure modes?

Review the relevant existing service, repository, and client files in each touched module before writing anything. Identify which files will change and which are new.

### Step 1 — `exceptions.py` and `errors.py`: new failure modes

Add one exception class per new failure mode to each affected module's `exceptions.py`. Each exception must carry context as instance attributes (e.g., `self.wallet_id = wallet_id`). Add corresponding `ErrorCode` string enum entries to `errors.py`.

Skip if no new failure modes are introduced.

### Step 2 — `policies.py`: business rules

Add one pure function per new business rule. Each raises the appropriate domain exception on violation and returns `None` on success. No DB access, no HTTP knowledge, no side effects.

Skip if no new business rules are introduced.

### Step 3 — `repositories.py`: data access methods

Add query or write methods to the affected repositories. Keep repositories free of business logic — they only query or persist data.

For any listing method needed by this functionality, apply the same N+1 prevention rules as in `build-feature.prompt.md` Step 4: collect IDs, call a batch method once, enrich with the returned map. Per-item lookups inside a loop are a code-review rejection criterion.

Skip if no new repository methods are needed.

### Step 4a — `clients/`: cross-module clients

If this functionality reads or coordinates data from another module, follow the client pattern:

1. Create `clients/<foreign>.py` inside each consuming module's `clients/` package (create the package if it does not exist yet).
2. Define a lightweight DTO (`@dataclass`), an ABC (`<Foreign>ClientABC`), and a concrete implementation (`<Foreign>Client`). The concrete class queries the shared DB directly and returns DTOs — it never returns foreign ORM models.
3. Update `clients/__init__.py` to re-export all new symbols.
4. Inject the client into the service via `__init__()` and wire it in `composition.py`.

Only `clients/` files may import foreign ORM models. Services, policies, and repositories import only from the `clients` package root.

Skip if all touched data belongs to a single module.

### Step 5 — `services.py`: business logic orchestration

Add or extend service methods to implement the functionality:

- Accept `uow: UnitOfWorkABC` for write methods; `db: AsyncSession` for read-only methods.
- Call `await uow.commit()` exactly once, at the end of each atomic unit of work.
- Access the session via `uow.session` when passing it to repositories or clients inside a write method.
- Call `AuditTrail.record(...)` for every critical state-changing operation, after the operation succeeds.
- Log `INFO` for successful state mutations; `DEBUG` for expected negative paths (e.g., wallet not found, skipping). Do not log read-only operations.

### Step 6 — Background job (only if the trigger is a scheduler or event)

If this functionality runs on a schedule or in response to a domain event rather than being called directly:

1. Scaffold the job under `app/<domain>/jobs/<job_name>/` with a dispatcher and a per-item runner following [ADR-016](../../docs/design/adr/016-background-job-architecture-pattern.md).
2. Gate the job behind a feature flag (see Known Constraints).
3. Wire `get_<job_name>_task()` in the domain's `composition.py`.
4. Schedule the task in `app/main.py`.

See `docs/guidelines/background-jobs.md` for the complete implementation checklist.

Skip if the functionality is always invoked directly by an existing service or endpoint.

### Step 7 — `composition.py`: dependency wiring

Update the relevant `get_<entity>_service()` factory to inject any new repositories, clients, or infrastructure dependencies introduced in the steps above. Add `get_<job_name>_task()` if a background job was added.

No changes needed if existing factories already wire all required dependencies.

### Step 8 — Alembic migration (only if schema changed)

If this functionality required changes to any ORM model (new columns, new tables, updated constraints), follow all steps in `add-migration.prompt.md`. Skip entirely if no model changes were made.

### Step 9 — Update `seeds/all.sql`

If this functionality depends on seeded data — a feature flag key, specific wallet states, published offers — add or update the relevant seed rows. Use valid UUIDs and realistic values covering both the happy path and any important negative states.

### Step 10 — Write tests

Use `write-tests.prompt.md` to write the full test suite for this functionality. Tests are a separate commit.

At minimum, cover:

- Each new policy function: one test per rule violation, one for the happy path.
- Each new repository method: test the query shape and edge cases (empty result, not-found, filter combinations).
- Each new or modified service method: happy path end-to-end, each sad path, and — for critical operations — assert that `AuditTrail.record` was called with the correct arguments.
- The dispatcher and runner independently, if a background job was added. Observe only public-contract behavior; do not assert on private attributes or internal scheduling state.

### Step 11 — Quality gates and commit

Run `make lint && make test && make coverage && make security`. Fix all failures. Confirm the coverage grade is at least ✅ Approved.