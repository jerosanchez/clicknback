<!-- markdownlint-disable MD041 -->
![CI](https://github.com/jerosanchez/clicknback/actions/workflows/ci.yml/badge.svg)
![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)
![status: early development](https://img.shields.io/badge/status-early%20development-orange)
<!-- markdownlint-enable MD041 -->

# README

## Overview

ClicknBack is a minimal, production-grade cashback backend system designed to showcase senior backend engineering skills. It is built with FastAPI (and related technologies) and PostgreSQL. It models a real-world cashback product with users, merchants, offers, purchases, wallet management, and payouts.

The system is designed for clarity, extensibility, and to demonstrate best practices in backend development.

**Key Features:**

- User registration, authentication (JWT)
- Merchant and offer management (admin)
- Purchase ingestion (idempotent, webhook-style)
- Cashback calculation and enforcement of monthly caps
- Wallet with pending, available, and paid balances
- Payout requests and processing
- Concurrency-safe wallet operations
- Full auditability and traceability

## Design & System Documentation

Key architectural and design decisions are documented as Architecture Decision Records (ADRs) in the [docs/adr/](docs/adr/) directory. Please review relevant ADRs before proposing or implementing significant changes.

System documentation—feature list, functional and non-functional requirements, data model, API design—can be found in the [docs/specs/](docs/specs/) directory.

## Contributing

For guidelines on setting up your environment, development workflow, and code quality requirements, see the [CONTRIBUTING.md](CONTRIBUTING.md) file.

Coding and text writing guidelines for both human developers and AI agents are available in the [docs/agents/](docs/agents/) directory.
