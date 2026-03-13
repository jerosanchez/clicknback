# ADR Index

## Introduction

Architecture Decision Records (ADRs) are the foundational design documents that capture critical architectural and technical decisions made during ClicknBack's development. Each ADR documents a specific decision, its context, the alternatives considered, and the rationale behind the chosen approach.

### Purpose of ADRs

ADRs serve several essential purposes:

- **Preserve decision rationale**: Explain *why* technical choices were made, not just *what* they are, enabling future developers to understand the reasoning rather than questioning or reversing decisions.
- **Facilitate knowledge sharing**: Make architectural decisions transparent and accessible to the entire team, reducing knowledge silos.
- **Support future decisions**: Provide a foundation for subsequent architectural choices, ensuring consistency and preventing conflicting decisions.
- **Enable informed trade-offs**: Document alternatives and their tradeoffs, making it clear what was considered and why certain approaches were rejected.

---

## Architecture Decision Records

- [ADR 000: Technology Stack Selection](adr/000-technology-stack-selection.md)
- [ADR 001: Adopt Modular Monolith Approach](adr/001-adopt-modular-monolith-approach.md)
- [ADR 002: Not to Use Dedicated DTOs](adr/002-not-to-use-dedicated-dtos.md)
- [ADR 003: API Module as Composition Root](adr/003-api-module-as-composition-root.md)
- [ADR 004: Use Lambda for Stateless Dependencies](adr/004-use-lambda-for-stateless-dependencies.md)
- [ADR 005: Use Containerized PostgreSQL](adr/005-use-containerized-postgresql.md)
- [ADR 006: Store Limited Value Fields as String](adr/006-store-limited-value-fields-as-string.md)
- [ADR 007: Layered Testing Strategy](adr/007-layered-testing-strategy.md)
- [ADR 008: JWT Stateless Authentication](adr/008-jwt-stateless-authentication.md)
- [ADR 009: Use Python's Native Logging Over FastAPI/Uvicorn](adr/009-native-logging-over-fastapi.md)
- [ADR 010: Async-First Database Layer with asyncpg](adr/010-async-database-layer.md)
- [ADR 011: EUR-Only Currency Policy](adr/011-eur-only-currency-policy.md)
- [ADR 012: Restrict Purchase Ingestion to Self (Self-Ingestion Policy)](adr/012-self-ingestion-policy.md)
- [ADR 013: Asynchronous Purchase Confirmation via Internal Event Broker](adr/013-async-purchase-confirmation.md)
- [ADR 014: In-Process Message Broker and Task Scheduler for MVP](adr/014-in-process-broker-and-scheduler.md)
- [ADR 015: Persistent Audit Trail for Critical Operations](adr/015-persistent-audit-trail.md)
- [ADR 016: Background Job Architecture Pattern — Fan-Out Dispatcher with Per-Item Retry Runners](adr/016-background-job-architecture-pattern.md)
- [ADR 017: Fixed-Interval Retry Strategy for Background Jobs](adr/017-fixed-interval-retry-strategy.md)
- [ADR 018: Database-Backed Feature Flag System](adr/018-feature-flag-system.md)
