# ADR-023: Event-Driven Audit Logging

## Status

Accepted

**Date:** 2026-03-26  
**Author(s):** AI Assistant  
**Implementation:** Complete — Phase 7 (All acceptance criteria met)

## Context

ADR-015 established a persistent audit trail using direct injection of an `AuditTrail` service into every service, job, and handler that performs critical operations. This pattern has worked well for establishing audit correctness, but has created architectural friction:

1. **Coupling:** Audit becomes a cross-cutting concern injected into service constructors, polluting signatures and complicating wiring.
2. **Scalability:** As the system adds new auditable operations (cashback payout, wallet withdrawal, merchant activation, etc.), the number of audit service injections grows linearly across modules.
3. **Testability:** Unit tests must mock the audit service in every test, even when they don't care about audit behavior. Audit record construction is scattered throughout test assertions.
4. **Future Challenges:** Cannot easily move audit to a separate microservice, swap audit backends, or implement truly async audit logging without refactoring all consuming code.

These issues arise because audit logging is conflated with business logic — both live in the same transaction, and both require the same injection pattern. However, conceptually, audit logging is an **event subscriber** (a cross-cutting concern), not a **business rule** (a domain actor).

The codebase already has a message broker pattern in place (ADR-014) used to publish domain events (e.g., `PurchaseConfirmed`, `PurchaseRejected`). This infrastructure can be extended to include audit events, allowing audit logging to be decoupled from business logic.

## Decision

Refactor the audit logging system to use an **event-driven model** built on the domain events already published by business modules:

1. **Domain Events as the Audit Source:** Business modules publish rich domain events
   (`PurchaseConfirmed`, `PurchaseRejected`, `PurchaseReversed`, …) that carry all
   audit-relevant context (actor, amount, currency, outcome details). There is no separate
   `AuditEvent` class — the audit module subscribes directly to domain events.

2. **Audit Handlers:** `app/core/audit/handlers.py` provides one handler per subscribable
   domain event (`_handle_purchase_confirmed`, `_handle_purchase_rejected`,
   `_handle_purchase_reversed`). An internal `_persist_audit_log()` helper centralises the
   `AuditLog` persistence logic.

3. **Event Emission:** Business services publish domain events **after** `uow.commit()`;
   background jobs publish after `db.commit()`. The audit handler fires only when the
   business operation has durably succeeded.

4. **Subscriber Registration:** `app/core/audit/composition.py` exposes
   `subscribe_audit_handlers(broker, …)` which registers one subscription per domain event
   type. It is called in `app/main.py` at startup.

5. **No Injection:** The `AuditTrail` service is no longer injected into any service, job, or
   handler. Business logic publishes domain events; the audit module is a fully independent
   subscriber with zero coupling to the callers.

### Benefits

- **Clean separation of concerns:** Business logic focuses on its domain operations; audit logging is an independent subscriber.
- **Scalability:** Adding a new auditable operation is a one-liner: publish an event. No new injections, no new wiring, no test mocks to update.
- **Event-driven architecture:** Audit is just one subscriber — future subscribers (compliance webhooks, analytics, fraud detection) can be added without touching business logic.
- **Future-proof:** The audit handler can be replaced or moved to a microservice, Kafka adapter, or external audit service without touching any business logic.
- **Async-ready:** Audit recording can operate asynchronously (if the broker is replaced with Kafka/RabbitMQ) without blocking business operations.
- **Testability:** Services no longer carry audit mocks; unit tests focus on business logic and event emission. Audit correctness is tested in audit handler tests.

### Implementation Phases

1. **Event Definition** — Define audit event classes capturing all audit-relevant context.
2. **Audit Handler** — Implement subscriber that translates events into audit records.
3. **Event Emission Refactoring** — Replace all audit service calls with event emissions.
4. **Dependency Cleanup** — Remove all `AuditTrail` injections from services and jobs.
5. **Wiring and Startup** — Register audit subscribers in `app/main.py`.
6. **Testing** — Write tests verifying event → audit record flow; remove audit mocks from service tests.
7. **Documentation** — Update architecture docs and feature-architecture guide.

See [GitHub issue #54](https://github.com/jerosanchez/clicknback/issues/54) for the full implementation roadmap.

## Consequences

### Positive

- Services are no longer coupled to audit infrastructure.
- Audit logging becomes pluggable; easy to swap implementations or move to a microservice.
- Adding auditable operations is simpler: no new injections required.
- Event handlers can be added independently without modifying business logic.
- Aligns with broader event-driven architecture patterns and prepares for distributed deployment.

### Negative

- Audit events must be published **after** a transaction succeeds; audit recording is implicit rather than explicit in the business flow.
- If the event broker fails to subscribe to an event at startup, audit logging silently fails (mitigated by comprehensive startup tests).
- The in-memory broker (ADR-014) executes handlers sequentially; if audit recording is slow, it blocks the job loop (mitigated by replacing with Kafka at scale).

### Neutral

- HTTP API contracts are unchanged; no external impact.
- The `audit_logs` table schema remains identical; no migrations required beyond removing the old audit service.
- Event handlers are registered at startup, not lazily on first use; adds minimal overhead.

## Trade-offs

### Why Not Keep Direct Injection?

Direct injection is simpler for a single audit service but creates coupling. As the system evolves (compliance webhooks, fraud detection, analytics), each new subscriber would require repeating the injection pattern, multiplying complexity. Event-driven decouples these concerns.

### Why Not Use a Message Queue (Kafka/RabbitMQ) Now?

The in-memory broker (ADR-014) is sufficient for MVP; audit events are published and consumed synchronously within the same process. When audit latency becomes a constraint, the broker implementation can be swapped without touching business logic. This defers operational complexity until it's justified.

### Why Not Store Audit Events as First-Class Entities?

Audit events are ephemeral; once converted to an audit record in the database, the event object is discarded. Storing events adds storage overhead with no benefit for compliance purposes. The audit record (not the event) is the system of record.

## Related Decisions

- **ADR-014** — In-process broker and scheduler; establishes the message broker infrastructure that audit events will use.
- **ADR-015** — Persistent audit trail; establishes the audit table schema and semantics; this ADR refactors how records are written, not what is recorded.
- **ADR-016** — Background job architecture; audit events follow the same publish/subscribe pattern as purchase verification events.

## Implementation Checklist

See GitHub issue #54 for detailed task breakdown and acceptance criteria.

## Future Considerations

1. **Async Audit Backend:** Replace in-memory broker with Kafka/RabbitMQ to make audit recording truly asynchronous, decoupled from business operation latency.
2. **Audit Event Persistence:** Store audit events as a separate event log for temporal querying and compliance audits.
3. **External Audit Services:** Forward audit events to third-party compliance platforms (e.g., Splunk, Datadog) via event subscribers.
4. **Audit Webhook:** Publish audit events to customer-provided webhooks for real-time compliance feeds.
