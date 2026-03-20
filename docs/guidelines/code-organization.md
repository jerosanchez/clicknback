# Code Organization and File Size Guidelines

This document is the authoritative reference for how to organize code within a module as it grows. It covers when to keep everything in a single file, when to split, how to split each layer, and how test files mirror those decisions.

---

## 1. The Default: One File Per Layer

Every module starts with one file per layer. This is the default and should be maintained as long as files remain at a **readable size** — typically under **200 lines**.

```text
app/<module>/
  __init__.py
  models.py
  schemas.py
  repositories.py
  services.py
  policies.py
  exceptions.py
  errors.py
  composition.py
  api.py          ← or api/ if split (see §3)
```

The corresponding tests mirror this:

```text
tests/<module>/
  test_<module>_api.py
  test_<module>_services.py
  test_<module>_policies.py
```

Do not split preemptively. Premature splitting adds indirection without benefit. Start flat and split only when a file becomes difficult to navigate.

---

## 2. When to Split

Split a file when it reaches a threshold where human reviewers struggle to navigate it. The practical guide:

| File | Split threshold | Split strategy |
| --- | --- | --- |
| `api.py` | ~200 lines, or distinct endpoint groups with clearly different concerns (e.g., role) | Sub-router package (see §3) |
| `services.py` | ~200 lines, or distinct operation types (creation, lifecycle, callbacks) | Service sub-modules (see §4) |
| `schemas.py` | ~150 lines, or many enum types | Schema sub-modules (see §5) |
| `repositories.py` | ~150 lines, or clearly separable query types | Repository sub-modules (see §5) |

These are guidelines, not hard rules. A 250-line file with good sectioning and a clear narrative may be more readable than three 80-line files with blurry responsibilities. Use judgment.

---

## 3. Splitting the API Layer: Sub-Router Package

When `api.py` grows beyond the threshold or has distinct endpoint groups (e.g., admin vs. public endpoints), replace the single file with a package.

### Directory Structure

```text
app/<module>/
  api/
    __init__.py       ← assembles and exports routers
    admin.py          ← endpoints requiring admin authentication
    public.py         ← endpoints accessible to regular users
```

Each sub-module defines its own `APIRouter` with the same prefix as before:

```python
# app/offers/api/admin.py
router = APIRouter(prefix="/offers", tags=["offers"])

@router.post("/", ...)
def create_offer(...): ...
```

The `__init__.py` assembles and re-exports them:

```python
# app/offers/api/__init__.py
from app.offers.api import admin, public

admin_router = admin.router
public_router = public.router

__all__ = ["admin_router", "public_router"]
```

### Wiring in `main.py`

Replace the single router include with one per sub-router:

```python
# Before
from app.offers import api as offers_api
app.include_router(offers_api.router, prefix="/api/v1")

# After
from app.offers.api import admin_router as offers_admin_router
from app.offers.api import public_router as offers_public_router

app.include_router(offers_admin_router, prefix="/api/v1")
app.include_router(offers_public_router, prefix="/api/v1")
```

### Splitting Criteria for API Sub-Modules

The most natural split boundary for the API layer is **access role**:

- **`admin.py`** — endpoints that require `get_current_admin_user`. All write operations (create, update, deactivate) typically live here, as well as admin-only listings with full details.
- **`public.py`** — endpoints that require only `get_current_user`, or that are fully public. Consumer-facing reads live here.

If role is not a useful boundary (e.g., all endpoints require admin), split by **resource area** instead:

```text
api/
  __init__.py
  lifecycle.py    ← create, activate, deactivate
  listings.py     ← GET collections with filters
  details.py      ← GET individual resource + sub-resources
```

### The Real-World Example: `offers`

Before splitting, `app/offers/api.py` was 328 lines covering three endpoints across two roles. After:

```text
app/offers/api/
  __init__.py      ← exports admin_router, public_router
  admin.py         ← 260 lines: POST /offers, GET /offers (admin listing)
  public.py        ←  86 lines: GET /offers/active
```

The split is immediately legible: `admin.py` is the admin surface, `public.py` is what end-users see.

---

## 4. Splitting the Service Layer

When `services.py` grows beyond the threshold, extract logical sub-concerns into dedicated modules under a `services/` package:

```text
app/<module>/
  services/
    __init__.py       ← re-exports the main service class
    creation.py
    lifecycle.py
    calculations.py
```

The main `<Entity>Service` class can remain in `services/__init__.py` or in a `services/service.py` and import helper functions or sub-services from sibling modules.

The public interface does not change: `composition.py` still imports and instantiates `<Entity>Service` exactly as before. Only the internal file layout changes.

---

## 5. Splitting Schemas or Repositories

For `schemas.py` or `repositories.py`, the pattern is the same: replace the file with a package and re-export from `__init__.py` so that all existing imports continue to work unchanged.

```text
app/<module>/
  schemas/
    __init__.py     ← re-exports everything: OfferCreate, OfferOut, ...
    base.py         ← shared base schemas
    listings.py     ← paginated output schemas
    enums.py        ← all Enum types
```

```python
# schemas/__init__.py
from app.offers.schemas.base import OfferCreate, OfferOut
from app.offers.schemas.listings import PaginatedOffersOut, PaginatedActiveOffersOut
from app.offers.schemas.enums import CashbackTypeEnum

__all__ = [
    "OfferCreate", "OfferOut",
    "PaginatedOffersOut", "PaginatedActiveOffersOut",
    "CashbackTypeEnum",
]
```

This is the key rule: **existing imports must continue to work**. Code in other modules that imports `from app.offers.schemas import OfferOut` must not need to change when you reorganize internals.

---

## 6. Test File Naming

Test files mirror the source file they exercise. When a source file is split into a package, the corresponding test files are named after the sub-modules:

| Source file | Test file |
| --- | --- |
| `app/offers/api.py` | `tests/offers/test_offers_api.py` |
| `app/offers/api/admin.py` | `tests/offers/test_offers_admin_api.py` |
| `app/offers/api/public.py` | `tests/offers/test_offers_public_api.py` |
| `app/offers/services.py` | `tests/offers/test_offers_services.py` |
| `app/offers/services/creation.py` | `tests/offers/test_offers_creation_service.py` |

The naming pattern is always: `test_<module>_<sub-module>_<layer>.py`

Each test file is self-contained: its fixtures, helpers, and test functions cover exactly the source file it mirrors. **Do not share fixtures between API test files via `conftest.py` unless they are truly module-wide** (e.g., the `offer_factory` that all offer tests use).

---

## 7. Maintaining Module Decoupling

These organizational changes are internal to a module. The contracts a module exposes to the outside world — imports in `main.py`, dependency factories in `composition.py`, imports in other modules' API files — do not change when you reorganize internals.

This is the design property that keeps modules ready for extraction into independent services: **each module's public surface is its `composition.py` factories and, if needed, a `clients/` package**. Everything else is private implementation detail.

When splitting, always verify that no import path crosses module boundaries at a level deeper than the module root:

```python
# ✅ Correct: import from module root
from app.offers.schemas import OfferOut

# ❌ Wrong: import from internal sub-module
from app.offers.schemas.listings import OfferOut
```

External modules import from the module root. The module root re-exports from its internal structure via `__init__.py`.

---

## 8. Cross-Module Dependencies: The `clients/` Package

When a module needs to read data from another module, it does not import the foreign module's service or repository directly. Instead, it defines its own **`clients/` package** with abstractions that encapsulate the foreign dependency.

This pattern serves two purposes:

1. **Explicit intent** — Document precisely what the consuming module needs from foreign modules.
2. **Microservice readiness** — Ensure that if a foreign module is extracted into a separate service, only the client implementation changes; the consuming module's service logic remains unaffected.

### Structure and Pattern

```text
app/<module>/
  clients/
    __init__.py        ← Re-exports all DTOs, ABCs, and concrete implementations
    <foreign>.py       ← One file per collaborating module (e.g., merchants.py, offers.py)
```

Each client file defines:

1. **DTO (Data Transfer Object)** – a simple dataclass containing only the fields the consuming module needs from the foreign entity.
2. **`<Foreign>ClientABC`** – an abstract interface defining methods the consuming module requires.
3. **`<Foreign>Client`** – a concrete in-process implementation querying the shared database.

### Example: Purchases Module Reading from Merchants

In `app/purchases/clients/merchants.py`:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

@dataclass
class MerchantDTO:
    id: str
    active: bool
    name: str

class MerchantsClientABC(ABC):
    @abstractmethod
    async def get_merchant_by_id(
        self, db: AsyncSession, merchant_id: str
    ) -> MerchantDTO | None:
        pass

class MerchantsClient(MerchantsClientABC):
    """In-process implementation for modular monolith.

    If merchants is extracted to a separate service, replace this with
    an HTTP client that calls the merchants service's evaluate endpoint.
    """

    async def get_merchant_by_id(
        self, db: AsyncSession, merchant_id: str
    ) -> MerchantDTO | None:
        result = await db.execute(
            select(Merchant).where(Merchant.id == merchant_id)
        )
        merchant = result.scalar_one_or_none()
        if merchant is None:
            return None
        return MerchantDTO(id=merchant.id, active=merchant.active, name=merchant.name)
```

The `clients/__init__.py` re-exports these for convenient importing:

```python
from app.purchases.clients.merchants import (
    MerchantDTO,
    MerchantsClient,
    MerchantsClientABC,
)

__all__ = ["MerchantDTO", "MerchantsClient", "MerchantsClientABC"]
```

### Using a Client in Services

The client is injected into the consuming module's service, just like a repository:

```python
# In app/purchases/services.py
class PurchaseService:
    def __init__(
        self,
        purchase_repo: PurchaseRepositoryABC,
        merchants_client: MerchantsClientABC,
    ):
        self.purchase_repo = purchase_repo
        self.merchants_client = merchants_client

    async def ingest_purchase(
        self, data: dict, db: AsyncSession
    ) -> Purchase:
        # Fetch merchant data via the client
        merchant = await self.merchants_client.get_merchant_by_id(
            db, data["merchant_id"]
        )
        if merchant is None:
            raise MerchantNotFoundError()

        # Use merchant data for business logic
        ...
```

Wiring the client in `composition.py`:

```python
def get_purchase_service(db: AsyncSession = Depends(get_async_db)) -> PurchaseService:
    merchant_client = MerchantsClient()
    repo = PurchaseRepository()
    return PurchaseService(repo, merchant_client)
```

---

## 9. Background Jobs: The `jobs/` Package

When a module runs background jobs (scheduled tasks that process items asynchronously), job logic lives in a `jobs/` sub-package that mirrors the module structure but focuses on job orchestration and task execution.

### Structure

```text
app/<module>/
  jobs/
    __init__.py
    <job_name>/
      __init__.py
      dispatcher.py     ← Scheduler tick entry point (fan-out logic)
      runner.py         ← Per-item task execution
      strategy.py       ← Swappable external-system integration
```

For example, the purchases module verification job:

```text
app/purchases/
  jobs/
    __init__.py
    verify_purchases/
      __init__.py
      dispatcher.py     ← Runs on scheduler tick; queries pending purchases; spawns tasks
      runner.py         ← Processes a single purchase verification attempt
      strategy.py       ← Encapsulates bank reconciliation simulation
```

### Dispatcher, Runner, and Strategy Pattern

**Dispatcher** (tick entry point):

- Runs once per scheduler interval (e.g., every 60 seconds).
- Queries for items in a "work-pending" state.
- Spawns one independent `asyncio.Task` per item via `asyncio.create_task()`.
- Does not wait for tasks to complete (fire-and-forget).

**Runner** (per-item task):

- Receives one item and its context (retry count, etc.).
- Owns its own database session and retry lifecycle.
- Calls the strategy to perform external-system integration (e.g., bank reconciliation).
- Updates the item's state in the DB and handles retries.

**Strategy** (pluggable external integration):

- An abstract interface defining how to interact with external systems.
- Allows testing the runner and dispatcher logic without real external calls.
- Can be swapped at runtime (e.g., from a mock strategy to a real one for integration tests).

### Example: Purchase Verification Job

See [ADR 016: Background Job Architecture Pattern](../../design/adr/016-background-job-architecture-pattern.md) for the full architecture and rationale.

---

## 10. Core Infrastructure Module: `app/core/`

The `app/core/` module is not a feature module like `users` or `purchases`. Instead, it houses **shared, cross-cutting infrastructure** that many modules depend on. It is organized into logical sub-packages:

**Structure**:

```text
app/core/
  __init__.py
  audit/
    __init__.py
    models.py         ← Audit log ORM model
    repositories.py   ← Audit log data access
    services.py       ← Audit trail recording service
  broker.py           ← In-process pub/sub message broker
  config.py           ← Settings and environment configuration
  current_user.py     ← JWT extraction and user context dependency
  database.py         ← Database session factories (sync and async)
  errors/
    __init__.py
    builders.py       ← Error response construction logic
    codes.py          ← Shared ErrorCode enums
    handlers.py       ← FastAPI exception handlers
  events/
    __init__.py
    purchase_events.py ← Domain event definitions
  health.py           ← Health check endpoints and logic
  logging.py          ← Structured logging configuration
  scheduler.py        ← Background job scheduler (cron-like ticks)
```

### Purpose of Each Component

| Component | Purpose |
| --- | --- |
| `audit/` | Persistent append-only log of critical operations (purchases confirmed, cashback credited, payouts, admin actions). Enables auditability and forensic analysis independent of application logs. See [ADR 015](../../design/adr/015-persistent-audit-trail.md). |
| `broker.py` | In-process pub/sub for decoupled communication between modules (e.g., background jobs publishing purchase-confirmed events). See [ADR 014](../../design/adr/014-in-process-broker-and-scheduler.md). |
| `config.py` | Centralized settings management using Pydantic. Environment-driven configuration (dev, testing, production). |
| `current_user.py` | FastAPI dependency that extracts JWT from request header, validates it, and injects user context. Reused by all auth-protected routes. |
| `database.py` | Session factory functions (`get_db()`, `get_async_db()`) for both sync and async contexts. Manages connection pooling and transaction lifecycle. |
| `errors/` | Centralized error code definitions and HTTP error response builders. Ensures all modules return consistent error shapes. See [ADR 009 (error handling strategy)](../../design/error-handling-strategy.md). |
| `events/` | Domain event definitions (e.g., `PurchaseConfirmedEvent`, `CashbackCreditedEvent`). Published to the broker for consumption by background jobs or other modules. |
| `health.py` | Health check endpoint and readiness probes (DB connectivity, etc.). Used for monitoring and deployment orchestration. |
| `logging.py` | Structured logging setup using Python's native logger. Ensures consistent log format and level across modules. |
| `scheduler.py` | Lightweight scheduler that runs dispatcher functions on a fixed interval. Powers background job processing. See [ADR 014](../../design/adr/014-in-process-broker-and-scheduler.md). |

### Using Core Infrastructure

Modules import from `app.core` as needed:

```python
from app.core.config import settings
from app.core.database import AsyncSession, Depends, get_async_db
from app.core.audit import AuditService
from app.core.broker import Broker
from app.core.current_user import get_current_user
```

The rule: **import from `app.core` directly; never import sub-components from `app.core.errors.builders` or `app.core.audit.models` in other modules.** The `app/core/` package re-exports public components from its `__init__.py` to maintain a stable contract.

---

## 11. HTTP Test Files: The `/http` Folder

The `/http` folder contains **smoke test files** organized by domain, using the VS Code REST Client extension format. These are not automated tests but manual, step-by-step request workflows that enable interactive exploration and verification of the API.

**Structure**:

```text
/http/
  auth/
    login.http
  merchants/
    create-merchant.http
    activate-merchant.http
    list-merchants.http
  offers/
    create-offer.http
    list-offers.http
    get-active-offers.http
    get-offer-details.http
    set-offer-status.http
  purchases/
    ingest-purchase.http
    get-purchase-details.http
    list-all-purchases.http
  users/
    create-user.http
```

### Purpose and Content

Each `.http` file contains:

1. **Setup section** – base URL, token variables, and common headers.
2. **Happy-path request** – the normal, expected-to-succeed flow.
3. **Sad-path requests** – edge cases, validation failures, authorization errors, etc.
4. **Comments** – explain what each request is testing and what the expected response should be.

Example (`http/auth/login.http`):

```http
@baseUrl = http://localhost:8001/api/v1

### 200 – Happy path: valid credentials
POST {{baseUrl}}/auth/login
Content-Type: application/json

{
  "email": "alice@clicknback.com",
  "password": "Str0ng!Pass"
}

### 401 – Sad path: wrong password
POST {{baseUrl}}/auth/login
Content-Type: application/json

{
  "email": "alice@clicknback.com",
  "password": "wrong"
}
```

### Using HTTP Files

1. Install the [VS Code REST Client](https://marketplace.visualstudio.com/items?itemName=humao.rest-client) extension.
2. Open an `.http` file.
3. Click the `Send Request` link above any request block to execute it.
4. View the response in the side panel.

These files serve as:

- **Documentation** – they show how to use the API by example.
- **Quick validation** – run requests without writing test code.
- **Integration checks** – verify the system end-to-end before running automated tests.
- **Onboarding** – new developers can follow the workflows step-by-step.
