---
name: architecture
type: rule
description: Modular monolith structure, layering patterns, and cross-module abstractions
---

# ARCHITECTURE

ClickNBack uses a **modular monolith** — one deployable unit with well-bounded domain modules. This section covers module anatomy, strict layering, cross-module clients, and Unit of Work patterns.

## Monolith Structure

- **Single codebase, single deployment**: Everything in `app/`, one binary, one database.
- **Well-bounded modules**: Each domain (users, merchants, purchases, etc.) is a self-contained package under `app/<module>/`.
- **Explicit dependencies**: Cross-module access is **only through client abstractions** in `clients/` package — never direct imports of another module's models or repositories.
- **Composition root**: `app/main.py` wires all routers, schedules background jobs, registers global handlers.
- **Core infrastructure**: `app/core/` holds shared infrastructure: config, DB sessions, auth, error builders, logging, event broker, scheduler.

## Module Anatomy

Every module follows this structure:

```text
app/<module>/
  __init__.py          ← Empty; marks the package
  models.py            ← SQLAlchemy ORM models (DB tables)
  schemas.py           ← Pydantic schemas (API input/output)
  repositories.py      ← DB access layer (ABC + concrete impl)
  services.py          ← Business logic orchestration
  policies.py          ← Pure business rule enforcement
  exceptions.py        ← Domain-specific exceptions
  errors.py            ← Module-specific ErrorCode enum
  composition.py       ← Dependency wiring (FastAPI Depends)
  api.py               ← FastAPI router; or api/ package if split
  _helpers.py          ← (Optional) shared helper functions
  clients/             ← (Optional) cross-module abstractions
    __init__.py        ← Re-exports all DTOs, ABCs, clients
    <foreign>.py       ← One per collaborating module
  jobs/                ← (Optional) background jobs
    __init__.py
    <job_name>/        ← One folder per job
```

## Strict Layering

Services, policies, and repositories follow a clear dependency hierarchy:

```
API (HTTP Boundary)
  ↓
Services (Business Logic Orchestration)
  ↓
Policies (Pure Business Rules) + Repositories (DB Access)
  ↓
Database
```

### Layer Boundaries

- **api.py**: HTTP concerns only. Translates HTTP requests to service calls; translates responses/exceptions to HTTP. No business logic.
- **services.py**: Business logic orchestration. Calls policies (before DB) and repositories; publishes events; handles transactions via Unit of Work.
- **policies.py**: Pure functions enforcing exactly one business rule each. Raise domain exceptions on violation; no side effects or I/O.
- **repositories.py**: DB access only. No business logic, no HTTP knowledge. Flush, never commit.
- **models.py**: SQLAlchemy ORM models. Single source of truth for table structure.
- **exceptions.py**: Domain-specific exceptions with context attributes. No HTTP concepts.
- **errors.py**: Module-scoped `ErrorCode` string enum for HTTP error codes.

### Critical Rules

- ❌ **Never**: Place business logic in `api.py`.
- ❌ **Never**: Raise `HTTPException` in services or repositories.
- ❌ **Never**: Import ORM models from other modules into services/policies/repos — use `clients/` and DTOs.
- ❌ **Never**: Call `db.commit()` in repositories — use `await db.flush()` only.
- ✅ **Always**: Repositories flush with `await db.flush()`.
- ✅ **Always**: Transactions are closed with `uow.commit()` at the service level.

## Unit of Work Pattern

- Service methods that **commit** accept `uow: UnitOfWorkABC` and call `await uow.commit()` as the single transaction boundary.
- Read-only service methods accept `db: AsyncSession` directly (no transaction needed).
- `uow.session` is the `AsyncSession` passed to repositories inside a write operation.
- See `app/core/unit_of_work.py` and [ADR-021](../../docs/design/adr/021-unit-of-work-pattern.md).

## Cross-Module Clients

When a module reads or writes data owned by another module:

1. **Create `clients/<foreign>.py`** with:
   - DTO `@dataclass` (defines cross-module data contract)
   - Abstract interface `<Foreign>ClientABC` 
   - Concrete `<Foreign>Client` (queries the shared DB, returns DTOs)
   
2. **Share DB read access only**: Clients query the same DB but return DTOs, never foreign ORM models.

3. **Inject clients into services** via `__init__()` and wire in `composition.py`.

4. **Re-export from `clients/__init__.py`**: Never import from sub-modules; always from package root.

### Example: Purchase Service Reading Merchant Data

```python
# app/purchases/clients/merchants.py
@dataclass
class MerchantDTO:
    id: str
    name: str
    active: bool

class MerchantsClientABC(ABC):
    async def get_merchant(self, db: AsyncSession, merchant_id: str) -> MerchantDTO | None:
        ...

class MerchantsClient(MerchantsClientABC):
    async def get_merchant(self, db: AsyncSession, merchant_id: str) -> MerchantDTO | None:
        # Query merchants DB, return DTO
        result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
        merchant = result.scalar_one_or_none()
        if not merchant:
            return None
        return MerchantDTO(id=merchant.id, name=merchant.name, active=merchant.active)
```

---
