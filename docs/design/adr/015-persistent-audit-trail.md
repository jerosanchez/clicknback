# ADR-015: Persistent Audit Trail for Critical Operations

## Status

Accepted

## Context

As the platform approaches production-grade features — purchase confirmation and rejection, cashback calculation, and wallet withdrawals — there is a growing need to record *who did what, when, and with what outcome* for every critical state-changing operation.

Python's standard `logging` module (ADR 009) covers runtime observability: structured log lines emitted to stdout, consumed by a log aggregation tool. This model is suited for debugging, performance monitoring, and alerting. It is **not** suited for auditability and traceability:

- Log lines are ephemeral, external to the application database, and unqueryable via standard SQL.
- They carry no first-class identity of the actor performing the action.
- There is no built-in mechanism to correlate an operation with the specific record it affected.
- Log rotation and retention policies can silently discard compliance-relevant records.

Critical operations in ClickNBack fall into two categories that both require traceability:

- **Automated system operations**: a background job confirms or rejects a purchase; a scheduler processes a payout. No human is involved, but the action must be attributable to the *system* with full context.
- **Manual admin interventions**: an admin activates a merchant, manually overrides a purchase state (future), or processes a payout. These carry the highest compliance risk and require the strongest accountability.

Without a persistent, queryable audit record, answering questions like *"why was this purchase rejected?", "who confirmed this payout?", "when did the cashback balance change?"* requires reconstructing state from log files — slow, error-prone, and sometimes impossible after log rotation.

## Decision

We introduce a dedicated `audit_trail` infrastructure component in `app/core/` that persists a record of every critical operation to the `audit_logs` database table.

### Component: `app/core/audit/`

A self-contained sub-package following the same layered structure used by domain feature modules. This makes it independently navigable and ready to be promoted to a standalone service if needed. All public symbols are re-exported from `__init__.py` so call sites remain unchanged:

```text
app/core/audit/
  __init__.py      ← Re-exports all public symbols
  enums.py         ← AuditActorType, AuditOutcome, AuditAction
  models.py        ← AuditLog ORM model
  repositories.py  ← AuditTrailRepositoryABC + AuditTrailRepository
  handlers.py      ← Audit event handler (_handle_audit_event)
```

- **`AuditActorType`** — string enum: `system` | `admin` | `user`.
- **`AuditAction`** — string enum listing every auditable action (e.g. `PURCHASE_CONFIRMED`, `WITHDRAWAL_PROCESSED`). New actions are added to `enums.py` as features are implemented.
- **`AuditLog`** — SQLAlchemy ORM model mapped to the `audit_logs` table.
- **`AuditTrailRepositoryABC`** and **`AuditTrailRepository`** — the repository pair following the project's standard pattern (ABCs enable mocking in unit tests).
- **`_handle_purchase_confirmed()`**, **`_handle_purchase_rejected()`**, **`_handle_purchase_reversed()`** — per-domain-event handlers in `app/core/audit/handlers.py` that subscribe to purchase domain events (see [ADR-023](023-event-driven-audit-logging.md)) and persist `AuditLog` rows. This replaces the old direct service injection pattern.

### `audit_logs` table

| Field          | Type     | Constraints / Notes                                                      |
|----------------|----------|--------------------------------------------------------------------------|
| id             | UUID     | PK                                                                       |
| occurred_at    | datetime | UTC timestamp; set by the application, not a DB default                  |
| actor_type     | string   | `system` \| `admin` \| `user`                                            |
| actor_id       | string   | UUID of the acting user/admin; `null` when actor_type=system             |
| action         | string   | `AuditAction` string enum member                                         |
| resource_type  | string   | Domain entity type: `purchase`, `payout`, `merchant`, etc.               |
| resource_id    | string   | UUID of the affected resource                                            |
| outcome        | string   | `success` \| `failure`                                                   |
| details        | JSON     | nullable; action-specific payload (amounts, status change, reason, etc.) |

### Usage pattern in services (deprecated; see ADR-023)

**Note:** As of ADR-023 (Event-Driven Audit Logging), the direct service injection pattern described below is no longer used. Services and jobs publish domain events (e.g., `PurchaseConfirmed`, `PurchaseReversed`) via the message broker instead of calling `AuditTrail.record()` directly. This section remains for historical context.

Previously, services that performed auditable operations received an `AuditTrail` instance via `__init__()`. The `record()` call was placed **after** the business operation succeeded — if the operation failed and raised an exception, no audit row was written, accurately reflecting the outcome.

For manual admin operations, `actor_type=AuditActorType.ADMIN` and `actor_id` was set to the authenticated user's ID.

**Current pattern (ADR-023):** Services and jobs publish domain events (e.g., `PurchaseConfirmed`, `PurchaseReversed`) via the message broker. Per-event audit handlers in `app/core/audit/handlers.py` subscribe and persist `AuditLog` rows after the business transaction succeeds.

### Querying audit records (future)

The `audit_logs` table is immediately queryable via SQL for compliance reviews, incident investigations, and customer support. Exposing it via an admin-only API endpoint is deferred to a future feature but requires no schema changes.

## Consequences

**Benefits:**

- Operations affecting financial state leave a durable, queryable record independent of log rotation.
- The actor (system job or specific admin) is unambiguously identified on every record.
- Each record links directly to the affected domain entity — no log-file archaeology required.
- Using the repository pattern means the audit trail is mockable in unit tests; services stay fully testable without a running database.
- The dual write (DB + structured log) ensures both layers carry consistent information.
- Adding new auditable actions requires adding one enum member to `AuditAction` and one `record()` call in the relevant service — minimal ceremony.

**Accepted trade-offs:**

- Every critical operation now involves an extra DB write. This is intentional and acceptable; audit safety is a higher priority than minimising write latency.
- The `audit_logs` table will grow without bound. Archiving or partitioning by date is a future operational concern; schema design does not preclude it.
- The `details` JSON column sacrifices queryability for flexibility. Individual fields from `details` are not indexed. If specific detail fields need to be filtered frequently, they should be promoted to first-class columns — deferred until the need materialises.

## Alternatives Considered

- **Log-only approach (no DB table)**: rejected — logs are ephemeral, unqueryable by SQL, not actor-aware, and subject to rotation.
- **Separate audit database**: rejected — operational overhead without benefit at current scale; a single-schema table in the same PostgreSQL instance is sufficient.
- **Event sourcing / immutable event log**: over-engineered for the current feature set; the simple append-only table achieves the same traceability goal with a fraction of the complexity.
- **Third-party audit library**: no Python library adds meaningful value over the thin component described here; the domain-specific `AuditAction` enum would still need to be maintained regardless.

## References

- [ADR-009: Python's Native Logging](009-native-logging-over-fastapi.md)
- [ADR-013: Async Purchase Confirmation](013-async-purchase-confirmation.md)
- [ADR-014: In-Process Broker and Scheduler](014-in-process-broker-and-scheduler.md)
- [ADR-023: Event-Driven Audit Logging](023-event-driven-audit-logging.md) (current implementation pattern)
- [NFR-10: Logging & Observability](../../specs/non-functional/10-logging-observability.md)
- [Data Model](../data-model.md)
