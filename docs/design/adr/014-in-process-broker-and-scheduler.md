
# ADR-014: In-Process Message Broker and Task Scheduler for MVP

## Status

Accepted

## Context

ClickNBack requires infrastructure for async communication and scheduled jobs across multiple features and modules:

- **Async communication:** decoupling components via event publishing/subscribing (e.g., background jobs, domain events, notifications, analytics, cross-module orchestration).
- **Job scheduling:** running periodic or delayed tasks (e.g., background verification, cleanup, reporting, notifications) without external job queues or cron.

At MVP stage, the system is a single-process modular monolith. There is no distributed infrastructure, no need for cross-service message passing, and no requirement for scheduled job persistence across restarts.

## Decision

We implement both components in-process using the Python standard library:

- **`InMemoryMessageBroker`** — a dict-backed async pub/sub broker. Handlers are awaited sequentially by `publish()`, so the caller retains full visibility: it knows every handler completed before moving on, and a failed handler surfaces immediately rather than failing silently in the background.
- **`InMemoryTaskScheduler`** — an `asyncio.create_task`-based periodic runner. Each registered task runs in its own asyncio Task on a fixed interval; all tasks are cancelled cleanly on application shutdown via the FastAPI lifespan hook.

Both are hidden behind ABCs (`MessageBrokerABC`, `TaskSchedulerABC`). Domain code depends only on the interfaces; the concrete implementations are bound once in the composition root.

## Consequences

**Benefits:**

- Zero additional dependencies or operational overhead — no Kafka, Redis, Celery, or APScheduler to run, monitor, or configure for local development.
- Full testability: each component is instantiated fresh per test; no shared state, no external process required.
- Clear upgrade path: replacing `InMemoryMessageBroker` with a Kafka adapter or `InMemoryTaskScheduler` with APScheduler requires only a one-line binding change in the composition root.

**Accepted trade-offs:**

- **No durability:** events and scheduled state are lost on process restart. Acceptable for an MVP where jobs re-discover state from the database on every run.
- **Sequential handler dispatch:** slow handlers delay the job loop. Acceptable at current scale; switch to fire-and-forget (`asyncio.create_task` per handler) or a real broker if independent handler concurrency becomes a requirement.
- **Single-process only:** the in-memory broker cannot fan out to handlers running in separate processes or machines. A real broker (Kafka, RabbitMQ) is the correct solution if the system scales horizontally.

## Alternatives Considered

- **Celery + Redis** — rejected: significant operational overhead (Redis instance, Celery worker process, beat scheduler) for a feature set easily covered in-process at MVP scale.
- **APScheduler** — rejected for now: a good fit for production scheduling (cron expressions, job stores, distributed locking), but unnecessary complexity before the system needs it.
- **Direct function calls (no broker)** — rejected: couples modules tightly; adding a new subscriber (e.g., notifications) would require editing the publisher itself.

## References

- [ADR-013: Async Purchase Confirmation via Internal Event Broker](013-async-purchase-confirmation.md)
- [ADR-001: Adopt Modular Monolith Approach](001-adopt-modular-monolith-approach.md)
