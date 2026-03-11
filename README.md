<!-- markdownlint-disable MD041 -->

![ClickNBack banner](/docs/clicknback-banner.png)

![CI](https://github.com/jerosanchez/clicknback/actions/workflows/ci.yml/badge.svg)
![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?logo=fastapi)
[![security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)
![status: early development](https://img.shields.io/badge/status-early%20development-orange)
<!-- markdownlint-enable MD041 -->

**A production-grade cashback platform backend built to showcase senior-level Python engineering.**

---

## What This Project Is

ClickNBack models how a real cashback application works: users earn rewards on purchases at partner merchants. The platform ingests purchase events, verifies them asynchronously via a background job (simulating bank reconciliation), publishes confirmation/rejection and other events to an internal message broker, calculates cashback, manages user wallets (pending, available, and paid balances), and processes withdrawals.

A complete [glossary](/docs/specs/domain-glossary.md) and [product spec documents](/docs/specs/) are available to better understand the business domain.

The system is intentionally small in surface area but deep in engineering rigor. It is not a tutorial or scaffold — it is a working backend continuously deployed to a real VPS, publicly accessible (see the [Try the Live API](#try-the-live-api) section below), demonstrating the kind of decisions, tradeoffs, and discipline expected in a production codebase.

If you want to understand this particular business domain and test the system end-to-end without reading all the documentation, you can also [explore the workflows](#explore-the-workflows) directly from your VS Code using a curated series of step by step, extensively commented HTTP request files.

Product specs are still evolving, see the [feature roadmap](#feature-roadmap) to see an up-to-date feature availability status.

---

## What This Showcases

- **Layered architecture** — strict separation between HTTP routing, business logic, and data access, with each layer only knowing about the layer directly below it
- **Dependency injection** — services receive all dependencies (repositories, policy callables, token providers) via constructors; FastAPI `Depends()` handles wiring at the boundary
- **Repository pattern with ABCs** — data access sits behind abstract interfaces, enabling full unit testing without touching the database
- **Business rule isolation** — policies are pure functions that raise domain exceptions; services orchestrate them; the API layer translates to HTTP
- **Consistent error handling** — a layered pipeline from domain exception → `HTTPException` → normalized JSON response `{ "error": { "code", "message", "details" } }`
- **Financial precision** — `Decimal` for all monetary values; row-level locking (`SELECT FOR UPDATE`) for wallet updates
- **Idempotency** — purchases keyed by external ID to prevent double-crediting
- **Internal message broker** — a simple in-memory pub/sub component enables decoupled communication between background jobs, domain services, and future modules (e.g., notifications)
- **Persistent audit trail** — every critical operation (purchase confirmation, cashback crediting, withdrawal, admin actions) writes an append-only row to `audit_logs`, providing durable, queryable traceability independent of log rotation
- **Test discipline** — unit tests (mocked dependencies via `create_autospec`), API-level tests (HTTP via `TestClient` + `dependency_overrides`), and integration tests; full coverage reporting
- **Modular monolith** — module boundaries are explicit and ready for extraction into separate services if the system grows

---

## Feature Roadmap

Last updated: 2026.03.05

_Status legend:_

- 🟢 done: Fully implemented and already available
- 🟡 ongoing: Currently working on this feature, expected in the next days/week
- ⚪ backlog: Queued for development, expected in the short-term
- ⚫ planned: Feature is considered for future development, timing is uncertain

| Feature | Domain | Status |
| --- | --- | --- |
| **Authentication** | | |
| User Login | Auth | 🟢 done |
| User Logout | Auth | ⚫ planned |
| **User Management** | | |
| User Registration | Users | 🟢 done |
| User Details (profile) | Users | ⚫ planned |
| User Listing | Users | ⚫ planned |
| User Update | Users | ⚫ planned |
| User Deletion | Users | ⚫ planned |
| **Merchant Management** | | |
| Merchant Creation | Merchants | 🟢 done |
| Merchants Listing | Merchants | 🟢 done |
| Merchant Activation | Merchants | 🟢 done |
| Merchant Details | Merchants | ⚫ planned |
| Merchant Update | Merchants | ⚫ planned |
| Merchant Deletion | Merchants | ⚫ planned |
| **Offer Management** | | |
| Offer Creation | Offers | 🟢 done |
| Offers Listing | Offers | 🟢 done |
| Active Offers Listing | Offers | 🟢 done |
| Offer Activation | Offers | 🟢 done |
| Offer Details | Offers | 🟢 done |
| Offer Update | Offers | ⚫ planned |
| Offer Deletion | Offers | ⚫ planned |
| **Purchase & Cashback** | | |
| Purchase Ingestion | Purchases | 🟢 done |
| Purchase Confirmation | Purchases | 🟢 done |
| Purchase Details | Purchases | 🟢 done |
| Purchases Listing | Purchases | 🟢 done |
| User Purchases Listing | Purchases | 🟡 ongoing |
| Cashback Calculation Engine | Purchases | ⚪ backlog |
| Purchase Reversal | Purchases | ⚪ backlog |
| **Wallet Management** | | |
| Wallet Summary | Wallets | ⚪ backlog |
| Wallet Transactions Listing | Wallets | ⚪ backlog |
| **Payouts** | | |
| Payout Request (Withdrawal) | Payouts | ⚪ backlog |
| Payout Processing | Payouts | ⚪ backlog |
| Payouts Listing | Payouts | ⚪ backlog |
| **Notifications** | | |
| Purchase Creation Notification | Notifications | ⚫ planned |
| Purchase Confirmation Notification | Notifications | ⚫ planned |
| Purchase Reversal Notification | Notifications | ⚫ planned |
| Payout Processing Notification | Notifications | ⚫ planned |
| **AI & Augmented Features** | | |
| Fraud Scoring | AI | ⚫ planned |
| Smart Offer Recommendations | AI | ⚫ planned |
| Automated FAQ/Support Chatbot | AI | ⚫ planned |
| Fraud Pattern Detection | AI | ⚫ planned |
| Personalized Cashback Insights | AI | ⚫ planned |
| Natural Language Query for Admins | AI | ⚫ planned |

---

## Try the Live API

The API is continuosly deployed at **<https://clicknback.com>**. No setup required.

- **Interactive docs (Swagger UI):** <https://clicknback.com/docs>
- **Demo admin credentials:** `carol@clicknback.com` / `Str0ng!Pass` — use these to access admin-only endpoints
- **Self-register:** anyone can create a personal account via `POST /api/v1/users`
- **Nightly reset:** the database resets every night at 03:00 UTC — any data you create will not persist
- **Rate limits:** login and registration are capped at 5 requests/min per IP; all other endpoints at 60 requests/min per IP — you will get a `429` if you exceed these
- _This is a shared demo environment; please be considerate._

---

## Explore the Workflows

If you want to understand the business domain and test the system end-to-end without reading all the documentation, start here:

**[End-to-End Workflows guide](docs/specs/workflows/end-to-end-workflows.md)** — a plain-language walkthrough of the four main business flows, explained from the user's perspective: admin setup, offer discovery, purchase & cashback, and wallet & payouts.

The guide comes with ready-to-run `.http` request sequences (compatible with the [VS Code REST Client](https://marketplace.visualstudio.com/items?itemName=humao.rest-client) extension) that target the live API and can be executed step-by-step to simulate each workflow manually:

| File | Workflow | Status |
| --- | --- | --- |
| [`01-admin-platform-setup.http`](docs/specs/workflows/http/01-admin-platform-setup.http) | Create and activate a merchant and an offer | 🟢 live |
| [`02-user-discovery.http`](docs/specs/workflows/http/02-user-discovery.http) | Register, log in, and browse active offers | 🟢 live |

 | [`03-purchase-and-cashback.http`](docs/specs/workflows/http/03-purchase-and-cashback.http) | Ingest a purchase, wait for async confirmation, verify cashback | ⚪ backlog |
| [`04-wallet-and-payout.http`](docs/specs/workflows/http/04-wallet-and-payout.http) | Check wallet balances and process a withdrawal | ⚪ backlog |

_The backlog files document the intended API surface for upcoming features — useful for understanding the domain model even before the endpoints are implemented._

_No local installation required, the requests hit the public API directly._

---

## Architecture Decisions

Significant design choices are documented as Architecture Decision Records (ADRs) under [`docs/design/adr/`](docs/design/adr/). Each record captures the context, the options considered, and the reasoning behind the decision taken — including what was explicitly rejected and why.

Topics covered include:

- [Technology stack selection](docs/design/adr/000-technology-stack-selection.md) — why FastAPI, SQLAlchemy, and PostgreSQL
- [Modular monolith approach](docs/design/adr/001-adopt-modular-monolith-approach.md) — explicit module boundaries designed for future extraction
- [API module as composition root](docs/design/adr/003-api-module-as-composition-root.md) — where and how dependencies are wired
- [JWT stateless authentication](docs/design/adr/008-jwt-stateless-authentication.md) — token strategy and tradeoffs
  - [Layered testing strategy](docs/design/adr/007-layered-testing-strategy.md) — unit, API-level, and integration test boundaries
  - [Async purchase confirmation](docs/design/adr/013-async-purchase-confirmation.md) — event-driven, background-verified confirmation and decoupled cashback allocation
  - [Persistent audit trail](docs/design/adr/015-persistent-audit-trail.md) — durable, queryable record of every critical operation for traceability and compliance

The full index is at [`docs/design/adr-index.md`](docs/design/adr-index.md).

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions, development workflow, code quality requirements, and code organization guidelines.
