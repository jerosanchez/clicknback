<!-- markdownlint-disable MD041 -->

![ClickNBack banner](/docs/clicknback-banner.png)

![CI](https://github.com/jerosanchez/clicknback/actions/workflows/ci.yml/badge.svg)
![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?logo=fastapi)
[![security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)
![coverage: 89%](https://img.shields.io/badge/coverage-89%25-brightgreen)
![status: actively maintained](https://img.shields.io/badge/status-actively%20maintained-green)

<!-- markdownlint-enable MD041 -->

**A production-grade cashback platform backend.**

Live at [clicknback.com](https://clicknback.com/docs) — no setup required.

This is a reference implementation — there are no paying customers, and no shortcuts taken because of it. It was built exactly the way it would need to be built for a real company: financial precision, idempotency guarantees, row-level locking, documented tradeoffs, and a CI/CD pipeline enforcing quality on every commit. Zero compromises.

Built by a software engineer who previously shipped to millions of users — as a mobile and a backend engineer, at scale-up startups. Every architectural decision is documented, justified, and open for technical review.

---

## What This Project Is

ClickNBack models how a real cashback application works: users earn rewards on purchases at partner merchants. The platform ingests purchase events, verifies them asynchronously via a background job (simulating bank reconciliation), publishes confirmation/rejection and other events to an internal message broker, calculates cashback, manages user wallets (pending, available, and paid balances), and processes withdrawals.

A complete [glossary](/docs/specs/domain-glossary.md) and [product spec documents](/docs/specs/) are available to better understand the business domain.

The system is continuously deployed to a VPS with a full CI/CD pipeline — lint, tests (85% coverage hard gate), and security scanning run on every commit. See [Try the Live API](#try-the-live-api) section to interact with it directly.

Product specs are still evolving (see the [feature roadmap](#feature-roadmap) to see an up-to-date feature status).

---

## Technical and Domain Features

ClickNBack demonstrates a wide range of technical and domain features designed for real-world financial systems:

- **Layered, modular architecture** with strict separation between HTTP, business logic, and data access. Each domain (users, merchants, offers, purchases, wallets) is a self-contained module, making the codebase easy to navigate and ready for future extraction to services ([ADR-001](docs/design/adr/001-adopt-modular-monolith-approach.md)).
- **Financial correctness and precision**: all monetary values use `Decimal` (never `float`), and wallet updates use row-level locking to prevent race conditions. Idempotency is enforced on purchases by external ID, ensuring no double-crediting.
- **Asynchronous, event-driven workflows**: purchase confirmation is handled by a background job that simulates bank reconciliation, decoupled from the ingestion flow ([ADR-013](docs/design/adr/013-async-purchase-confirmation.md)).
- **Reliable background jobs**: jobs follow a Fan-Out Dispatcher + Per-Item Runner pattern, with independent retry lifecycles and in-flight locking ([ADR-016](docs/design/adr/016-background-job-architecture-pattern.md)).
- **Event-driven audit trail**: every critical operation (purchase confirmation, cashback crediting, withdrawal, admin actions) is recorded in an append-only audit log via a decoupled, event-driven subsystem that publishes audit events through the message broker ([ADR-015](docs/design/adr/015-persistent-audit-trail.md), [ADR-023](docs/design/adr/023-event-driven-audit-logging.md)).
- **Consistent, secure authentication**: JWT-based stateless authentication supports web, mobile, and third-party integrations ([ADR-008](docs/design/adr/008-jwt-stateless-authentication.md)).
- **Feature flag system**: features can be enabled/disabled at runtime, globally or per-merchant/user ([ADR-018](docs/design/adr/018-feature-flag-system.md)).
- **Test discipline**: a comprehensive three-layer testing pyramid — unit tests (all dependencies mocked), integration tests (real PostgreSQL database, no mocks), and E2E tests (full Docker Compose stack) — with full coverage reporting, strict Arrange-Act-Assert structure, and one canonical example per layer ([ADR-007](docs/design/adr/007-layered-testing-strategy.md)).
- **Developer experience**: containerized PostgreSQL for all environments ([ADR-005](docs/design/adr/005-use-containerized-postgresql.md)), native Python logging ([ADR-009](docs/design/adr/009-native-logging-over-fastapi.md)), and a CI/CD pipeline enforcing lint, test, coverage, and security gates.
- **API design**: clear, industry-standard endpoints (e.g., `/users/me` for self-resources ([ADR-020](docs/design/adr/020-use-users-me-prefix-for-self-resource-endpoints.md))), batch loading to avoid N+1 queries ([ADR-019](docs/design/adr/019-batch-loading-strategy.md)), and consistent error handling with normalized JSON responses.
- **Business rule isolation**: policies are pure functions, enforced at the service layer, making business logic easy to test and evolve.
- **Internal message broker and scheduler**: async pub/sub and periodic jobs are handled in-process for simplicity and testability ([ADR-014](docs/design/adr/014-in-process-broker-and-scheduler.md)).
- **Domain-driven constraints**: EUR-only currency policy ([ADR-011](docs/design/adr/011-eur-only-currency-policy.md)), self-ingestion policy for purchases ([ADR-012](docs/design/adr/012-self-ingestion-policy.md)), and storing limited-value fields as strings for flexibility ([ADR-006](docs/design/adr/006-store-limited-value-fields-as-string.md)).
- **Atomic multi-repository operations**: the Unit of Work pattern ensures atomicity and testability when coordinating changes across modules ([ADR-021](docs/design/adr/021-unit-of-work-pattern.md)).
- **Collaborator verification in tests**: service tests verify correct delegation to dependencies ([ADR-022](docs/design/adr/022-collaborator-integration-verification-in-unit-tests.md)).

Other highlights include dependency injection via FastAPI, repository pattern for data access, and a focus on extensibility and maintainability throughout the codebase. Not every feature is tied to a specific ADR, but all are designed for correctness, clarity, and real-world readiness.

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
| Purchase Reversal | Purchases | 🟢 done |
| **Wallet Management** | | |
| Wallet Summary | Wallets | 🟢 done |
| Wallet Transactions Listing | Wallets | 🟢 done |
| **Payouts** | | |
| Payout Request (Withdrawal) | Payouts | ⚪ backlog |
| Payout Processing | Payouts | ⚪ backlog |
| Payouts Listing | Payouts | ⚪ backlog |
| **Feature Flags** | | |
| Set Feature Flag | Feature Flags | 🟡 ongoing |
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

The full index is at [`docs/design/adr-index.md`](docs/design/adr-index.md).

---

## The Story

ClickNBack did not emerge from a tutorial. It was built during a deliberate sabbatical — the chance to take the time to build something properly, with the right constraints, and document every decision along the way. The full journey is on the blog:

- **Why the sabbatical**: [A Sabbatical With Intent](https://jerosanchez.com/posts/20251203-a-sabbatical-with-intent/) — context, intent, and what "building with intent" looks like in practice
- **Why this domain**: [The Pivot: Why I Dropped a Marketplace for a Cashback System](https://jerosanchez.com/posts/20260321-the-pivot-why-i-dropped-a-marketplace/) — why financial systems were the right backdrop, not a tutorial topic
- **The technical tour**: [Before You Ask: What You'll Find If You Read ClickNBack](https://jerosanchez.com/posts/20260323-before-you-ask/) — guided walkthrough of the ADRs, the architecture, the tests, and the honest tradeoffs

_If you are a recruiter or hiring manager evaluating this project, the technical tour post is the most efficient starting point._

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions, development workflow, code quality requirements, and code organization guidelines.
