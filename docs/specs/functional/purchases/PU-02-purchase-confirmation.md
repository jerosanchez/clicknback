
# PU-02: Purchase Confirmation (Async/Event-Driven)

IMPORTANT: This is a living document, specs are subject to change.

## Overview

Purchase confirmation is handled asynchronously via a background job and an internal event broker. After a user ingests a purchase, a periodic background job simulates bank reconciliation by attempting to verify the purchase (date, amount, merchant name). If verification succeeds, a `PurchaseConfirmed` event is published; if it fails after a configurable number of retries (settings), a `PurchaseRejected` event is published. A separate service subscribes to these events and updates purchase status, triggers cashback calculation, and updates wallet balances.

## User Story

_As a system, I want to automatically confirm or reject pending purchases after verifying them against simulated bank data, so that cashback is only released for legitimate transactions._

---

## Constraints

### System Constraints

- Only the background job (trusted system process) can trigger confirmation or rejection
- Purchase must exist with status `pending`
- Associated cashback transaction must exist (created after confirmation)
- Verification is retried up to N times before rejection

---

## BDD Acceptance Criteria

**Scenario:** System successfully confirms a pending purchase
**Given** a purchase exists with status `pending`
**And** the background job verifies the purchase against simulated bank data
**When** verification succeeds
**Then** a `PurchaseConfirmed` event is published, purchase status changes to `confirmed`, cashback is calculated and credited to the user's wallet

**Scenario:** System rejects a purchase after failed verification
**Given** a purchase exists with status `pending`
**And** the background job fails to verify the purchase after N retries
**When** retries are exhausted
**Then** a `PurchaseRejected` event is published, purchase status changes to `rejected`, no cashback is credited

**Scenario:** Manual confirmation endpoint is not available
**Given** an admin or user attempts to confirm a purchase via API
**When** the system receives the request
**Then** a `405 Method Not Allowed` or `403 Forbidden` is returned

---

## Use Cases

### Happy Path

1. User ingests a purchase (status: `pending`).
2. Background job periodically attempts to verify the purchase against simulated bank data.
3. If verification succeeds, job publishes `PurchaseConfirmed` event.
4. Event subscriber updates purchase status to `confirmed`, triggers cashback calculation, and credits wallet.

### Sad Paths

- If verification fails after N retries, job publishes `PurchaseRejected` event; subscriber updates purchase status to `rejected`.
- If purchase is already confirmed or rejected, no further action is taken.
- Manual confirmation attempts via API are rejected.

## API Contract

There is no longer a public API endpoint for purchase confirmation. Confirmation and rejection are handled internally by the background job and event subscriber.

### Internal Events

- `PurchaseConfirmed` (purchase_id, user_id, merchant_id, amount, verified_at)
- `PurchaseRejected` (purchase_id, user_id, merchant_id, amount, failed_at, reason)

### Background Job

- Runs periodically to verify pending purchases
- Retries up to N times before rejection

### Event Subscriber

- Listens for confirmation/rejection events
- Updates purchase status, triggers cashback calculation, updates wallet

See [Confirm purchase](../../design/api-contracts/purchases/confirm-purchase.md) for detailed API specifications.
