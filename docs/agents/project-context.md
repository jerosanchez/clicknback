# ClickNBack – Project Context

This document provides a self-contained reference for AI agents (and human developers) to understand the ClickNBack project: its purpose, domain, architecture, and engineering philosophy. It deliberately avoids referencing specific internal documents, keeping explanations at a level of purpose and strategy rather than current implementation detail.

---

## 1. Project Purpose

**ClickNBack** is a production-grade cashback platform backend that models how modern cashback applications operate. It is intentionally small in surface area but deep in engineering rigor.

The system enables:

- Users to earn cashback on purchases made at partner merchants.
- Merchants to be registered and associated with cashback offer configurations.
- The platform to track purchases, calculate rewards, manage pending/confirmed balances, and process withdrawals.
- Administrators to manage the platform and enforce business rules.

The primary goal is to simulate a **real-world financial incentive system** — one that demands correctness, concurrency safety, idempotency, and fraud-awareness — within a compact, well-structured codebase. It is not an academic exercise: the engineering decisions reflect genuine production concerns.

---

## 2. Domain Concepts

| Concept | Description |
| --- | --- |
| **User** | Registers in the system and earns cashback. Roles: `user`, `admin`. |
| **Merchant** | A partner business with configured cashback terms. Can be activated or deactivated. |
| **Offer** | A time-bound reward rule attached to a merchant — percentage or fixed cashback, with optional per-user monthly caps. Only one active offer per merchant at a time. |
| **Purchase** | An external transaction event ingested into the system via API (simulating an affiliate webhook). The idempotency key is the external purchase ID. Starts in `pending` state. |
| **Cashback Transaction** | An internal reward record generated from a purchase. Tracks its own state independently from the purchase. |
| **Wallet** | Tracks three balance buckets per user: `pending`, `available`, and `paid`. Consistency under concurrent writes is a hard requirement. |
| **Payout** | A user-initiated request to move `available` balance into `paid`. Requires row-level locking to prevent race conditions. |

---

## 3. Core System Flows

### User Registration and Authentication

Users register with email and password. Passwords are hashed with bcrypt. Authentication uses JWT Bearer tokens containing user ID and role. Tokens have a configurable TTL. Role-based access control is enforced at the API layer: some endpoints are user-only, others are admin-only, and some are public.

### Merchant and Offer Management (Admin)

Administrators create merchants and define cashback offers. Offers specify reward type (percentage or fixed), a validity period, and an optional monthly cap per user. Merchants and offers can be activated or deactivated. Business rules around cashback percentage limits and offer validity are enforced as explicit policy checks.

### Purchase Ingestion

Purchases arrive as API calls with an external purchase ID, user ID, merchant ID, purchase amount, and currency. The system:

1. Validates idempotency (rejects duplicates at DB level via a unique constraint).
2. Identifies the active offer for the merchant.
3. Calculates cashback (applying caps, rounding rules, and limits).
4. Creates a `Purchase` record (`pending`) and a `CashbackTransaction` record (`pending`).
5. Increments the user's pending wallet balance.

All of these steps happen inside a single database transaction.

### Cashback Confirmation

When a purchase is externally confirmed (e.g., merchant settlement):

- The purchase moves from `pending` → `confirmed`.
- The cashback transaction moves from `pending` → `available`.
- The wallet's pending balance decreases and available balance increases.

### Purchase Reversal

If a purchase is canceled or reversed:

- The purchase moves to `reversed`.
- The cashback transaction moves to `reversed`.
- The wallet is adjusted: pending balance decreases (if not yet confirmed) or available balance decreases (if previously confirmed).

Reversals must be handled correctly in both pre- and post-confirmation states.

### Withdrawal (Payout Request)

Users request withdrawal of their available balance. The system:

1. Validates sufficient available balance.
2. Acquires a row-level lock on the wallet (`SELECT FOR UPDATE`).
3. Deducts available balance and increases paid balance.
4. Creates a payout record for auditability.

Concurrency safety is a hard requirement: concurrent withdrawal requests must not result in overdrafts.

---

## 4. Tech Stack

| Component | Library/Tool |
| --- | --- |
| Web framework | FastAPI |
| ORM | SQLAlchemy (sync, `sessionmaker`) |
| Database | PostgreSQL |
| Migrations | Alembic |
| Password hashing | `passlib` + `bcrypt` |
| JWT | `python-jose` |
| Settings | `pydantic-settings` |
| Testing | `pytest`, `pytest-cov` |
| Linting/formatting | `ruff`, `black`, `flake8`, `pylint` |
| Python | ≥ 3.13 |

---

## 5. Architecture

### Modular Monolith

ClickNBack is structured as a **modular monolith**: a single deployable unit whose internals are organized into well-bounded domain modules. Each module owns its models, business logic, and API surface. Cross-module communication happens through explicit client abstractions rather than direct imports of internal components.

This structure supports independent development of features while maintaining transactional consistency and operational simplicity. If a module needed to become a microservice in the future, the client abstraction layer would be the only seam that needs to change.

### Layered Architecture

Within each module, a strict layering is enforced:

```text
HTTP (api.py) → Business Logic (services.py + policies.py) → Data Access (repositories.py) → Database
```

Each layer only depends on the layer directly below it. HTTP concepts (status codes, request/response bodies) never leak into the service layer. Database concerns never leak into the API layer.

### Project Structure

```text
app/
  main.py              ← FastAPI app factory + router registration
  models.py            ← Central Alembic model discovery import
  core/                ← Cross-cutting infrastructure (config, DB, auth, error handling, logging)
  auth/                ← Authentication module
  users/               ← Users module
  merchants/           ← Merchants module
  offers/              ← Offers module
  purchases/           ← Purchases module
  wallets/             ← Wallets module
  payouts/             ← Payouts module
tests/
  conftest.py          ← Shared pytest fixtures (factories)
  auth/ users/ merchants/ ...
alembic/               ← DB migration scripts
docs/
seeds/                 ← SQL seed data
pyproject.toml
```

### Module Inventory

| Module | Responsibility |
| --- | --- |
| **Users** | Registration, password management, user lookup |
| **Auth** | Login, JWT issuance and validation, RBAC dependencies |
| **Merchants** | Merchant profiles, activation/deactivation |
| **Offers** | Cashback offer definitions, validity windows, per-user caps |
| **Purchases** | Purchase ingestion, idempotency, state transitions, reversal |
| **Wallets** | Balance tracking (pending/available/paid), concurrency-safe updates |
| **Payouts** | Withdrawal requests, payout processing, settlement records |
| **Core** | Config, DB sessions, logging, current-user dependencies, error infrastructure |

---

## 6. Core Engineering Concerns

### Financial Precision

All monetary values use `Decimal`, never `float`. Rounding is deterministic and applied consistently. This is non-negotiable for a financial system.

### Idempotency

Purchases are keyed by an external purchase ID with a database-level unique constraint. Submitting the same purchase twice returns a conflict rather than creating a duplicate reward.

### Concurrency Safety

Wallet balance updates use `SELECT FOR UPDATE` row-level locking to prevent race conditions under concurrent withdrawal requests or simultaneous confirmations. Database transactions wrap all multi-step financial operations.

### State Machines

Purchases and cashback transactions follow explicit state machines with only the defined transitions permitted. Invalid transitions are rejected as domain violations.

### Auditability

Every financial state change is logged. Structured logging with extra context fields (user ID, purchase ID, amounts) is used throughout. Every wallet change is traceable to a source event.

### Fraud Prevention

The system enforces: duplicate detection via idempotency keys, monthly cashback caps per user per offer, and (optionally) rate limiting on purchase ingestion.

### Error Handling

All errors follow a consistent JSON shape:

```json
{
  "error": {
    "code": "SEMANTIC_ERROR_CODE",
    "message": "Human-readable description.",
    "details": { "contextual": "data" }
  }
}
```

Domain exceptions raised in the business logic layer are caught at the API layer and converted to appropriately shaped HTTP responses. No domain exception escapes the API boundary unhandled.

---

## 7. Testing Strategy

Three levels of tests are employed:

- **Unit tests** cover services and policies in complete isolation. Repositories are replaced with `create_autospec` mocks. No database is required.
- **API-level tests** exercise the full HTTP layer (routing, request parsing, error mapping, response shape) without a database. FastAPI's `dependency_overrides` mechanism replaces services and DB sessions with controlled fakes.
- **Integration/E2E tests** run against a real test database and exercise the full request path including persistence.

Tests for each feature module live under `tests/<module>/` and mirror the module structure. Shared model factories in `tests/conftest.py` provide customizable test data builders using `**kwargs` defaults.

---

## 8. Design Principles

1. **Layered architecture**: each layer has a single responsibility and depends only on the layer below.
2. **Business logic is isolated**: services and policies never import FastAPI, HTTP status codes, or HTTP exceptions.
3. **Dependencies are injected**: services receive callables and repository abstractions via their constructor. Concrete wiring happens in `composition.py`.
4. **Testability by design**: abstract repository interfaces enable mocking; dependency overrides enable HTTP-layer testing without infrastructure.
5. **Consistent error shape**: all error responses follow the standard `{ "error": { "code", "message", "details" } }` envelope.
6. **DB is the source of truth**: constraints are enforced at both the application and database level (unique indexes, NOT NULL, foreign keys).
7. **Explicit over implicit**: error codes are enums, not strings. State transitions are named and validated. No surprise side-effects.
8. **Financial correctness first**: monetary precision, transactional atomicity, and concurrency safety are treated as hard constraints, not optimizations.
