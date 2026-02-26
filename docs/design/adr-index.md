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
