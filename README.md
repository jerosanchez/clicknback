<!-- markdownlint-disable MD041 -->
![CI](https://github.com/jerosanchez/clicknback/actions/workflows/ci.yml/badge.svg)
![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)
![status: early development](https://img.shields.io/badge/status-early%20development-orange)
<!-- markdownlint-enable MD041 -->

# ClickNBack – Backend Engineering Demo

**A production-grade cashback platform backend built to demonstrate senior-level Python engineering.**

Built with **Python 3.13** | **FastAPI** | **PostgreSQL** | **SQLAlchemy** | **Alembic** | **pytest**

---

## What This Project Is

ClickNBack models how a real cashback application works: users earn rewards on purchases at partner merchants. The platform ingests purchase events, calculates cashback, manages user wallets (pending, available, and paid balances), and processes withdrawals.

The system is intentionally small in surface area but deep in engineering rigor. It is not a tutorial or scaffold — it is a working backend demonstrating the kind of decisions, tradeoffs, and discipline expected in a production codebase.

---

## What This Showcases

- **Layered architecture** — strict separation between HTTP routing, business logic, and data access, with each layer only knowing about the layer directly below it
- **Dependency injection** — services receive all dependencies (repositories, policy callables, token providers) via constructors; FastAPI `Depends()` handles wiring at the boundary
- **Repository pattern with ABCs** — data access sits behind abstract interfaces, enabling full unit testing without touching the database
- **Business rule isolation** — policies are pure functions that raise domain exceptions; services orchestrate them; the API layer translates to HTTP
- **Consistent error handling** — a layered pipeline from domain exception → `HTTPException` → normalized JSON response `{ "error": { "code", "message", "details" } }`
- **Financial precision** — `Decimal` for all monetary values; row-level locking (`SELECT FOR UPDATE`) for wallet updates
- **Idempotency** — purchases keyed by external ID to prevent double-crediting
- **Test discipline** — unit tests (mocked dependencies via `create_autospec`), API-level tests (HTTP via `TestClient` + `dependency_overrides`), and integration tests; full coverage reporting
- **Modular monolith** — module boundaries are explicit and ready for extraction into separate services if the system grows

---

## Feature Progress

| Feature | Domain | Status |
| --- | --- | --- |
| **Authentication** | | |
| User Login | Auth | 🟢 done |
| **User Management** | | |
| User Registration | Users | 🟢 done |
| **Merchant Management** | | |
| Merchant Creation | Merchants | 🟢 done |
| Merchants Listing | Merchants | 🟢 done |
| Merchant Activation | Merchants | 🟢 done |
| **Offer Management** | | |
| Offer Creation | Offers | ⚪ planned |
| Offers Listing | Offers | ⚪ planned |
| Active Offers Listing | Offers | ⚪ planned |
| Offer Activation | Offers | ⚪ planned |
| Offer Details | Offers | ⚪ planned |
| **Purchase & Cashback** | | |
| Purchase Ingestion (Webhook) | Purchases | ⚪ planned |
| Purchase Confirmation | Purchases | ⚪ planned |
| Purchase Details | Purchases | ⚪ planned |
| Purchases Listing | Purchases | ⚪ planned |
| Cashback Calculation Engine | Purchases | ⚪ planned |
| Purchase Reversal | Purchases | ⚪ planned |
| **Wallet Management** | | |
| Wallet Summary | Wallets | ⚪ planned |
| Wallet Transactions Listing | Wallets | ⚪ planned |
| **Payouts** | | |
| Payout Request (Withdrawal) | Payouts | ⚪ planned |
| Payout Processing | Payouts | ⚪ planned |
| Payouts Listing | Payouts | ⚪ planned |

---

## Quick Start

```bash
# Install dependencies and start the database
make install
make up

# Run the test suite
make test
```

The API is available at `http://localhost:8000`. Interactive docs (Swagger UI) are at `http://localhost:8000/docs`.

---

## Navigating the Code

The application lives under `app/`. Every domain is a self-contained module (e.g., `app/users/`, `app/merchants/`) that follows the same layered structure:

- `api.py` — HTTP routing only: receives requests, calls the service, maps exceptions to responses
- `services.py` — business logic orchestration; no HTTP knowledge; fully injectable and unit-testable
- `policies.py` — pure functions enforcing individual business rules; raise domain exceptions on violation
- `repositories.py` — data access behind an ABC; the concrete implementation uses SQLAlchemy
- `models.py`, `schemas.py` — ORM models and Pydantic request/response schemas respectively
- `exceptions.py`, `errors.py` — domain exceptions and module-level HTTP error codes
- `composition.py` — wires concrete implementations together for FastAPI `Depends()`

Cross-cutting infrastructure (config, DB session factory, JWT, logging, error builders) lives in `app/core/`.

Tests mirror the module structure under `tests/`. The `conftest.py` at the root provides factory fixtures used across all test suites.

For a detailed walkthrough of each layer, its responsibilities, and the architectural rationale, see [docs/agents/project-context.md](docs/agents/project-context.md).

---

## Architecture Decisions

Significant design choices are documented as Architecture Decision Records (ADRs) under [`docs/design/adr/`](docs/design/adr/). Each record captures the context, the options considered, and the reasoning behind the decision taken — including what was explicitly rejected and why.

Topics covered include:

- [Technology stack selection](docs/design/adr/000-technology-stack-selection.md) — why FastAPI, SQLAlchemy, and PostgreSQL
- [Modular monolith approach](docs/design/adr/001-adopt-modular-monolith-approach.md) — explicit module boundaries designed for future extraction
- [API module as composition root](docs/design/adr/003-api-module-as-composition-root.md) — where and how dependencies are wired
- [JWT stateless authentication](docs/design/adr/008-jwt-stateless-authentication.md) — token strategy and tradeoffs
- [Layered testing strategy](docs/design/adr/007-layered-testing-strategy.md) — unit, API-level, and integration test boundaries

The full index is at [`docs/design/adr-index.md`](docs/design/adr-index.md).

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions, development workflow, and code quality requirements.
