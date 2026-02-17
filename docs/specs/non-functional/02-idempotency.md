# NFR-02: Idempotency

## Overview

The system must guarantee that idempotent operations, particularly purchase ingestion, can be safely retried without causing duplicate side effects or data corruption, even when called multiple times with identical inputs.

## Motivation

Network failures, system outages, and automatic retry mechanisms mean operations may be retried multiple times. For financial operations like purchase ingestion, idempotency prevents duplicate charges, duplicate wallet credits, or inconsistent reward calculations.

## Definition

- Purchase ingestion operations must use idempotency keys to deduplicate requests.
- Idempotent operations should always return the same result regardless of the number of calls.
- The system must detect and reject duplicate requests within a reasonable retention window.

## Acceptance Criteria

- Ingesting the same purchase twice with the same transaction ID results in only one wallet update.
- Requests with an idempotency key return 409 Conflict or the original successful response if retried.
- Duplicate detection is tracked in the database and cleaned up after 24 hours.
- The idempotency key is returned in the API response for client reference.

## Technical Approach

- Database idempotency table tracks keys and results for 24 hours.
- Purchase API endpoints accept `Idempotency-Key` header (unique per purchase source).
- Before processing, check if idempotency key exists; if so, return cached result.
- Combine idempotency key with purchase source for uniqueness (e.g., `sha256(purchase_id + source)`).
- Implement at the service layer to ensure all code paths respect idempotency semantics.
