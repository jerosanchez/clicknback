# NFR-06: State Management & Validation

## Overview

The system must enforce valid state transitions for entities like wallets, transactions, and withdrawal requests, preventing invalid state changes and ensuring compliance with business logic rules.

## Motivation

Entities (wallet, transactions, withdrawal requests) have valid state lifecycles (e.g., withdrawal: pending → approved → completed → settled). Allowing arbitrary state transitions leads to logical inconsistencies, incorrect processing, and compliance violations.

## Definition

- Each entity has defined valid states and allowed transitions.
- State transitions are validated against a state machine before persisting.
- Invalid transitions are rejected with clear error messages.
- State change events are logged for auditing.

## Acceptance Criteria

- Attempting an invalid state transition (e.g., completed → pending) returns 400 Bad Request with reason.
- Database constraints or application logic prevent invalid states from being persisted.
- Unit tests cover all valid and invalid state transitions per entity.
- Audit log records all state changes with timestamp and actor.

## Technical Approach

- Define state machines for key entities using an enum or dedicated state model.
- Implement state validation in the service layer before repository calls.
- Use a state transition matrix or guard clauses to define allowed transitions.
- Database schema: state columns have CHECK constraints or are enforced via ORM validation.
- Use a library like `transitions` (Python) if complexity grows beyond a few entities.
- Emit domain events on state changes for downstream services.
