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

### Component: `app/core/audit.py`

A single file containing all audit infrastructure:

- **`AuditActorType`** — string enum: `system` | `admin` | `user`.
- **`AuditAction`** — string enum listing every auditable action (e.g. `PURCHASE_CONFIRMED`, `WITHDRAWAL_PROCESSED`). New actions are added here as features are implemented.
- **`AuditLog`** — SQLAlchemy ORM model mapped to the `audit_logs` table.
- **`AuditTrailRepositoryABC`** and **`AuditTrailRepository`** — the repository pair following the project's standard pattern (ABCs enable mocking in unit tests).
- **`AuditTrail`** — the thin service class injected into feature services. Exposes a single primary method: `record(...)`. Internally, it both persists the row *and* emits a structured log line via the root Python logger, so the runtime log and the DB record are always in sync.
- **`get_audit_trail()`** — FastAPI `Depends()` factory that provides a fully wired `AuditTrail` instance; accepts `AsyncSession` so the audit write participates in the same transaction as the business operation when needed.

### `audit_logs` table

| Field          | Type     | Constraints / Notes                                          |
|----------------|----------|--------------------------------------------------------------|
| id             | UUID     | PK                                                           |
| occurred_at    | datetime | UTC timestamp; set by the application, not a DB default      |
| actor_type     | string   | `system` \| `admin` \| `user`                               |
| actor_id       | string   | UUID of the acting user/admin; `null` when actor_type=system |
| action         | string   | `AuditAction` string enum member                             |
| resource_type  | string   | Domain entity type: `purchase`, `payout`, `merchant`, etc.  |
| resource_id    | string   | UUID of the affected resource                                 |
| outcome        | string   | `success` \| `failure`                                      |
| details        | JSON     | nullable; action-specific payload (amounts, status change, reason, etc.) |

### Usage pattern in services

Services that perform auditable operations receive an `AuditTrail` instance via `__init__()`, alongside their other dependencies:

```python
class PurchaseService:
    def __init__(
        self,
        purchase_repository: PurchaseRepositoryABC,
        audit_trail: AuditTrail,
    ): ...

    async def confirm_purchase(self, purchase_id: str, db: AsyncSession) -> Purchase:
        purchase = await self._confirm_internally(purchase_id, db)
        await self.audit_trail.record(
            db=db,
            actor_type=AuditActorType.SYSTEM,
            actor_id=None,
            action=AuditAction.PURCHASE_CONFIRMED,
            resource_type="purchase",
            resource_id=purchase.id,
            outcome="success",
            details={"amount": str(purchase.amount), "merchant_id": purchase.merchant_id},
        )
        return purchase
```

The `record()` call is placed **after** the business operation succeeds. If the operation fails and raises an exception, no audit row is written — which accurately reflects the outcome.

For manual admin operations, `actor_type=AuditActorType.ADMIN` and `actor_id` is set to the authenticated user's ID, obtained from the route handler and passed down to the service.

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
- [NFR-10: Logging & Observability](../../specs/non-functional/10-logging-observability.md)
- [Data Model](../data-model.md)
