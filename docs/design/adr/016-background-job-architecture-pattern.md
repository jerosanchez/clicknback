# ADR-016: Background Job Architecture Pattern — Fan-Out Dispatcher with Per-Item Retry Runners

## Status

Accepted

## Context

ClickNBack needs background jobs that process a variable-size set of domain items (e.g. pending purchases) periodically, where each item requires:

- **Multiple I/O-bound operations** — database reads/writes, external-system calls (bank gateway, payment processor).
- **Independent retry lifecycles** — item A should not block item B and a transient failure on item A should not hold up the batch.
- **Reliable duplicate suppression** — the scheduler fires on a fixed interval; if a previous tick's work is still running, a new tick must not spawn a duplicate task for the same item.
- **Swappable external-system integrations** — the business logic for "how do we decide the outcome?" is likely to change (simulated → real bank gateway), while the orchestration (retries, deduplication, side-effect persistence) should stay stable.
- **Full testability without spawning real asyncio tasks** — each concern should be exercisable in isolation.

A naive implementation collapses all of this into one function, making it impossible to test individual concerns, reason about failure boundaries, or swap integrations later.

## Decision

We decompose every background processing job into five focused components, each with a single responsibility and a clean interface to its neighbours. We call this the **Fan-Out Dispatcher + Per-Item Runner** pattern.

### Components

```text
Scheduler tick
  │
  ▼
┌─────────────────────────────────────────────────────────────┐
│  Task Builder (_task.py)                                     │
│  Composition root. Wires all collaborators together and      │
│  returns a zero-arg async callable (ScheduledTask).          │
└──────────────────────────┬──────────────────────────────────┘
                           │ calls on every tick
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Dispatcher (_dispatcher.py)                                 │
│  Queries for "work to do" items. Checks the in-flight        │
│  tracker, spawns one asyncio.Task per new item only.         │
└────────┬────────────────────────────────────────────────────┘
         │ spawn_task(item_id) — one per new item
         ▼
┌─────────────────────────────────────────────────────────────┐
│  Runner (_runner.py)                                         │
│  Drives one item through up to max_attempts verification     │
│  rounds. Sleeps between soft failures. Force-settles on      │
│  exhaustion. Removes itself from the in-flight tracker on    │
│  exit (success or exception) via finally.                    │
│                                                              │
│  Opens a fresh DB session per attempt — no open transaction  │
│  spans multiple I/O calls.                                   │
└────────┬────────────────────────────────────────────────────┘
         │ calls per outcome
         ▼
┌─────────────────────────────────────────────────────────────┐
│  Processor (_processor.py)                                   │
│  Applies one resolved outcome (confirm / reject):            │
│  persists status, publishes domain event, writes audit row.  │
│  No retry awareness — it receives a final decision and acts. │
└─────────────────────────────────────────────────────────────┘

Cross-cutting collaborators:

┌─────────────────────────────────────────────────────────────┐
│  Strategy (_verifiers.py)                                    │
│  Encapsulates "how do we decide the outcome of one attempt?" │
│  Contract: given one item and an attempt number, return      │
│  confirmed / rejected / pending. No retry logic inside.      │
│  Swap SimulatedVerifier for a real gateway adapter here only.│
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  In-Flight Tracker (_in_flight_tracker.py)                   │
│  Tracks which items already have an active runner task.      │
│  Dispatcher checks before spawning; runner discards on exit. │
│  InMemoryInFlightTracker is safe for a single event loop.    │
│  RedisInFlightTracker can be introduced for multi-process    │
│  deployments behind the same InFlightTrackerABC interface.   │
└─────────────────────────────────────────────────────────────┘
```

### Key design choices

**Per-item fan-out, not batch iteration**:

Each item gets its own `asyncio.Task`, so one slow or retrying item never holds up the rest. The scheduler tick becomes a lightweight dispatch cycle, not a serial loop over all items.

**Retry lives in the runner, not the dispatcher**:

The dispatcher fires on the scheduler interval (e.g., every 60 s). If it also encoded retry logic, items would be delayed by the full scheduler interval between attempts. Instead, the runner owns its own inner loop and sleeps only `retry_interval_seconds` — a much tighter, per-item control knob — before trying again. This also means `max_attempts` is a per-item limit, not a per-batch count.

**Independent DB session per attempt**:

Each attempt opens its own session via `db_session_factory()`. This ensures a partial failure (network hiccup after a successful write) never leaves an open transaction holding row-level locks and affecting unrelated items.

**Idempotency guard at the top of every attempt**:

Before each attempt the runner re-fetches the item from the DB and checks its status. If the item was settled externally (race condition, manual admin action, duplicate event) the loop exits silently. This prevents double-settling.

**Outcome processor is a narrow side-effect unit**:

`_confirm_purchase` and `_reject_purchase` do exactly three things in order: update status, publish event, write audit row. They have no control flow. This makes the side-effect sequence easy to reason about, and means changing the audit schema, the event payload, or the status transition requires editing exactly one function.

**`spawn_task` is injected into the dispatcher**:

The dispatcher does not import the runner directly. The task builder creates the closure that calls the runner and passes it as a plain callable. This means the dispatcher can be unit-tested by passing a `MagicMock` for `spawn_task` — no asyncio tasks, no DB, no broker needed.

**All cross-cutting collaborators are behind ABCs**:

`PurchaseVerifierABC`, `InFlightTrackerABC`, `AuditTrailABC`, `MessageBrokerABC`, `PurchaseRepositoryABC`. The runner and processor only know the interfaces. The concrete implementations are bound once in the task builder.

### Reference implementation

`app/purchases/jobs/verify_purchases/` is the canonical implementation:

```text
_task.py                ← composition root / task builder
_dispatcher.py          ← fan-out dispatcher
_runner.py              ← per-purchase retry runner
_processor.py           ← outcome side-effect processor
_verifiers.py           ← verification strategy (ABC + simulated implementation)
_in_flight_tracker.py   ← in-flight deduplication (ABC + in-memory implementation)
```

## Where to Place a New Background Job

Background jobs are **domain-owned**. A job belongs to the domain it operates on:

- A purchase verification job lives under `app/purchases/jobs/verify_purchases/`.
- A payout settlement job lives under `app/payouts/jobs/settle_payouts/`.
- A notification dispatch job lives under `app/notifications/jobs/dispatch_notifications/`.

Only use `app/core/jobs/` for a job that is genuinely cross-cutting (i.e., it operates across multiple domains and has no clear owner). This should be rare.

If a job's `InFlightTrackerABC` (or another interface it introduces) needs to be shared across two or more domains, promote the abstract interface — not the implementation — to `app/core/`.

## Applying This Pattern to Future Background Jobs

When implementing a new background job (e.g., withdrawal settlement, notification dispatch, payout reconciliation):

1. **Create a sub-package** under `app/<domain>/jobs/<job_name>/`.
2. **Define a Strategy ABC** for the external-system interaction specific to this job.
3. **Implement the Processor** with the minimal side-effect set for a resolved outcome.
4. **Implement the Runner** with the retry loop; keep it free of domain-specific side effects — it calls the processor.
5. **Implement the Dispatcher** by scanning for "actionable" items; keep it free of runner knowledge — it receives `spawn_task`.
6. **Wire in the Task Builder** (`make_<job>_task`), which is the only file that imports all of the above.
7. **Compose the task** in the domain's `composition.py` (e.g., `app/<domain>/composition.py`) and **schedule it** in `app/main.py`.
8. **Reuse `InFlightTrackerABC`** — promote it to `app/core/` only when two or more domains need it.
9. **Test each component in isolation** using the same approach as `tests/purchases/jobs/test_verify_purchases_*.py`.

## Consequences

**Benefits:**

- Clear single-responsibility boundaries — each file is ~50–100 lines and describes exactly one concept.
- Items are processed concurrently; one slow item cannot starve others.
- Each concern is unit-testable in isolation without launching real asyncio tasks or touching a real database.
- Swapping external integrations (verifier, tracker) requires changing only the strategy implementation and the task builder binding — all orchestration code is untouched.
- The fan-out approach scales to hundreds of items per tick within a single event loop; it is horizontally scalable by replacing `InMemoryInFlightTracker` with `RedisInFlightTracker` without touching any other component.

**Accepted trade-offs:**

- More files than a single-function implementation. This is intentional — the cognitive cost of navigating five small files is lower than understanding one large, multi-concern function.
- The task builder (composition root) must be updated when a new collaborator is added. This is its explicit role.
- The in-memory tracker is process-local; duplicate processing is possible if the same job runs in two processes simultaneously. The abstraction is the mitigation path — not a workaround.

## Alternatives Considered

**Single-function background job** — rejected: quickly becomes untestable and hard to reason about as complexity grows. Every requirement change touches the same blob of code.

**Batch processing (iterate serially inside the scheduler tick)** — rejected: one slow item stalls all others; no per-item retry control; harder to add concurrency later.

**Celery or APScheduler** — not applicable here; this ADR is about internal code organisation, not the scheduler infrastructure choice. See [ADR-014](014-in-process-broker-and-scheduler.md) for that decision.

**Shared retry loop in a base class** — rejected: inheritance for orchestration creates fragile coupling between the shared base and each concrete job. The current pattern composes instead.

## References

- [ADR-013: Async Purchase Confirmation](013-async-purchase-confirmation.md)
- [ADR-014: In-Process Broker and Scheduler](014-in-process-broker-and-scheduler.md)
- [ADR-015: Persistent Audit Trail](015-persistent-audit-trail.md)
- [Reference implementation: `app/purchases/jobs/verify_purchases/`](../../../app/purchases/jobs/verify_purchases/)
- [Tests: `tests/purchases/jobs/`](../../../tests/purchases/jobs/)
