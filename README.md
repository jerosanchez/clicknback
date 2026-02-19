<!-- markdownlint-disable MD041 -->
![CI](https://github.com/jerosanchez/clicknback/actions/workflows/ci.yml/badge.svg)
![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)
![status: early development](https://img.shields.io/badge/status-early%20development-orange)
<!-- markdownlint-enable MD041 -->

# ClicknBack – Backend Engineering Demo

**A production-grade cashback backend system showcasing senior-level engineering practices.**

Built with **Python** | **FastAPI** | **PostgreSQL** and related technologies.

This repository demonstrates designing and building a real-world system with proper architecture, comprehensive documentation, rigorous testing, and thoughtful API design. It models a complete cashback product: users, merchants, offers, purchases, wallet management, and payouts.

---

## Quick Start for Reviewers

```bash
make dev
```

Server runs at `http://localhost:8000`

## Project Structure

```text
app/                    # Application code
├── core/               # Shared infra (config, database, etc.)
├── users/              # User domain module (blueprint)
│   ├── api.py          # API endpoints
│   ├── models.py       # Database models
│   ├── schemas.py      # Request/response schemas
│   ├── services.py     # Business logic
│   ├── repositories.py # Data access layer
│   └── exceptions.py   # Domain exceptions
├── ...
└── main.py             # Application factory

tests/                  # Test suite (unit, integration, E2E)
├── conftest.py         # Pytest configuration & fixtures
├── users/
└── ...

docs/                   # Comprehensive documentation
├── design/             # Architecture, ADRs, API contracts, etc.
├── specs/              # Product overview, requirements, etc.
└── agents/             # Coding guidelines (for humans & AIs)

seeds/                  # SQL scrips to populate local DB

alembic/                # Database migrations
```

---

## Feature List

| Feature | Domain | Status |
| --------- | -------- | -------- |
| **🔑 Authentication** | | |
| User Authentication (Login) | Auth | 🟡 ongoing |
| **🏪 Merchant Management** | | |
| Merchant Creation | Merchants | ⚪ defined |
| Merchants Listing | Merchants | ⚪ defined |
| Merchant Activation | Merchants | ⚪ defined |
| **🎁 Offer Management** | | |
| Offer Creation | Offers | ⚪ defined |
| Offers Listing | Offers | ⚪ defined |
| Active Offers Listing | Offers | ⚪ defined |
| Offer Activation | Offers | ⚪ defined |
| Offer Details View | Offers | ⚪ defined |
| **💵 Payouts** | | |
| Payout Request (Withdrawal) | Payouts | ⚪ defined |
| Payout Processing | Payouts | ⚪ defined |
| Payouts Listing | Payouts | ⚪ defined |
| User Payouts Listing | Payouts | ⚪ defined |
| **💸 Purchase & Cashback Flow** | | |
| Purchase Ingestion (Webhook) | Purchases | ⚪ defined |
| Purchase Confirmation | Purchases | ⚪ defined |
| Purchase Details View | Purchases | ⚪ defined |
| Purchases Listing | Purchases | ⚪ defined |
| User Purchases Listing | Purchases | ⚪ defined |
| Cashback Calculation Engine | Purchases | ⚪ defined |
| Purchase Reversal | Purchases | ⚪ defined |
| **👤 User Management** | | |
| User Registration | Users | 🟢 ready |
| **👛 Wallet Management** | | |
| Wallet Summary View | Wallets | ⚪ defined |
| Wallet Transactions Listing | Wallets | ⚪ defined |

---

## System Documentation

> ⚠️ **Living Documentation Notice**
>
> This system is in **early development**. The documentation is a living entity and can get out of sync with the implementation. Some inconsistencies between docs and code are expected as the project evolves.
>
> **In case of conflicts:**
>
> - For feature maturity status, trust the [Feature List](#feature-list) table in this README
> - For implemented behavior, trust the **code and tests** as the source of truth
> - Documentation serves as design intent and architectural guidance
>
> Contributions should keep docs and code aligned where possible.

### Specifications & Requirements

Start here to understand what the system does and what's required:

- [Product Overview](docs/specs/product-overview.md) — High-level overview of the ClicknBack cashback system
- [System Requirements](docs/specs/system-requirements.md) — Functional and non-functional requirements
  - [Functional Specifications](docs/specs/functional/) — Detailed workflows for each domain (users, merchants, offers, purchases, wallets, payouts)
  - [Non-Functional Requirements](docs/specs/non-functional/) — Data integrity, idempotency, financial precision, concurrency, performance, etc.
- [Domain Glossary](docs/specs/domain-glossary.md) — Key domain concepts and terminology

### Design & Architecture

Understand how the system is built and the decisions made:

- [Architecture Overview](docs/design/architecture-overview.md) — High-level system architecture
- [Architecture Decision Records (ADRs)](docs/design/adr-index.md) — Key design decisions and rationale
- [Data Model](docs/design/data-model.md) — Entity relationships and database schema
- [API Contracts](docs/design/api-contracts-index.md) — Detailed API specifications for all endpoints
- [Security Strategy](docs/design/security-strategy.md) — Authentication, authorization, and data consistency and protection
- [Error Handling Strategy](docs/design/error-handling-strategy.md) — Error classification and handling patterns
- [Testing Strategy](docs/design/testing-strategy.md) — Testing approach and coverage requirements
- [Deployment Plan](docs/design/deployment-plan.md) — Deployment procedures and environment configuration
- [Operation Plan](docs/design/operation-plan.md) — Operational guidelines and monitoring

## Contributing

For guidelines on setting up your environment, development workflow, and code quality requirements, see the [CONTRIBUTING.md](CONTRIBUTING.md) file.

Coding and text writing guidelines for both human developers and AI agents are available in the [docs/agents/](docs/agents/) directory.
