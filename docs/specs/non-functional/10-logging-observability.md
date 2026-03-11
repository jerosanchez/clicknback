# NFR-10: Logging & Observability

## Overview

The system maintains two complementary and independent logging layers:

1. **Runtime logging** — structured log lines emitted to stdout via Python's native `logging` module. Used for debugging, performance monitoring, and alerting.
2. **Persistent audit trail** — critical operations are additionally written to the `audit_logs` database table, providing a durable, queryable record of who did what, when, and with what outcome. Used for traceability, compliance, and incident investigation.

Both layers are always active for auditable operations. They are not interchangeable: runtime logs are ephemeral and subject to rotation; audit rows are permanent application records.

## Motivation

In a financial system, logs are essential for regulatory compliance, fraud detection, and incident investigation. Unstructured or incomplete logs make debugging difficult and can result in compliance violations. Observability enables proactive monitoring of system health.

Additionally, for critical state-changing operations (purchase confirmation, withdrawal processing, manual admin overrides), answering *"who did this, when, and why?"* must not depend on log files that may be rotated or lost. A persistent, database-backed audit trail provides the authoritative answer.

## Definition

### Runtime Logging

- All financial transactions, state changes, and errors are logged with structured data.
- Logs include context: user ID, request ID, operation, timestamp, duration, outcome.
- Log levels are used appropriately: INFO (business events), WARN (recoverable issues), ERROR (failures).
- Logs are centralized and searchable; retention follows compliance requirements.

### Persistent Audit Trail

- Every critical operation writes a row to `audit_logs` with: actor type, actor ID, action, affected resource, outcome, and an action-specific JSON payload.
- "Critical operations" include, but are not limited to: purchase confirmation/rejection, cashback crediting, withdrawal request, payout processing, merchant/offer activation, and any manual admin override.
- Audit rows are append-only and never updated or deleted.
- The `actor_type` field distinguishes system-initiated operations (background jobs, event handlers) from human-initiated ones (admin, user). System operations set `actor_id` to null.

## Acceptance Criteria

- Every wallet debit/credit operation produces both a structured log line and an audit row.
- Every purchase confirmation/rejection produces an audit row with purchase ID, actor type, amount, and reason (if rejected).
- Every critical API action by an admin produces an audit row with the admin's user ID.
- Every API request logs: method, path, status_code, duration_ms, user_id, error (if any) — runtime log only.
- Logs are structured with consistent field names and types.
- Audit rows are queryable by `actor_id`, `action`, `resource_type`, `resource_id`, and `occurred_at`.

## Technical Approach

### Runtime Logging

- Uses Python's native `logging` module configured in `app/core/logging.py` (see ADR-009).
- `ExtraDictFormatter` appends structured `extra=` keyword arguments to log lines.
- All modules obtain a logger via `logging.getLogger(__name__)`.
- Log to stdout; container/logging agent handles centralization.

### Persistent Audit Trail

- `app/core/audit.py` provides all audit infrastructure: `AuditActorType` enum, `AuditAction` enum, `AuditLog` ORM model, `AuditTrailRepositoryABC` / `AuditTrailRepository`, and the `AuditTrail` service class.
- `AuditTrail.record(...)` writes the audit row to the database **and** emits a corresponding `INFO` log line — both always happen together.
- `AuditTrail` is injected into feature services via `__init__()`, following the standard dependency injection pattern. It is wired by `composition.py` and overridden in tests using `AuditTrailRepositoryABC`.
- See [ADR-015: Persistent Audit Trail](../../design/adr/015-persistent-audit-trail.md) for full rationale and design details.

## Auditable Actions

The following actions must produce an audit row. The list grows as features are implemented:

| Action constant                | Resource type   | When                                             |
|------------------------------- | --------------- | ------------------------------------------------ |
| `PURCHASE_CONFIRMED`           | purchase        | Background job successfully confirms a purchase  |
| `PURCHASE_REJECTED`            | purchase        | Background job exhausts retries and rejects      |
| `CASHBACK_CREDITED`            | wallet          | Cashback amount credited to user wallet          |
| `WITHDRAWAL_REQUESTED`         | payout          | User submits a withdrawal request                |
| `WITHDRAWAL_PROCESSED`         | payout          | Payout is settled (success or failure)           |
| `PURCHASE_REVERSED`            | purchase        | Purchase reversal triggered                      |
| `MERCHANT_ACTIVATED`           | merchant        | Admin activates or deactivates a merchant        |
| `OFFER_ACTIVATED`              | offer           | Admin activates or deactivates an offer          |
