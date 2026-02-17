# NFR-05: Concurrency Safety

## Overview

The system must safely handle concurrent operations on shared resources (e.g., multiple withdrawal requests on the same wallet) without race conditions, lost updates, or oversending from the wallet balance.

## Motivation

In production, multiple users or services may attempt simultaneous operations on the same wallet. Without proper concurrency control, the wallet can be withdrawn beyond its actual balance or updates can be lost. This is especially critical for financial systems.

## Definition

- Concurrent operations on shared resources (wallets, balances) must not produce race conditions.
- Pessimistic locking (row locks) or optimistic locking (version numbers) prevents lost updates.
- No withdrawal request succeeds if it would negative balance or exceed withdrawable funds.

## Acceptance Criteria

- Load test: 100+ concurrent withdrawal requests on the same wallet; no oversending occurs.
- Test: Verify that balance cannot go negative under concurrent operations.
- Test: Version numbers or timestamps prevent stale write conflicts.
- Monitoring shows lock contention; no unacceptable deadlocks observed in stress tests.

## Technical Approach

- Use row-level locks (SELECT FOR UPDATE) during withdrawal operations.
- Database isolation level: READ_COMMITTED or higher.
- Pessimistic locking pattern: `session.query(Wallet).filter(...).with_for_update().first()`.
- Add `version` column to `wallets` table for optimistic locking as backup.
- Integration tests use thread pools to simulate concurrent requests.
- Performance tests ensure lock contention doesn't block legitimate concurrent operations.
