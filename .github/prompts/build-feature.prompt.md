# Prompt: Implement a New Feature

Use this prompt to implement a single feature (one single endpoint or component) inside an **existing module**. If the module does not exist yet, scaffold it first with `create-module.prompt.md`, then return here.

## Context Files (Read First)

Before writing any code, read the following files in full:

- `docs/guidelines/project-context.md` — domain model and system purpose
- `docs/guidelines/functional-specification.md` — how to recognize a complete and well-formed functional specification; use this to validate the spec before starting implementation- `docs/guidelines/api-contracts.md` — how to recognize a complete and well-formed API contract; use this to validate the contract and ensure consistency with the spec during Step 0- `docs/guidelines/feature-architecture.md` — module anatomy, layer responsibilities, coding conventions
- `docs/guidelines/code-organization.md` — when and how to split large files; naming conventions for split packages and their tests
- `docs/guidelines/unit-testing.md` — test structure, patterns, and what to test at each level
- `docs/guidelines/quality-gates.md` — mandatory quality gate sequence
- `docs/design/architecture-overview.md` — system structure and module boundaries
- `docs/design/data-model.md` — entity relationships and field conventions
- `docs/design/error-handling-strategy.md` — error response shape, exception hierarchy, handler rules
- `docs/design/security-strategy.md` — auth model, token handling, secrets rules
- `docs/guidelines/arch-decision-records.md` — how to read and understand ADRs
- All ADR files under `docs/design/adr/` — architectural decisions and their rationale; read the ADR index first to find relevant decisions for the feature you're implementing
- The functional spec referenced in **Step 0** below — this is the source of truth for endpoints, auth, business rules, constraints, and all acceptance scenarios

## Known Constraints

- Do not modify files under `alembic/versions/` — migrations are generated via `alembic revision --autogenerate`, never hand-edited.
- Do not add dependencies to `pyproject.toml` without flagging the addition for human review before proceeding.
- Do not place business logic in `api.py` — it belongs in `services.py` or `policies.py`.
- Do not raise `HTTPException` in services or repositories — raise domain exceptions from `exceptions.py` only.
- Do not use allow-all CORS or wildcard origins in any configuration.
- Do not log passwords, tokens, or secrets at any log level.
- Do not modify `app/core/errors/handlers.py` or the global error response shape.
- Do not import ORM models from other modules into `repositories.py`, `policies.py`, or `services.py` — use a `clients/` package and DTOs instead (see Step 4a).
- **Small infrastructure/support modules** (broker, scheduler, token provider, etc.) must keep the ABC and the default in-memory/simple implementation in the **same file**, placed directly under `app/core/` (e.g., `app/core/broker.py`, `app/core/scheduler.py`). Do not split the interface and its default implementation into separate files (`broker_abc.py` + `broker.py`) — that fragmentation adds no value at this scale and forces unnecessary cross-file navigation. **Exception:** when an infrastructure component grows to encompass its own model, repository, service, and factory (as `app/core/audit/` does), promote it to a sub-package under `app/core/` following the same layered structure as domain feature modules. The sub-package must expose all public symbols through its `__init__.py` so call sites remain unchanged.
- Event or message payload definitions that are domain-specific belong in a sub-package (e.g., `app/core/events/`) and are kept separate from the infrastructure files. See `app/core/broker.py`, `app/core/scheduler.py`, and `app/auth/token_provider.py` as reference examples.
- Critical state-changing operations (purchase confirmation/rejection, cashback crediting, withdrawal processing, payout settlement, admin overrides) **must** call `AuditTrail.record(...)` in the service method, after the operation succeeds. Inject `AuditTrail` via `__init__()` and wire it in `composition.py`. See `docs/guidelines/feature-architecture.md` §2 (`core/audit/`) and [ADR-015: Persistent Audit Trail](../../docs/design/adr/015-persistent-audit-trail.md).
- **Domain-specific background jobs** (polling loops, confirmation jobs, settlement jobs) belong under `app/<domain>/jobs/<job_name>/`, following the Fan-Out Dispatcher + Per-Item Runner pattern documented in [ADR-016](../../docs/design/adr/016-background-job-architecture-pattern.md). Use `app/core/jobs/` only for cross-cutting jobs with no clear domain owner. Wire the task in the domain's `composition.py` (e.g. `get_<job_name>_task()`), then schedule it in `app/main.py`. Tests live under `tests/<domain>/jobs/`, one file per module (`test_<job>_runner.py`, `test_<job>_dispatcher.py`, etc.). See `docs/guidelines/background-jobs.md` for the full checklist.
- **Feature flags:** If the feature being implemented should be controllable at runtime (e.g. a background job, an experimental endpoint, or a behaviour that may need to be disabled during testing, demos, or incident response), gate it behind a feature flag. Treat `feature_flags` as a foreign module and follow **the same Step 4a client pattern** already used for cross-module dependencies: add a `clients/feature_flags.py` file to the **current module's own** `clients/` package (creating the package if it doesn't exist yet). Define a `FeatureFlagsClientABC` with an `is_enabled(key)` method and a concrete `FeatureFlagsClient` that calls `FeatureFlagService` via the shared database. Inject the ABC into the gated component via `__init__()` and call `await feature_flags.is_enabled("<flag_key>")` at the relevant entry point. Wire the concrete class in `composition.py`. If `feature_flags` is ever promoted to a standalone microservice, only that concrete class is replaced with one calling `GET /api/v1/feature-flags/{key}/evaluate` — no other code in the consuming module changes. Resolution is fail-open: if no flag record exists, `is_enabled()` returns `True`. See [ADR-018: Database-Backed Feature Flag System](../../docs/design/adr/018-feature-flag-system.md) for resolution semantics and the evaluate endpoint design. Seed the flag key in `seeds/all.sql` with `enabled = true` so the system behaves normally out of the box.

## Commit Protocol

Each step that produces code or files is a **separate commit**. Do not begin the next step until the current step's commit is approved and executed by the human.

To close a step:
1. Run `make lint && make test && make coverage && make security` — all must pass.
2. Stage the changes and output `git diff --staged`.
3. Propose a commit message.
4. **Wait for explicit human approval before executing `git commit`.**

**Commit message style:** Write a single summary line. Add a body only when it carries genuine value — a non-obvious rationale, a constraint that isn't self-evident from the diff, or a trade-off worth preserving. Never list files or restate what the diff already shows.

---

## Implementation Steps

Follow these steps in order. Complete and commit each one before moving to the next.

### Step 0 — Functional Specification Review

Before writing any implementation code, ensure the functional specification is complete and review it against the corresponding API contract.

**Step 0a — Ensure a functional spec exists and is specified**

If the human has not provided a functional spec file path, ask for it:

> Which functional spec doc covers this feature? Please provide the path relative to the workspace root (e.g., `docs/specs/functional/feature-flags/FF-01-set-feature-flag.md`).

Once you have the path:
1. Read the functional spec file in full.
2. Verify it follows the mandatory format documented in [Writing Functional Specifications](../../docs/guidelines/functional-specification.md):
   - Title with "IMPORTANT: This is a living document, specs are subject to change."
   - User Story in the given–want–benefit format
   - Constraints section (Authorization, Input, Data, Behavior)
   - BDD Acceptance Criteria with at least one happy path, one auth failure, one validation failure, and one business-rule failure
   - Use Cases (Happy Path and Sad Paths) with numbered steps and error codes
   - API Contract reference(s) linking to `docs/design/api-contracts/<domain>/`

If the spec is incomplete or malformed, update it to include the missing sections according to the guidelines and what makes the most sense for the feature.

**Step 0b — Review the functional spec and API contract for consistency**

Once a complete functional spec exists:

1. Extract the list of all error codes mentioned in the spec's Use Cases (e.g., `USER_NOT_FOUND`, `VALIDATION_ERROR`).
2. For each endpoint referenced in the spec's "API Contract" section, read the corresponding API contract file (`docs/design/api-contracts/<domain>/*.md`).
3. Cross-check the following to ensure the spec and contract are consistent:
   - **Constraints match response details:** Is every constraint from the spec reflected in a validation response (`422`) or business-rule failure (`400`/`409`) in the contract?
   - **Error codes match:** Does every error code in the spec's sad paths appear in the contract's failure responses?
   - **Acceptance criteria map to scenarios:** Can each BDD scenario be mapped to an endpoint and one or more response codes?
   - **Success status code matches intent:** Does the happy path response status (e.g., `200`, `201`, `202`) match the operation (read, create, async task)?
   - **Authorization responses are complete:** Do the contract's `401` and `403` failures match the spec's Authorization Constraints?

If inconsistencies are found, fix them (updating the docs) according to what makes the most sense for the feature, so the human can review them together with the spec and contract before implementation begins. For example, if the spec has a validation constraint that is not reflected in the contract, add a `422` response with the appropriate error code to the contract. If the spec has a sad path scenario that is not reflected in the contract, add the corresponding failure response to the contract. If the contract has a `403` response but the spec does not mention any authorization constraints, add the relevant constraints to the spec.

**Step 0c — Add missing constraints, acceptance criteria, or response documentation**

If the review uncovers gaps (e.g., missing error code, missing scenario, missing constraint), update either the spec or the contract according to what makes the most sense for the feature.For example, if the spec has a validation constraint that is not reflected in the contract, add a `422` response with the appropriate error code to the contract. If the spec has a sad path scenario that is not reflected in the contract, add the corresponding failure response to the contract.

---

### Step 1 — `schemas.py`: Pydantic schemas

Add or extend `<Entity>Create` (POST body), `<Entity>Update` (PATCH body, all-optional fields), and `<Entity>Out` (response) as needed for this feature. `<Entity>Out` must set `model_config = {"from_attributes": True}`. Add `Paginated<Entity>Out` with `items`, `total`, `page`, `page_size` fields if this feature includes a listing endpoint.

**Schema validators:** For every ORM column constraint that cannot be expressed by Pydantic's built-in field arguments (`gt`, `ge`, `min_length`, `pattern`, etc.), add a `@field_validator` to enforce the constraint at the schema level before the data reaches the service. Common cases:

| ORM column type | Validator to add |
| --- | --- |
| `Numeric(scale=N)` | Reject values with more than N decimal places |
| `String` with domain-specific rules | Reject values outside the allowed set (or use `Literal` / `Enum`) |
| Cross-field invariant | `@model_validator(mode="after")` |

Example for a `Numeric(precision=12, scale=2)` column:

```python
from pydantic import field_validator

@field_validator("amount")
@classmethod
def amount_scale_must_not_exceed_2(cls, v: Decimal) -> Decimal:
    if v.as_tuple().exponent < -2:
        raise ValueError("Amount must have at most 2 decimal places.")
    return v
```

Test every `@field_validator` in a dedicated `test_{module}_schemas.py` file. See `docs/guidelines/unit-testing.md` §8a for the pattern.

### Step 2 — `exceptions.py` and `errors.py`: domain exceptions and error codes

Add one exception class per failure mode introduced by this feature to `exceptions.py`. Each exception must carry context as instance attributes (e.g., `self.merchant_id = merchant_id`). Add corresponding `ErrorCode` string enum entries to `errors.py`.

### Step 3 — `policies.py`: business rule functions

One pure function per business rule introduced by this feature. Each function raises the appropriate domain exception on violation and returns `None` on success. No DB access, no HTTP knowledge, no side effects.

### Step 4 — `repositories.py`: data access layer

Add the query methods needed by this feature to `<Entity>RepositoryABC` (abstract) and `<Entity>Repository` (SQLAlchemy). Repositories only query the DB — no business logic.

**New modules use `AsyncSession` (see [ADR 010: Async Database Layer](../../docs/design/adr/010-async-database-layer.md)).** All repository methods are `async def` and use SQLAlchemy 2.0 `select()` statements:

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

async def get_by_id(self, db: AsyncSession, entity_id: str) -> Entity | None:
    result = await db.execute(select(Entity).where(Entity.id == entity_id))
    return result.scalar_one_or_none()
```

Do **not** use the legacy `session.query()` API — it does not compose with `AsyncSession`.

**Dynamic filter lists:** When building a list of WHERE conditions to spread into `.where()`, annotate it as `list[ColumnElement[bool]]` using the public `ColumnElement` type imported from `sqlalchemy`. Avoid `_ColumnExpressionArgument` — it is a private alias that Pylance cannot fully resolve, causing `list[Unknown]` errors under strict type checking:

```python
from sqlalchemy import ColumnElement

conditions: list[ColumnElement[bool]] = []
if status is not None:
    conditions.append(Entity.status == status)
if conditions:
    stmt = stmt.where(*conditions)
```

### Step 4a — `clients/`: cross-module clients (only if this feature reads data owned by another module)

If this feature needs to read data from another module (e.g., look up a user, merchant, or offer), **do not** import that module's ORM models into the repository, policies, or service. Instead:

1. Create a `clients/` package inside the module (if it does not already exist).
2. Add one file per collaborating module (e.g., `clients/users.py`, `clients/merchants.py`). Each file contains:
   - A lightweight **DTO** (plain `@dataclass`) carrying only the fields this module needs from the foreign entity.
   - An abstract client class (`<Foreign>ClientABC`) and a concrete implementation (`<Foreign>Client`). The concrete class queries the shared DB directly using `AsyncSession` and returns DTOs — it never returns foreign ORM models.
3. Add a `clients/__init__.py` that re-exports all DTOs, ABCs, and concrete clients so the rest of the module imports from `app.<module>.clients` (not from sub-modules directly).
4. Inject the clients into the service via `__init__()`, just like the repository.
5. Update `composition.py` to instantiate and wire the clients.

This pattern isolates all cross-module coupling to the `clients/` package. If a collaborating module is extracted to a microservice, only its concrete client implementation changes; services, policies, and repositories remain untouched.

**When splitting `clients.py` into a `clients/` package during refactoring**, preserve every existing comment in the functions being moved — comments often document non-obvious trade-offs or deferred decisions and must not be lost.

```text
app/<module>/
  clients/
    __init__.py        ← re-exports all DTOs, ABCs, and concrete clients
    users.py           ← UserDTO, UsersClientABC, UsersClient
    merchants.py       ← MerchantDTO, MerchantsClientABC, MerchantsClient
    offers.py          ← OfferDTO, OffersClientABC, OffersClient
```

```python
# app/<module>/clients/users.py
from abc import ABC, abstractmethod
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.models import User  # ← only clients/ files may import foreign ORM models


@dataclass
class UserDTO:
    id: str
    active: bool


class UsersClientABC(ABC):
    @abstractmethod
    async def get_user_by_id(
        self, db: AsyncSession, user_id: str
    ) -> UserDTO | None:
        pass


class UsersClient(UsersClientABC):
    """Modular-monolith implementation — queries the shared DB directly.

    Replace with an HTTP client if the users module is extracted to a
    separate service.
    """

    async def get_user_by_id(
        self, db: AsyncSession, user_id: str
    ) -> UserDTO | None:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            return None
        return UserDTO(id=user.id, active=user.active)
```

```python
# app/<module>/clients/__init__.py
from app.<module>.clients.users import UserDTO, UsersClient, UsersClientABC
from app.<module>.clients.merchants import MerchantDTO, MerchantsClient, MerchantsClientABC

__all__ = [
    "UserDTO", "UsersClientABC", "UsersClient",
    "MerchantDTO", "MerchantsClientABC", "MerchantsClient",
]
```

Policy functions and services import from the package root, not from sub-modules:

```python
# ✅ Correct: import from clients package root
from app.<module>.clients import UserDTO, UsersClientABC

# ❌ Wrong: import from internal sub-module
from app.<module>.clients.users import UserDTO
```

```python
# policies.py uses DTOs
def enforce_user_active(user: UserDTO | None, user_id: str) -> None: ...

# services.py receives clients via __init__
class EntityService:
    def __init__(
        self,
        repository: EntityRepositoryABC,
        users_client: UsersClientABC,
        ...
    ): ...
```

### Step 5 — `services.py`: business logic orchestration

Add the method(s) for this feature to `<Entity>Service`. Orchestrate policy checks and repository calls. Raise domain exceptions on failures. Log `INFO` for successful state-mutating operations, `DEBUG` for expected negative paths. Do not log read-only operations.

**New modules use `async def` service methods (see ADR 010):**

```python
from sqlalchemy.ext.asyncio import AsyncSession

async def create_entity(self, data: dict, db: AsyncSession) -> Entity:
    ...
```

**Audit trail — required for critical operations (see ADR-015):**

If this feature performs a critical state-changing operation (purchase confirmation/rejection, cashback crediting, withdrawal processing, payout settlement, or any manual admin override), the service method must also call `AuditTrail.record(...)` after the operation succeeds:

```python
from app.core.audit import AuditActorType, AuditAction, AuditTrail

class EntityService:
    def __init__(
        self,
        entity_repository: EntityRepositoryABC,
        audit_trail: AuditTrail,
    ): ...

    async def perform_critical_op(
        self, entity_id: str, actor_id: str | None, db: AsyncSession
    ) -> Entity:
        entity = await self._do_the_work(entity_id, db)
        await self.audit_trail.record(
            db=db,
            actor_type=AuditActorType.SYSTEM,   # or ADMIN / USER
            actor_id=actor_id,                   # None for system jobs
            action=AuditAction.PURCHASE_CONFIRMED,
            resource_type="purchase",
            resource_id=entity.id,
            outcome="success",
            details={"amount": str(entity.amount)},
        )
        return entity
```

Place the `record()` call **after** the business operation succeeds. If the operation raises, no audit row is written — which accurately reflects the real outcome. The `AuditTrail` instance is injected via `__init__()` and wired in `composition.py` via `get_audit_trail`. Check `docs/specs/non-functional/10-logging-observability.md` for the full list of operations that require an audit row.

### Step 6 — `composition.py`: dependency wiring

Update `get_<entity>_service()` if new dependencies (e.g., a second repository or an external client) are required by this feature. No changes needed if the existing factory already covers it.

### Step 7 — `api.py` (or `api/`): HTTP router

Add one route handler per endpoint. Each handler: declares request/response schemas and status codes; resolves dependencies via `Depends()`; calls the service; catches each domain exception and converts it with the appropriate `core/errors/builders.py` factory; catches bare `Exception` last, logs at `ERROR`, and raises `internal_server_error()`. Never put business logic here.

**New modules use `async def` route handlers with `get_async_db` (see ADR 010):**

```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_db

@router.post("/entities/", status_code=status.HTTP_201_CREATED)
async def create_entity(
    data: EntityCreate,
    service: EntityService = Depends(get_entity_service),
    db: AsyncSession = Depends(get_async_db),
) -> EntityOut:
    ...
```

If `api.py` already exceeds ~200 lines or this feature introduces a clearly distinct endpoint group (e.g., public vs. admin), consult `docs/guidelines/code-organization.md` §3 and split into an `api/` package before adding new routes.

For list responses with nested items, use explicit `model_validate()` conversion:

```python
return Paginated<Entity>Out(
    items=[<Entity>Out.model_validate(item) for item in items],
    total=total,
    page=page,
    page_size=page_size,
)
```

### Step 8 — `http/<module>/`: manual HTTP smoke-test files

Create one `.http` file per new route inside `http/<module>/` at the project root (e.g., `http/purchases/create-purchase.http`). These files are testing artifacts and living documentation; they live outside the application source tree and are shared across the whole project.

Before writing the files, read `docs/guidelines/http-requests-file.md` in full — it documents every authoring convention in detail. A short summary of the required structure:

- **Variable block at the top:** `@baseUrl`, any resource ID variables, and `@adminToken` / `@userToken` placeholder variables (expired local-dev JWTs from seed data — never real credentials).
- **Helper login requests** immediately after the variable block, one per role exercised in the file, with a comment directing the developer to paste the returned token into the variable above.
- **One `###` block per distinct HTTP response** the endpoint can return, titled `### <status> – <Happy/Sad path>: <description>` and followed by at least one `#` comment explaining the scenario, the expected outcome, and any seed-data dependency.
- **Coverage order:** happy paths first, then 401 → 403 → 422 (validation) → 400/409 (business rules) → 404.
- **Never commit real tokens, API keys, or production credentials.**

See `docs/guidelines/http-requests-file.md` for the full coverage checklist, naming rules, and an annotated example.

### Step 9 — Alembic migration (only if model changed)

If this feature required changes to the ORM model (new columns, constraints, etc.), run `alembic revision --autogenerate -m "<describe change>"`. Inspect the generated file under `alembic/versions/`. Run `alembic upgrade head`, then `alembic downgrade -1` followed by `alembic upgrade head` to verify the round-trip. Skip this step entirely if no model changes were made.

### Step 10 — Update `seeds/all.sql`

Add realistic seed rows to exercise this feature. Use valid UUIDs. Add enough rows to cover pagination (at least `page_size + 1`) if a listing endpoint is included. Seed both states for any status/flag fields. Group inserts with short SQL comments.

### Step 11 — Write tests

Once all `.http` smoke tests are passing, use `write-tests.prompt.md` to write the test suite for this feature. Tests are a separate commit.

**Testing concurrent/background infrastructure (schedulers, brokers):** Never assert on private attributes (`_registered`, `_running`, etc.) or call internal methods (`_run_loop`) directly — this couples tests to implementation details, breaks on refactors, and triggers linter warnings. Instead, observe only public-contract behaviour:

If for some reason you need to take shortcuts and assert on internal state, add a comment justifying the deviation from best practices and explaining why it is necessary for testing this feature. This ensures future maintainers understand the rationale and can make informed decisions when refactoring.

### Step 12 — Quality gates and commit

Run `make lint && make test && make coverage && make security`. Fix all failures. Run `make coverage` and confirm the grade is at least ✅ Approved. Then stage all changes from this step, propose a commit message, and wait for human approval before executing `git commit`.
