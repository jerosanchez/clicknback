# NFR-01: Data Integrity

## Overview

The system must enforce data consistency and integrity constraints to prevent invalid or duplicate data at the database level, ensuring the reliability of critical entities like user accounts and email addresses.

## Motivation

In a financial application, data integrity is paramount. Allowing duplicate emails or invalid states can lead to incorrect transaction routing, account mismanagement, and compliance violations. Database-level constraints provide a hard safety barrier.

## Definition

- All unique constraints (email, identifiers) must be enforced at the database schema level, not solely in application code.
- Database triggers or constraints ensure data consistency cannot be bypassed.
- Invalid state transitions are prevented at the database layer.

## Acceptance Criteria

- Attempting to create a user with a duplicate email returns a database constraint violation (409 Conflict).
- Database schema includes explicit UNIQUE constraints on email columns.
- All critical state fields have NOT NULL constraints where applicable.
- Integration tests verify that direct database inserts also respect these constraints.

## Technical Approach

- SQL UNIQUE constraints on the `users.email` column with a partial index for active records.
- Foreign key constraints to maintain referential integrity.
- Database migrations version and document all schema constraints.
- Constraint validation testing at the repository layer.
