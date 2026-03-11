# Prompt: Implement a New Feature

Use this prompt to implement a single feature (one or more related endpoints) inside an **existing module**. If the module does not exist yet, scaffold it first with `create-module.prompt.md`, then return here.

## Context Files (Read First)

Before writing any code, read the following files in full:

- `docs/agents/project-context.md` — domain model and system purpose
- `docs/agents/feature-guide.md` — module anatomy, layer responsibilities, coding conventions
- `docs/agents/code-organization.md` — when and how to split large files; naming conventions for split packages and their tests
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
- Do not import ORM models from other modules into `repositories.py`, `policies.py`, or `services.py` — use a `clients/` package and DTOs instead (see Step 4a).
- **Infrastructure/support modules** (broker, scheduler, token provider, etc.) must keep the ABC and the default in-memory/simple implementation in the **same file**, placed directly under `app/core/` (e.g., `app/core/broker.py`, `app/core/scheduler.py`). Do not split the interface and its default implementation into separate files (`broker_abc.py` + `broker.py`) — that fragmentation adds no value at this scale and forces unnecessary cross-file navigation.
- Event or message payload definitions that are domain-specific belong in a sub-package (e.g., `app/core/events/`) and are kept separate from the infrastructure files. See `app/core/broker.py`, `app/core/scheduler.py`, and `app/auth/token_provider.py` as reference examples.
- Critical state-changing operations (purchase confirmation/rejection, cashback crediting, withdrawal processing, payout settlement, admin overrides) **must** call `AuditTrail.record(...)` in the service method, after the operation succeeds. Inject `AuditTrail` via `__init__()` and wire it in `composition.py`. See `docs/agents/feature-guide.md` §2 (`core/audit.py`) and ADR-015.

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

Test every `@field_validator` in a dedicated `test_{module}_schemas.py` file. See `docs/agents/testing-guidelines.md` §8a for the pattern.

### Step 2 — `exceptions.py` and `errors.py`: domain exceptions and error codes

Add one exception class per failure mode introduced by this feature to `exceptions.py`. Each exception must carry context as instance attributes (e.g., `self.merchant_id = merchant_id`). Add corresponding `ErrorCode` string enum entries to `errors.py`.

### Step 3 — `policies.py`: business rule functions

One pure function per business rule introduced by this feature. Each function raises the appropriate domain exception on violation and returns `None` on success. No DB access, no HTTP knowledge, no side effects.

### Step 4 — `repositories.py`: data access layer

Add the query methods needed by this feature to `<Entity>RepositoryABC` (abstract) and `<Entity>Repository` (SQLAlchemy). Repositories only query the DB — no business logic.

**New modules use `AsyncSession` (see ADR 010).** All repository methods are `async def` and use SQLAlchemy 2.0 `select()` statements:

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

If `api.py` already exceeds ~200 lines or this feature introduces a clearly distinct endpoint group (e.g., public vs. admin), consult `docs/agents/code-organization.md` §3 and split into an `api/` package before adding new routes.

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

**Testing concurrent/background infrastructure (schedulers, brokers):** Never assert on private attributes (`_registered`, `_running`, etc.) or call internal methods (`_run_loop`) directly — this couples tests to implementation details, breaks on refactors, and triggers linter warnings. Instead, observe only public-contract behaviour:

If for some reason you need to take shortcuts and assert on internal state, add a comment justifying the deviation from best practices and explaining why it is necessary for testing this feature. This ensures future maintainers understand the rationale and can make informed decisions when refactoring.

### Step 12 — Quality gates and commit

Run `make lint && make test && make coverage && make security`. Fix all failures. Run `make coverage` and confirm the grade is at least ✅ Approved. Then stage all changes from this step, propose a commit message, and wait for human approval before executing `git commit`.
