# ADR 021: Unit of Work Pattern for Atomic Multi-Repository Operations

**Date:** 2026-03-16
**Status:** Accepted

## Context

When ingesting a purchase, two writes must succeed together or not at all: inserting the purchase record (via `PurchaseRepository`) and crediting the user's pending wallet balance (via `WalletsClient`, which delegates to `WalletRepository`). If the purchase is persisted but the wallet credit is not — or vice versa — the system ends up in an inconsistent state where the purchase record and the wallet balance are out of sync.

SQLAlchemy's `AsyncSession` makes this easy to achieve at the DB level: both repositories flush their SQL into the same session, and a single `commit()` makes both writes durable atomically. The problem is *who calls `commit()`*. Both repositories correctly avoid committing themselves, since they may be composed into larger transactions. That leaves the service as the natural coordinator — but calling `await db.commit()` directly inside a service method leaks a database implementation detail into the business-logic layer.

The service layer should only express *what* needs to happen atomically; it should not know *how* that is committed or against which engine. This concern exists in any service method that must coordinate writes across multiple repositories or modules.

### Option 1: `db.commit()` directly in the service (status quo)

The service receives `db: AsyncSession` as a parameter, orchestrates all repository calls, and calls `await db.commit()` when finished.

```python
async def ingest_purchase(self, data, current_user_id, db: AsyncSession) -> Purchase:
    result = await self.repository.add_purchase(db, new_purchase)
    await self.wallets_client.credit_pending(db, user_id, cashback_amount)
    await db.commit()   # ← DB detail in service
    ...
```

- ✅ **Pros:** No extra abstraction; straightforward.
- ❌ **Cons:** The service imports and depends on SQLAlchemy's `AsyncSession`. It cannot be tested without an `AsyncMock` that satisfies async commit semantics. More importantly, the service now *knows* it is talking to a SQL database — violating the layering principle that services operate on domain concepts, not infrastructure details.

### Option 2: Commit inside the repository

Give the repository a dedicated "save and commit" method that handles the full lifecycle.

```python
async def save(self, db: AsyncSession, purchase: Purchase) -> Purchase:
    db.add(purchase)
    await db.commit()
    return purchase
```

- ✅ **Pros:** No commit in the service.
- ❌ **Cons:** The repository commits too early — before the wallet credit is flushed — breaking atomicity. A repository cannot know whether its caller has additional writes to include in the same transaction. This is the fundamental reason repositories should not commit.

### Option 3: Unit of Work pattern

Introduce a `UnitOfWorkABC` that owns the transaction boundary. Repositories and clients flush changes into `uow.session` but never commit. The service, after all writes are staged, calls `await uow.commit()`. The service knows *about* a Unit of Work as a concept, but it is decoupled from SQLAlchemy specifics.

```python
# app/core/unit_of_work.py
class UnitOfWorkABC(ABC):
    @property
    @abstractmethod
    def session(self) -> AsyncSession: ...

    @abstractmethod
    async def commit(self) -> None: ...

    @abstractmethod
    async def rollback(self) -> None: ...
```

```python
# service
async def ingest_purchase(self, data, current_user_id, uow: UnitOfWorkABC) -> Purchase:
    db = uow.session
    result = await self.repository.add_purchase(db, new_purchase)
    await self.wallets_client.credit_pending(db, user_id, cashback_amount)
    await uow.commit()   # ← domain-level concept, not DB detail
    ...
```

The concrete `SQLAlchemyUnitOfWork` wraps an `AsyncSession` and is wired in `composition.py`. In tests, a plain `Mock(spec=UnitOfWorkABC)` replaces it, allowing full isolation without touching the database.

- ✅ **Pros:** Service stays decoupled from SQLAlchemy. Transaction boundary is an explicit, testable concept. Future implementations (e.g., an in-memory UoW for tests, or a distributed saga coordinator) can be swapped by changing only `composition.py`. Consistent with the Dependency Inversion Principle already applied everywhere else in the codebase (repositories have ABCs, clients have ABCs).
- ❌ **Cons:** One additional abstraction and file to understand. Service methods that only read data still receive `db: AsyncSession` directly, creating two different conventions depending on whether the operation writes or only reads.
- ⚠️ **Notes:** The `session` property on `UnitOfWorkABC` is a deliberate exposure: repositories and clients that need the session for reads and flushes access it via `uow.session`. This is intentional — the UoW is not a full repository registry; it is solely a transaction boundary manager.

## Decision

Use the Unit of Work pattern (Option 3). Introduce `UnitOfWorkABC` and `SQLAlchemyUnitOfWork` in `app/core/unit_of_work.py`. Any service method that performs a write (commit), regardless of the number of repositories or clients, must accept a `UnitOfWorkABC` instead of a raw `AsyncSession`, and call `await uow.commit()` to close the transaction.

Read-only service methods that do not commit continue to accept `db: AsyncSession` directly — there is no benefit in wrapping a read-only session in a UoW.

## Consequences

- **What becomes easier:** Services that coordinate multi-repository writes can be unit-tested without mocking SQLAlchemy internals — a `Mock(spec=UnitOfWorkABC)` with `commit = AsyncMock()` is sufficient. It also becomes trivial to assert whether `commit` was or was not called in a given scenario, giving test coverage over transactional correctness.

- **What becomes harder:** New developers must understand when to use `uow: UnitOfWorkABC` vs. `db: AsyncSession` in a service signature. The rule is: if the method commits, use UoW; if it is read-only, use the raw session.

- **What must be enforced:** Code review should ensure that:
  1. No service method calls `db.commit()` or `db.rollback()` directly — route those through a `UnitOfWorkABC`.
  2. Repositories and clients never call `commit()` — they only flush.
  3. Service methods that write to multiple repositories/clients always accept `UnitOfWorkABC` and commit via it.

- **How to reverse it:** Fully reversible. Removing the UoW means changing affected service signatures back to `db: AsyncSession` and calling `await db.commit()` directly — a mechanical, localised change. The UoW does not affect the database schema, migrations, or any external contracts.
