# ADR 010: Async-First Database Layer with asyncpg

## Status

Accepted

## Context

ClickNBack's API is built on FastAPI, an ASGI framework that fully supports Python's `async`/`await` model. However, the original database layer was implemented with synchronous SQLAlchemy (`create_engine`, `Session`, `sessionmaker`) backed by `psycopg2`. This means that even though the HTTP server is non-blocking, every database call blocks the event loop's thread for the duration of the query.

For a cashback platform with concurrent purchase ingestion, wallet updates, and cashback confirmations, this is a correctness risk as much as a performance one: blocked I/O under concurrency is the source of latency spikes, event-loop starvation, and subtle ordering bugs when multiple requests race to update the same wallet.

The question is: should we migrate to a fully async database stack, and if so, how should the transition be managed in a codebase that already has synchronous modules?

### Option 1: Keep Synchronous SQLAlchemy (`psycopg2` + `Session`)

```python
def create_merchant(self, db: Session, merchant: Merchant) -> Merchant:
    db.add(merchant)
    db.commit()
    db.refresh(merchant)
    return merchant

@router.post("/merchants/")
def create_merchant(
    data: MerchantCreate,
    db: Session = Depends(get_db),
) -> MerchantOut:
    return merchant_service.create_merchant(db, data.model_dump())
```

- ✅ Simpler mental model for contributors less familiar with async Python
- ✅ No blocking concern for low-concurrency workloads in development
- ❌ Blocks the event loop on every DB call — even a 5 ms query ties up the thread
- ❌ Defeats the purpose of running under an ASGI server (Uvicorn)
- ❌ Synchronous repositories cannot be awaited in async route handlers without thread pool offloading
- ❌ No path to concurrency-correct wallet updates without explicit thread locking

### Option 2: Full Async Replace (Migrate All Modules at Once)

```python
async def create_merchant(self, db: AsyncSession, merchant: Merchant) -> Merchant:
    db.add(merchant)
    await db.commit()
    await db.refresh(merchant)
    return merchant

@router.post("/merchants/")
async def create_merchant(
    data: MerchantCreate,
    db: AsyncSession = Depends(get_async_db),
) -> MerchantOut:
    return await merchant_service.create_merchant(db, data.model_dump())
```

- ✅ Fully non-blocking end-to-end
- ✅ Consistent approach across all modules — no dual-path maintenance
- ❌ Large single migration affecting all existing modules simultaneously
- ❌ High risk of regressions if rushed; breaks all tests until fully migrated
- ⚠️ Acceptable as a future goal once existing modules are covered with sufficient integration tests

### Option 3: Dual-Path — Async for New Modules, Sync Preserved for Existing

```python
# New modules (purchases, wallets, payouts) — async all the way through
async def get_purchase_by_external_id(
    self, db: AsyncSession, external_id: str
) -> Purchase | None:
    result = await db.execute(
        select(Purchase).where(Purchase.external_id == external_id)
    )
    return result.scalar_one_or_none()

@router.post("/purchases/")
async def ingest_purchase(
    data: PurchaseCreate,
    db: AsyncSession = Depends(get_async_db),
) -> PurchaseOut:
    ...

# Existing modules — synchronous, unchanged until migrated
@router.post("/merchants/")
def create_merchant(
    data: MerchantCreate,
    db: Session = Depends(get_db),
) -> MerchantOut:
    ...
```

- ✅ Zero risk to existing functionality — modules are unchanged
- ✅ Async correctness for the financial core: purchases, wallets, and payouts
- ✅ Incremental migration path: each old module can be converted independently
- ✅ Both engines coexist in `core/database.py` with explicit, named factories
- ⚠️ Temporary dual-path adds a small mental overhead until migration is complete
- ⚠️ Requires discipline: new modules must always use the async path

## Decision

Adopt **Option 3** now, with **Option 2 as the target end state**.

Introduce a second, async database engine in `app/core/database.py`:

```python
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

_async_database_url = settings.database_url.replace(
    "postgresql://", "postgresql+asyncpg://"
).replace("postgresql+psycopg2://", "postgresql+asyncpg://")

async_engine = create_async_engine(_async_database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,   # required: objects expire after commit in async context
)

async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session
```

The `asyncpg` driver replaces `psycopg2` for all new modules. It is a pure-Python async driver for PostgreSQL with no C extension dependency and native support for SQLAlchemy's `AsyncSession`.

**All new modules must use the async stack.** Repositories accept `AsyncSession`, service methods are `async def`, and route handlers use `async def` with `Depends(get_async_db)`:

```python
# repositories.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

class PurchaseRepository(PurchaseRepositoryABC):
    async def get_by_external_id(
        self, db: AsyncSession, external_id: str
    ) -> Purchase | None:
        result = await db.execute(
            select(Purchase).where(Purchase.external_id == external_id)
        )
        return result.scalar_one_or_none()

# services.py
class PurchaseService:
    async def ingest_purchase(
        self, data: dict, db: AsyncSession
    ) -> Purchase:
        ...

# api.py
@router.post("/purchases/")
async def ingest_purchase(
    data: PurchaseCreate,
    service: PurchaseService = Depends(get_purchase_service),
    db: AsyncSession = Depends(get_async_db),
) -> PurchaseOut:
    ...
```

Existing modules (`users`, `merchants`, `offers`, `auth`) continue using the synchronous `Session` and `get_db()` dependency. They are migrated to the async path as a separate, incremental effort.

Alembic migrations remain synchronous — they use `psycopg2` and `engine_from_config`, which does not require asyncpg. No changes to `alembic/env.py` are needed.

Tests for async modules use `pytest-asyncio` with `@pytest.mark.asyncio` and `AsyncMock` or `create_autospec` on async repository methods.

## Consequences

- ✅ The financial core (purchases, cashback, wallets, payouts) is non-blocking end-to-end — no event-loop starvation under concurrent ingestion.
- ✅ `expire_on_commit=False` ensures ORM objects remain accessible after `commit()` without triggering implicit lazy loads — removing a common source of `MissingGreenlet` errors in async contexts.
- ✅ The dual-path is fully reversible: existing modules still work unchanged.
- ✅ Clear migration path: convert one module at a time, with full test coverage as the safety net.
- ✅ `asyncpg` is a mature, widely-used async PostgreSQL driver; no stability risk.
- ⚠️ Two database dependency factories (`get_db` and `get_async_db`) coexist until migration is complete. Contributors must use the correct one for their module — this is enforced by code review and documented in the feature guide.
- ⚠️ `asyncpg` does not support `psycopg2`-style `NOTIFY/LISTEN` patterns; this is not a concern for ClickNBack's current feature set.
- ⚠️ SQLAlchemy's `select()` API replaces the legacy `session.query()` style in async modules — contributors unfamiliar with SQLAlchemy 2.0 Core-style queries will need to learn the new pattern.

## Alternatives Considered

### `run_in_executor` wrapper (Option 1 variant)

Synchronous DB calls could be offloaded to a thread pool via `asyncio.run_in_executor`, preserving the sync API while yielding the event loop. This is a known workaround but is explicitly rejected here:

- It hides the blocking nature of the call behind an abstraction.
- Thread-pool overhead grows under load, negating the benefit.
- The async-all-the-way approach is both more correct and more idiomatic for an ASGI application.

### `databases` library

The `databases` library wraps `asyncpg` with a higher-level, query-builder-style API. It was considered but rejected:

- Adds an additional abstraction layer on top of SQLAlchemy, which already manages query generation.
- SQLAlchemy 2.0's `AsyncSession` covers the same ground with a first-party, stable implementation.
- Using `databases` would require maintaining two ORM-adjacent libraries for what is fundamentally a single concern.
