<!-- markdownlint-disable MD041 -->

![ClickNBack banner](/docs/clicknback-banner.png)

![CI](https://github.com/jerosanchez/clicknback/actions/workflows/ci.yml/badge.svg)
![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?logo=fastapi)
[![security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)
![coverage: 89%](https://img.shields.io/badge/coverage-89%25-brightgreen)
![status: actively maintained](https://img.shields.io/badge/status-actively%20maintained-green)

<!-- markdownlint-enable MD041 -->

**A production-grade cashback platform backend.** Live at [clicknback.com](https://clicknback.com/docs) — no setup required.

This is a reference implementation, not a startup — there are no paying customers, and no shortcuts taken because of it. It was built exactly the way it would need to be built for a real company: financial precision, idempotency guarantees, row-level locking, documented tradeoffs, and a CI/CD pipeline enforcing quality on every commit. Zero external pressure. Zero compromises.

Built during a deliberate sabbatical by a software engineer who previously shipped to millions of users — 6+ years as a mobile engineer and 1+ year as a backend engineer, both at scale-up startups. Every architectural decision is documented, justified, and open for technical review.

---

## The Story

ClickNBack did not emerge from a tutorial. It was built during a deliberate sabbatical — the chance to take the time to build something properly, with the right constraints, and document every decision along the way. The full journey is on the blog:

- **Why the sabbatical**: [A Sabbatical With Intent](https://jerosanchez.com/posts/20251203-a-sabbatical-with-intent/) — context, intent, and what "building with intent" looks like in practice
- **Why this domain**: [The Pivot: Why I Dropped a Marketplace for a Cashback System](https://jerosanchez.com/posts/20260321-the-pivot-why-i-dropped-a-marketplace/) — why financial systems were the right backdrop, not a tutorial topic
- **The technical tour**: [Before You Ask: What You'll Find If You Read ClickNBack](https://jerosanchez.com/posts/20260323-before-you-ask/) — guided walkthrough of the ADRs, the architecture, the tests, and the honest tradeoffs

_If you are a recruiter or hiring manager evaluating this project, the technical tour post is the most efficient starting point._

---

## What This Project Is

ClickNBack models how a real cashback application works: users earn rewards on purchases at partner merchants. The platform ingests purchase events, verifies them asynchronously via a background job (simulating bank reconciliation), publishes confirmation/rejection and other events to an internal message broker, calculates cashback, manages user wallets (pending, available, and paid balances), and processes withdrawals.

A complete [glossary](/docs/specs/domain-glossary.md) and [product spec documents](/docs/specs/) are available to better understand the business domain.

The system is continuously deployed to a real VPS with a full CI/CD pipeline — lint, tests (85% coverage hard gate), and security scanning run on every commit. See [Try the Live API](#try-the-live-api) to interact with it directly.

Product specs are still evolving (see the [feature roadmap](#feature-roadmap) to see an up-to-date feature status).

---

## What This Project Showcases

Three design decisions worth examining closely:

- **Financial correctness** — `Decimal` everywhere (never `float`), `SELECT FOR UPDATE` row-level locking on wallet mutations, and idempotency by `external_id`. Money bugs are unrecoverable.
- **[Async purchase confirmation](docs/design/adr/013-async-purchase-confirmation.md)** — purchases are ingested immediately; a background job simulates bank reconciliation before cashback is allocated. Both confirmed and rejected flows are fully handled.
- **[Background job architecture](docs/design/adr/016-background-job-architecture-pattern.md)** — Fan-Out Dispatcher + Per-Item Runner: each task owns its own DB session, retry lifecycle, and in-flight lock. Fully tested in isolation without spawning real asyncio tasks.

The full engineering surface this project demonstrates:

- **Layered architecture** — strict separation between HTTP routing, business logic, and data access, with each layer only knowing about the layer directly below it
- **Dependency injection** — services receive all dependencies (repositories, policy callables, token providers) via constructors; FastAPI `Depends()` handles wiring at the boundary
- **Repository pattern** — data access sits behind abstract interfaces, enabling full unit testing without touching the database
- **Business rule isolation** — policies are pure functions that raise domain exceptions; services orchestrate them; the API layer translates to HTTP
- **Consistent error handling** — a layered pipeline from domain exception → `HTTPException` → normalized JSON response `{ "error": { "code", "message", "details" } }`
- **Financial precision** — `Decimal` for all monetary values; row-level locking (`SELECT FOR UPDATE`) for wallet updates
- **Idempotency** — purchases keyed by external ID to prevent double-crediting
- **Internal message broker** — a simple in-memory pub/sub component enables decoupled communication between background jobs, domain services, and future modules (e.g., notifications)
- **Persistent audit trail** — every critical operation (purchase confirmation, cashback crediting, withdrawal, admin actions) writes an append-only row to `audit_logs`, providing durable, queryable traceability independent of log rotation
- **Background job architecture** — background jobs follow a deliberate _Fan-Out Dispatcher + Per-Item Runner_ pattern: a lightweight dispatcher spawns one independent `asyncio.Task` per pending item on each scheduler tick; each task owns its own retry lifecycle and DB session; an abstracted in-flight tracker prevents duplicate processing; and a swappable Strategy interface decouples the external-system integration from all orchestration logic. The design is fully documented in [ADR-016](docs/design/adr/016-background-job-architecture-pattern.md)
- **Test discipline** — unit tests (mocked dependencies via `create_autospec`), API-level tests (HTTP via `TestClient` + `dependency_overrides`), and integration tests; full coverage reporting; background job components tested in isolation without spawning real asyncio tasks
- **Modular monolith** — module boundaries are explicit and ready for extraction into separate services if the system grows
- **Feature flag system** — a DB-backed flag module (`app/feature_flags/`) allows capabilities to be enabled or disabled at runtime without redeployment; flags are scoped globally or per-merchant/user, enabling targeted demo workflows, safe incident response, and progressive delivery strategies (canary rollouts, A/B tests); resolution is fail-open

---

## Feature Roadmap

Last updated: 2026.03.23

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
| Purchase Confirmation (job) | Purchases | 🟢 done |
| Purchase Confirmation (manual) | Purchases | ⚪ backlog |
| Purchase Details | Purchases | 🟢 done |
| Purchases Listing | Purchases | 🟢 done |
| User Purchases Listing | Purchases | 🟢 done |
| Cashback Calculation | Purchases | 🟢 done |
| Purchase Reversal | Purchases | 🟡 ongoing |
| **Wallet Management** | | |
| Wallet Summary | Wallets | 🟢 done |
| Wallet Transactions Listing | Wallets | 🟢 done |
| **Payouts** | | |
| Payout Request (Withdrawal) | Payouts | ⚪ backlog |
| Payout Processing | Payouts | ⚪ backlog |
| Payouts Listing | Payouts | ⚪ backlog |
| **Feature Flags** | | |
| Set Feature Flag | Feature Flags | ⚪ backlog |
| Delete Feature Flag | Feature Flags | ⚪ backlog |
| List Feature Flags | Feature Flags | ⚪ backlog |
| Evaluate Feature Flag | Feature Flags | ⚪ backlog |
| **Notifications** | | |
| Purchase Creation Notification | Notifications | ⚫ planned |
| Purchase Confirmation Notification | Notifications | ⚫ planned |
| Purchase Reversal Notification | Notifications | ⚫ planned |
| Payout Processing Notification | Notifications | ⚫ planned |
| **AI & Augmented Features** | | |
| Fraud Scoring | AI | ⚫ planned |
| Smart Offer Recommendations | AI | ⚫ planned |
| Automated FAQ/Support Chatbot | AI | ⚪ backlog |
| Fraud Pattern Detection | AI | ⚪ backlog |
| Personalized Cashback Insights | AI | ⚫ planned |
| Natural Language Query for Admins | AI | ⚫ planned |

---

## Try the Live API

The API is continuously deployed at **[clicknback.com/docs](https://clicknback.com/docs)** — no setup required.

See [QUICKSTART.md](QUICKSTART.md) for a complete guided tour: demo credentials, a step-by-step
REST client walkthrough ([http/quickstart.http](http/quickstart.http)), and a curl reference —
the full cashback lifecycle from login to wallet balance in under five minutes.

---

## Architecture Decisions

Twenty-three architectural decisions (and counting) are documented as ADRs under [`docs/design/adr/`](docs/design/adr/). Each record captures the context, the options considered, and the reasoning behind the decision — including what was explicitly rejected and why. This is the paper trail of how a production-grade backend is designed, not just built.

Topics covered include:

- [Technology stack selection](docs/design/adr/000-technology-stack-selection.md) — why FastAPI, SQLAlchemy, and PostgreSQL
- [Modular monolith approach](docs/design/adr/001-adopt-modular-monolith-approach.md) — explicit module boundaries designed for future extraction
- [API module as composition root](docs/design/adr/003-api-module-as-composition-root.md) — where and how dependencies are wired
- [JWT stateless authentication](docs/design/adr/008-jwt-stateless-authentication.md) — token strategy and tradeoffs
- [Layered testing strategy](docs/design/adr/007-layered-testing-strategy.md) — unit, API-level, and integration test boundaries
- [Async purchase confirmation](docs/design/adr/013-async-purchase-confirmation.md) — event-driven, background-verified confirmation and decoupled cashback allocation
- [Persistent audit trail](docs/design/adr/015-persistent-audit-trail.md) — durable, queryable record of every critical operation for traceability and compliance
- [Background job architecture pattern](docs/design/adr/016-background-job-architecture-pattern.md) — Fan-Out Dispatcher + Per-Item Runner: how complex async background jobs decompose into independently testable, strategy-driven components with isolated retry lifecycles

The full index is at [`docs/design/adr-index.md`](docs/design/adr-index.md).

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions, development workflow, code quality requirements, and code organization guidelines.
