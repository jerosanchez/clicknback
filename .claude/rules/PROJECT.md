---
name: project
type: rule
description: ClickNBack product overview, entities, roles, and tech stack
---

# PROJECT

ClickNBack is a production-grade cashback platform backend demonstrating real-world financial correctness, idempotency, and concurrency safety.

## Product Overview

- **Users earn cashback** on purchases at partner merchants; the platform tracks balances, manages rewards, and processes withdrawals.
- **Financial rigor**: All monetary values use `Decimal`, never `float`. Every transaction is idempotent and concurrency-safe.
- **Domain model**: User, Merchant, Offer, Purchase, CashbackTransaction, Wallet, Payout.
- **State machines**: Purchase (`pending → confirmed | reversed`) and CashbackTransaction (mirrors purchase states).
- **Wallet model**: Tracks three buckets per user: `pending`, `available`, `paid`; updated atomically within transactions.
- **Withdrawal safety**: Uses `SELECT FOR UPDATE` row-level locking to prevent race conditions.

## Roles

| Role | Capabilities |
|------|--------------|
| **User** | Registers, owns wallet, views purchases, requests payouts |
| **Admin** | Manages merchants, creates offers, approves/rejects payouts, views audit trail |
| **System** | Background jobs, event publishing (internal use only) |

## Domain Entities

| Entity | Purpose |
|--------|---------|
| **User** | Registered user with active flag, email, password (bcrypt+salt) |
| **Merchant** | Partner store; defines default cashback percentage, active flag |
| **Offer** | Defines reward: percentage or fixed amount, validity period, per-user monthly cap, active flag |
| **Purchase** | Transaction: external_id (unique), status, amount, currency, date, idempotency guarantee |
| **CashbackTransaction** | Records reward earned; mirrors purchase state (pending/confirmed/reversed) |
| **Wallet** | Per-user balance tracking: pending, available, paid buckets; atomically updated |
| **Payout** | Withdrawal request: amount, status (pending/approved/rejected/paid), audit trail |

## Tech Stack

- **Language**: Python ≥ 3.13
- **Framework**: FastAPI (async HTTP)
- **Database**: PostgreSQL + SQLAlchemy (async, SQLAlchemy 2.0 style)
- **Authentication**: JWT (python-jose) + bcrypt (passlib)
- **Migrations**: Alembic (declarative)
- **Testing**: pytest (unit, integration, E2E)
- **Message Broker**: In-process broker (can upgrade to external queue)
- **Scheduler**: In-process scheduler (can upgrade to external job queue)

## Currency Policy

- **EUR only**: All purchases, offers, and wallets are EUR. No multi-currency support.
- See [ADR-011](../../docs/design/adr/011-eur-only-currency-policy.md).

## Key Constraints

- Purchases are idempotent by `external_id` (unique DB constraint); re-submission yields a conflict.
- Errors follow a standard JSON shape: `{ "error": { "code", "message", "details" } }`.
- All async operations use `AsyncSession` (SQLAlchemy 2.0 style `select()`).
- No blocking I/O in request handlers; all DB operations are async.
- Domain exceptions (not HTTPException) raised in services/policies; translated to HTTP errors in API layer.

---
