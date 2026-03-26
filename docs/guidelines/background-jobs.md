# Background Jobs Guide

This document is the authoritative reference for implementing periodic background jobs in ClickNBack. It covers module placement, the factory pattern, dependency injection, scheduler wiring, configuration, testing conventions, and the rejection-simulation pattern.

---

## 1. Where Jobs Live

Background jobs are **domain-owned**. A job belongs to the domain it operates on and lives under `app/<domain>/jobs/<job_name>/`:

```text
app/purchases/jobs/
  __init__.py
  verify_purchases/     ← One sub-package per job
    __init__.py
    _task.py
    _dispatcher.py
    _runner.py
    _processor.py
    _verifiers.py
    _in_flight_tracker.py

app/payouts/jobs/
  __init__.py
  settle_payouts/       ← Future job example
    ...
```

Only use `app/core/jobs/` for a job that is genuinely cross-cutting (operates across multiple domains with no clear owner) — this should be rare.

Each job follows the **Fan-Out Dispatcher + Per-Item Runner** pattern (ADR-016). Do not co-locate unrelated jobs in a single file.

Tests mirror this structure under `tests/<domain>/jobs/` (e.g., `tests/purchases/jobs/`).

---

## 2. The Factory Pattern

Jobs must not hard-code their dependencies (repositories, audit trail, broker, DB session factory). Instead, each job module exposes a **factory function** — `make_<job_name>_task` — that accepts all dependencies as keyword arguments and returns a zero-argument `ScheduledTask` closure:

```python
from app.core.scheduler import ScheduledTask

def make_verify_purchases_task(
    *,
    repository: PurchaseRepositoryABC,
    broker: MessageBrokerABC,
    db_session_factory: async_sessionmaker[AsyncSession],
    rejection_merchant_id: str,
    max_verification_attempts: int,
    interval_seconds: float,
    datetime_provider: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
) -> ScheduledTask:
    async def task() -> None:
        async with db_session_factory() as db:
            await _run_core_logic(db=db, ...)
    return task
```

Key rules:

- All parameters are **keyword-only** (`*` before the first arg). Makes call sites self-documenting.
- Inject `datetime_provider` so tests can freeze time without patching the module.
- The returned `task()` takes no arguments — it must match `ScheduledTask = Callable[[], Coroutine[Any, Any, None]]`.

### Why a factory, not a plain function?

The `InMemoryTaskScheduler` stores and calls `task()` with no arguments. All dependency context must be captured at schedule-time. A factory makes this closure explicit and keeps the job module free of global state.

---

## 3. Core Logic Extraction

Separate the pure business logic from the closure so it can be tested directly without constructing a session factory or mocking `asynccontextmanager`:

```python
# Internal — tested directly; no need for session-factory mocking
async def _verify_pending_purchases(
    *,
    db: AsyncSession,
    repository: PurchaseRepositoryABC,
    ...
    now: datetime,
) -> None:
    ...

# Public — the closure that wraps _verify_pending_purchases
def make_verify_purchases_task(...) -> ScheduledTask:
    async def task() -> None:
        async with db_session_factory() as db:
            await _verify_pending_purchases(db=db, repository=repository, ..., now=datetime_provider())
    return task
```

Name convention: `_<job_name>` (single leading underscore — module-private, but importable in tests for direct invocation).

---

## 4. Database Sessions

Jobs are **not** part of the FastAPI request lifecycle. They must open and close their own `AsyncSession`:

```python
async with db_session_factory() as db:
    await _run(db=db, ...)
```

Use `AsyncSessionLocal` (from `app.core.database`) as the factory. Pass it as an argument to the factory function — do not import it directly inside the job module (keeps the job testable in isolation).

---

## 5. Audit Trail

Every job that transitions a purchase status, updates a wallet balance, or records a financial transaction must emit a **domain event** after the state change is committed. The audit module subscribes to domain events and persists audit records independently (see ADR-023).

Do **not** call `AuditTrail.record(...)` directly from jobs. Instead, publish the domain event that represents the outcome:

```python
await broker.publish(
    PurchaseConfirmed(
        purchase_id=purchase.id,
        user_id=purchase.user_id,
        merchant_id=purchase.merchant_id,
        amount=purchase.amount,
        currency=purchase.currency,
        cashback_amount=cashback_amount,
        verified_at=now,
    )
)
```

The audit module's event handler (`app/core/audit/handlers.py`) subscribes to these domain events and writes the corresponding `AuditLog` row. This keeps jobs decoupled from audit infrastructure.

When adding a new auditable operation, define (or reuse) a domain event in
`app/core/events/<domain>_events.py` and register a handler in
`app/core/audit/composition.py`.

---

## 6. Event Publishing

Publish domain events **after** the state change is committed to the DB. Use the module-level `broker` singleton from `app.core.broker`:

```python
from app.core.broker import broker  # passed in as a dependency at wiring time
await broker.publish(PurchaseConfirmed(...))
```

Define event dataclasses in `app/core/events/<domain>_events.py`. Use frozen `@dataclass` so events are immutable and equality-comparable (useful in tests).

---

## 7. Wiring in `main.py`

Wire jobs in `app/main.py` — the application composition root. Import the factory, construct the task, and register it with the scheduler **before** the `lifespan` definition:

```python
# app/purchases/composition.py — compose the task with all its dependencies
from app.purchases.jobs.verify_purchases import make_verify_purchases_task, SimulatedPurchaseVerifier

def get_verify_purchases_task():
    return make_verify_purchases_task(...)

# app/main.py — schedule via the composition root
from app.purchases.composition import get_verify_purchases_task

scheduler = InMemoryTaskScheduler()
scheduler.schedule(
    "verify_purchases",
    get_verify_purchases_task(),
    interval_seconds=settings.purchase_confirmation_interval_seconds,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await scheduler.start()
    yield
    await scheduler.stop()
```

Two-layer wiring:

1. **`<domain>/composition.py`** — constructs the task with all dependencies wired.
2. **`app/main.py`** — schedules the pre-built task using the composition root.

Never call `scheduler.start()` or schedule tasks inside the lifespan — that couples startup ordering to job logic. Register all tasks before the lifespan block.

---

## 8. Configuration

Every job interval and behavioural knob must be a `Settings` field in `app/core/config.py` with a sensible default:

```python
# app/core/config.py
purchase_confirmation_interval_seconds: int = 60
purchase_max_verification_attempts: int = 3
rejection_merchant_id: str = ""
```

Add matching entries to `.env.example` with comments explaining each variable:

```ini
PURCHASE_CONFIRMATION_INTERVAL_SECONDS=60
PURCHASE_MAX_VERIFICATION_ATTEMPTS=3
REJECTION_MERCHANT_ID=f0000000-0000-0000-0000-000000000001
```

---

## 9. Rejection/Simulation Patterns

Where a real external system (e.g., a bank) cannot be connected in development or demo environments, use a **fixed seed entity** to simulate failure scenarios.

### Steps

1. **Choose a fixed UUID** for the simulated-failure entity (e.g., `f0000000-0000-0000-0000-000000000001`).
2. **Add it to `seeds/all.sql`** with a descriptive name (e.g., `BankSimFail`). Add a comment explaining its purpose.
3. **Add it to Settings** as a configurable string (`rejection_merchant_id`). Default to the well-known UUID in `.env.example`.
4. **Document it** in `README.md` (Testing section) and in the relevant workflow doc under `docs/specs/workflows/`.
5. **Guard the check** so disabling the simulation is a one-line env change (`rejection_merchant_id = ""`):

```python
is_rejection = bool(rejection_merchant_id) and purchase.merchant_id == rejection_merchant_id
```

This pattern is preferable to hardcoding magic values inside the job logic.

---

## 10. Testing Background Jobs

Tests live under `tests/<domain>/jobs/` following the **one file per module** convention:

```text
tests/purchases/jobs/
  __init__.py
  test_verify_purchases_runner.py
  test_verify_purchases_dispatcher.py
  test_verify_purchases_task.py
  test_verify_purchases_in_flight_tracker.py
```

Follow the project's standard patterns:

### Test the core logic directly

Import private helpers directly from their submodule and test them with mocked dependencies. This avoids constructing a real session factory and makes tests fast and deterministic:

```python
from app.purchases.jobs.verify_purchases._runner import _run_verification_with_retry
from app.purchases.jobs.verify_purchases._dispatcher import _dispatch_pending_purchases

@pytest.mark.asyncio
async def test_confirms_normal_purchase(repository, broker, db):
    purchase = _make_purchase()
    repository.get_pending_purchases = AsyncMock(return_value=[purchase])
    repository.update_status = AsyncMock()
    broker.publish = AsyncMock()

    await _verify_pending_purchases(
        db=db,
        repository=repository,
        broker=broker,
        rejection_merchant_id="",
        max_verification_attempts=3,
        interval_seconds=60.0,
        now=datetime(2026, 3, 11, 12, 0, 0, tzinfo=timezone.utc),
    )

    repository.update_status.assert_called_once_with(db, purchase.id, "confirmed")
```

### Use `create_autospec` for dependencies

```python
from unittest.mock import create_autospec
repository = create_autospec(PurchaseRepositoryABC)
```

### Freeze time with `datetime_provider`

Pass `datetime_provider=lambda: fixed_now` to the factory. Never patch `datetime.now` globally.

### Test the factory too

Verify that the zero-arg closure produced by the factory actually dispatches correctly with no pending items:

```python
async def test_task_factory_invokes_dispatcher(repository, broker):
    session_factory, _ = _make_session_factory()
    repository.get_pending_purchases = AsyncMock(return_value=[])

    task = make_verify_purchases_task(
        repository=repository, ..., db_session_factory=session_factory
    )
    assert callable(task)
    await task()

    repository.get_pending_purchases.assert_called_once()
```

### Coverage checklist for a typical job

| Scenario | What to assert |
| --- | --- |
| Happy path | Status updated, domain event published |
| No pending items | None of the above called |
| Simulation/failure entity within retry window | No status update, no event, no audit |
| Simulation/failure entity retries exhausted | Correct status, `PurchaseRejected` event, audit |
| Simulation disabled (empty ID) | All items treated as normal |
| Mixed batch | Correct per-item routing |
| Factory closure | Calls core logic with correct session |

---

## 11. Checklist: Implementing a New Background Job

- [ ] Create `app/<domain>/jobs/<job_name>/` sub-package following the Fan-Out Dispatcher + Per-Item Runner pattern (ADR-016).
- [ ] Add a `__init__.py` to `app/<domain>/jobs/` if it does not exist yet.
- [ ] Add job interval and any behavioural settings to `app/core/config.py` and `.env.example`.
- [ ] Add any new `AuditAction` members to `app/core/audit/enums.py`.
- [ ] Add event dataclasses to `app/core/events/<domain>_events.py` if needed.
- [ ] Add repository methods (e.g., `get_pending_*`, `update_status`) if missing from the relevant repository.
- [ ] Compose the task in `app/<domain>/composition.py` (e.g., `get_<job_name>_task()`).
- [ ] Schedule the task in `app/main.py` before the lifespan block, via the composition root function.
- [ ] Add seed data for any simulation entities to `seeds/all.sql`.
- [ ] Write unit tests under `tests/<domain>/jobs/` — one file per module (`test_<job>_runner.py`, `test_<job>_dispatcher.py`, etc.).
- [ ] Document the simulation entity in `README.md` (Testing section) and the relevant workflow file.
