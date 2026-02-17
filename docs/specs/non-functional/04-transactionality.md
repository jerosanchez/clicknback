# NFR-04: Transactionality

## Overview

The system must ensure that all wallet updates and related state changes are atomic—either all steps succeed together or all are rolled back—to prevent inconsistent financial states and lost updates.

## Motivation

Wallet operations often involve multiple steps: debit wallet, credit wallet, update transaction status, audit log. If any step fails mid-way, the system enters an inconsistent state where money appears or disappears. ACID transactions guarantee consistency.

## Definition

- Wallet credit/debit operations are wrapped in database transactions.
- All related updates (wallet, transaction records, audit logs) succeed or fail as a single unit.
- Transactions follow the ACID properties: Atomicity, Consistency, Isolation, Durability.
- If any operation fails, the entire transaction is rolled back to the pre-transaction state.

## Acceptance Criteria

- Test: Simulate a failure mid-operation and verify wallet state is unchanged.
- Test: Concurrent transactions on the same wallet don't leave it in an inconsistent state.
- Database transaction logs show atomic operations are committed or rolled back.
- Long-running transactions have defined timeouts to prevent resource exhaustion.

## Technical Approach

- Use database transactions at the repository layer for wallet operations.
- SQLAlchemy `Session` with `@transactional` decorator or context managers.
- Isolation level: READ_COMMITTED (or higher if needed for specific scenarios).
- Implement retry logic with exponential backoff for transaction conflicts.
- Unit tests mock transaction boundaries; integration tests use actual database transactions.
