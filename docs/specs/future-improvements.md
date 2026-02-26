# Future Improvements

This document identifies opportunities to incorporate advanced engineering features into ClickNBack. The goal is not to add complexity for its own sake, but to use this project as a practice ground for techniques that appear in real production systems. Each item is scoped to be independently implementable in roughly one to two days.

---

## 1. Rate Limiting

**Where:** Purchase ingestion endpoint (`POST /purchases`) and the login endpoint (`POST /auth/login`).

**Why those endpoints:** Purchase ingestion simulates an affiliate webhook — a natural target for abuse or replay attacks. The login endpoint is the canonical use case for brute-force protection.

**General approach:** Add a middleware or per-route decorator powered by [`slowapi`](https://github.com/laurentS/slowapi), which is the FastAPI-idiomatic wrapper around `limits`. Use an in-memory store for the simplest case; swap in a Redis backend when persistence across restarts is needed. Rules are expressed as strings (`"10/minute"`) and keyed by the client IP or, for authenticated endpoints, the user ID from the JWT.

**Flow improvement:** Without rate limiting, a single IP can hammer the purchase ingestion endpoint indefinitely. With it, the system returns `429 Too Many Requests` with a `Retry-After` header after the threshold is crossed, and the counter resets on the defined window.

**Benefits:**

- Demonstrates middleware integration in FastAPI.
- Concrete fraud-prevention mechanism aligned with the project's stated requirement.
- Visible in the error-handling pipeline (fits the existing `{ "error": { "code", "message" } }` envelope).

**Trade-offs / drawbacks:**

- In-memory counters are lost on restart and do not work across multiple instances; Redis is needed for production-grade correctness.
- IP-based keying is easily bypassed with proxies; user-ID keying requires the request to be authenticated first, which complicates placement in the middleware stack.
- Globally applied rules can affect legitimate high-volume affiliate partners — real systems would need per-partner quotas.

---

## 2. Redis Caching

**Where:** Active offer lookup during purchase ingestion; merchant status lookup.

**Why those points:** When a purchase arrives, the system must find the currently active offer for the merchant. In a high-throughput scenario this is a hot-path DB read that changes infrequently (offers are admin-managed). Caching the result gives a clear performance win without any correctness risk if invalidation is done correctly.

**General approach:** Introduce a `CacheClient` abstraction in `app/core/` backed by `redis-py`. Wrap the repository call in the service: on a cache hit, return the cached offer; on a miss, query the DB and write to cache with a short TTL (e.g., 60 seconds). When an offer is created, activated, or deactivated, the service explicitly invalidates the key. The cache key is `offer:active:<merchant_id>`.

**Flow improvement:** Purchase ingestion goes from "always hits the DB for offer lookup" to "DB is only hit once per 60-second window per merchant". Under any realistic load this removes a significant fraction of read queries from the critical path.

**Benefits:**

- Demonstrates the cache-aside pattern, a standard interview and production topic.
- Introduces Redis to the stack cleanly — the `CacheClient` abstraction keeps it mockable in unit tests.
- TTL-based expiry means stale data is self-healing even if explicit invalidation is missed.

**Trade-offs / drawbacks:**

- The 60-second TTL window means a newly deactivated offer could still be applied to purchases arriving in that window — a real system would need a shorter TTL or synchronous invalidation on deactivation.
- Adds Redis as an infrastructure dependency (a `docker-compose` service entry is all that is needed for local dev).
- Cache serialization (Pydantic model → JSON → back) adds a small amount of boilerplate.

---

## 3. Circuit Breaker

**Where:** The `auth` module's interaction with a simulated external identity verifier, or more naturally on a simulated affiliate network client that notifies purchase confirmations.

**Why here:** The project already simulates an external affiliate webhook. A natural extension is to model the reverse direction: the platform calling out to an affiliate API to confirm a purchase or retrieve metadata. That outbound call is the right place for a circuit breaker.

**General approach:** Introduce a thin `AffiliateClient` class (currently implicit) in a `clients.py` file inside the `purchases` module. Wrap each outbound call with [`circuitbreaker`](https://github.com/fabfuel/circuitbreaker) (a small, zero-dependency Python library). The decorator tracks failures; after a threshold (e.g., 5 failures within 30 seconds), the circuit opens and calls fail immediately with a `CircuitBreakerError` rather than waiting for a timeout. After a cooldown window, the circuit moves to half-open and allows a single probe request.

**Flow improvement:** Without a circuit breaker, N concurrent purchase confirmation requests all hang waiting for a dead external service for the full HTTP timeout before failing. With a circuit breaker, after the first few failures the remaining calls fail immediately, freeing threads and allowing the system to degrade gracefully rather than exhausting its connection pool.

**Benefits:**

- Demonstrates resilience engineering — a topic that consistently appears in senior-level discussions.
- The `AffiliateClient` abstraction it forces you to introduce is good design regardless of the circuit breaker.
- The state machine (closed → open → half-open) is a real concept worth internalizing.

**Trade-offs / drawbacks:**

- In-process circuit breaker state is not shared across multiple application instances; a distributed circuit breaker requires Redis or a sidecar.
- Threshold calibration is non-trivial in production: too sensitive and transient errors trip the breaker; too lenient and you don't prevent cascade failures.
- For this project the "external service" is simulated, so the demonstration value is architectural rather than observational.

---

## 4. Event-Driven Internal Communication

**Where:** The purchase confirmation and reversal flows, which currently need to update both the purchase record and the wallet atomically.

**Why here:** Purchase confirmation triggers two downstream effects: the cashback transaction state changes and the wallet balance moves. These are currently coupled inside a single service method. An event-driven approach models the domain more accurately — a `PurchaseConfirmed` event is emitted and the wallet module reacts to it as a subscriber.

**General approach:** Implement a lightweight in-process event bus in `app/core/events.py`. The bus is a simple dictionary of `event_type → list[handler]`. Modules register handlers at startup (in `main.py` or `composition.py`). The `PurchaseService` emits `PurchaseConfirmed(purchase_id, user_id, cashback_amount)` after persisting the state change; the `WalletService` handler picks it up and applies the balance update — both within the same DB transaction via a shared `Session`. This is the simplest version. A more advanced version replaces the in-process bus with Redis Pub/Sub or a Celery task queue, accepting eventual consistency in exchange for decoupling.

**Flow improvement:** The purchase and wallet modules no longer need to know about each other. The purchase service emits an event and is done; the wallet module evolves independently. Adding a new side-effect (e.g., sending a push notification on confirmation) is a new subscriber registration, not a change to the purchase service.

**Benefits:**

- Demonstrates the observer / domain event pattern, a cornerstone of event-driven and DDD architectures.
- Makes the decoupling between modules explicit and enforced rather than a convention.
- The in-process version is zero-infrastructure; the Redis version demonstrates a real message broker without much additional code.

**Trade-offs / drawbacks:**

- The in-process bus is synchronous and still within the same transaction — it preserves ACID but does not decouple deployment.
- Moving to an async broker (Redis Pub/Sub, Celery) introduces eventual consistency: the wallet update may lag behind the purchase confirmation. That window must be handled (idempotent consumers, at-least-once delivery).
- Debugging event-driven systems is harder — tracing an operation across emitters and subscribers requires correlation IDs and good logging.

---

## 5. Background Task Processing

**Where:** Post-registration welcome email, cashback confirmation notification, and payout processing (which can be deferred rather than blocking the HTTP response).

**Why here:** These are all fire-and-forget operations relative to the HTTP response. The user should get a `201` or `200` immediately; the downstream work (sending an email, triggering a notification webhook) should not add latency to the response.

**General approach:** Two levels of implementation are useful here as learning progressions:

1. **FastAPI `BackgroundTasks`** — pass a `BackgroundTasks` instance into an endpoint, call `background_tasks.add_task(send_welcome_email, user.email)`. Zero infrastructure. The task runs in the same process after the response is sent. Good enough for low-volume side-effects.

2. **Celery with a Redis broker** — define `@celery_app.task` functions, call `.delay()` from the service layer. Celery workers run in a separate process. Demonstrates a real distributed task queue: retries, exponential backoff, dead-letter queues, task monitoring via Flower.

**Flow improvement:** Endpoint response time drops from `(business logic + email send)` to `(business logic)`. Failures in the background task do not affect the HTTP response; they are retried by Celery without user impact.

**Benefits:**

- Celery is ubiquitous in Python backends — demonstrating it shows familiarity with the production Python ecosystem.
- Retry logic and idempotency of tasks are important topics (what happens if the Celery worker crashes mid-send?).
- Flower (the Celery monitoring UI) provides a visual output with minimal setup.

**Trade-offs / drawbacks:**

- Celery adds Redis (or RabbitMQ) as a broker dependency and a separate worker process to the development environment.
- Background task failures are silent unless monitoring is set up — the user gets a `201` even if the email task fails permanently.
- `BackgroundTasks` runs in the same process as the web server — under Uvicorn this means a slow or blocking task can affect request handling.

---

## 6. AI-Augmented Fraud Scoring

**Where:** Purchase ingestion — before a purchase is persisted, assign it a fraud risk score. Flag high-risk purchases for review rather than immediately crediting cashback.

**Why here:** The project already mentions fraud prevention as a concern (idempotency keys, monthly caps). Adding a scoring step is a natural extension and a compelling demo of AI integration in a financial context.

**General approach:** Define a `FraudScorer` interface in `app/core/` and inject it into `PurchaseService` via the constructor. Two implementations are interesting:

1. **Rule-based scorer** — a set of heuristics (purchase amount far above user's average, merchant is newly added, purchase at an unusual hour) produces a score between 0 and 1. Fully deterministic, no external dependency, easy to test.

2. **LLM-assisted anomaly explanation** — when the rule-based score exceeds a threshold, call an LLM API (OpenAI, Mistral via `litellm`) with a structured prompt: *"Given this user's purchase history summary and this new purchase, identify any anomalies."* The LLM response is stored as a `fraud_explanation` field on the purchase record and surfaced in an admin endpoint. This is AI-augmented, not AI-automated: a human admin reviews flagged purchases.

**Flow improvement:** Instead of crediting every purchase immediately, high-risk purchases are created in a `flagged` state. An admin can review the LLM-generated explanation and either approve (transitions to normal `pending`) or reject (transitions to `reversed`). Low-risk purchases flow through unchanged.

**Benefits:**

- Demonstrates thoughtful, bounded AI integration — AI is used as a decision support tool, not a black box.
- The `FraudScorer` interface makes the feature fully testable (the LLM implementation is swapped for a stub in unit tests).
- Adds a new entity state and admin workflow — good practice for state machine extension.
- The LLM prompt engineering aspect is a in-demand, practical skill.

**Trade-offs / drawbacks:**

- LLM calls add latency to the purchase ingestion path (100–500 ms). For a synchronous endpoint this is noticeable; most real systems would either accept the latency as a trade-off for the security benefit or move the LLM call to an async worker.
- LLM API calls cost money and introduce an external dependency with its own availability characteristics — the circuit breaker from §3 pairs naturally here.
- False positive rates from a simple rule-based scorer can be high, annoying legitimate users and increasing admin workload.
- For a demo project, the LLM call can be safely stubbed or skipped in CI tests using environment-flag-controlled injection.

---

## Summary

| Feature | Module(s) Touched | Infrastructure Added | Difficulty |
| --- | --- | --- | --- |
| Rate limiting | `core/`, `auth/`, `purchases/` | Redis (optional) | Low |
| Redis caching | `core/`, `purchases/`, `offers/` | Redis | Low–Medium |
| Circuit breaker | `purchases/` (affiliate client) | None | Low |
| Event-driven comms | `purchases/`, `wallets/`, `core/` | Redis (optional) | Medium |
| Background tasks | `users/`, `payouts/`, `core/` | Redis + Celery | Medium |
| AI fraud scoring | `purchases/`, `core/` | LLM API key | Medium |

Each feature is independent of the others (except that background tasks and LLM calls both pair well with the circuit breaker) and can be implemented in isolation without disrupting the existing codebase.
