# PU-08: Admin Purchase Confirmation

IMPORTANT: This is a living document, specs are subject to change.

## Overview

Admins can manually confirm pending purchases without waiting for background job verification. When an admin confirms a purchase, the system transitions the purchase status to `confirmed`, performs cashback calculation, and credits the user's wallet. A domain event is published so the audit trail records that an admin (not a background job) performed the confirmation.

## User Story

_As an admin, I want to manually confirm pending purchases so that I can override the automatic verification process and immediately credit cashback when needed._

---

## Constraints

### Authorization Constraints

- Only authenticated admin users can confirm purchases.
- Admin role must be verified before allowing confirmation.

### Purchase Constraints

- Purchase must exist.
- Purchase must have status `pending`; only pending purchases may be confirmed.
- Associated cashback transaction must exist (created during purchase ingestion).
- On confirmation, the purchase `cashback_amount` is moved from the user's wallet `pending_balance` to `available_balance`.
- The confirmation is recorded in the audit trail with the admin's user ID.
- Confirmation and wallet update are committed atomically in a single DB transaction.

### Audit Constraints

- The audit record must capture that the action was performed by an admin (not a background job).
- The audit record must include the admin's user ID, action timestamp, and the purchase ID.

---

## BDD Acceptance Criteria

**Scenario:** Admin successfully confirms a pending purchase
**Given** I am an authenticated admin user
**And** the purchase exists with status `pending`
**When** the admin submits a confirmation request
**Then** purchase status changes to `confirmed`, the purchase's `cashback_amount` is moved from `pending_balance` to `available_balance`, a domain event is published, and the confirmation is recorded in the audit trail with the admin's user ID

**Scenario:** Non-admin user attempts to confirm a purchase
**Given** I am an authenticated non-admin user
**When** the system checks authorization
**Then** access is denied with 403 Forbidden

**Scenario:** Admin attempts to confirm non-existent purchase
**Given** I am an authenticated admin user
**When** the system attempts to find the purchase
**Then** a 404 Not Found error is returned

**Scenario:** Admin attempts to confirm non-pending purchase
**Given** I am an authenticated admin user
**And** the purchase has status `confirmed`, `rejected`, or `reversed`
**When** the system checks purchase status
**Then** a 400 Bad Request error is returned with code `PURCHASE_NOT_PENDING`

**Scenario:** User attempts to confirm a purchase without authentication
**Given** I am an unauthenticated user
**When** the system checks the authorization header
**Then** a 401 Unauthorized error is returned

---

## Use Cases

### Happy Path

Admin successfully confirms a purchase:

1. Admin sends confirmation request for existing pending purchase.
2. System verifies admin authentication and role.
3. System retrieves purchase record with associated cashback transaction.
4. System verifies purchase status is `pending`.
5. System confirms the purchase and updates wallet balances atomically.
6. System publishes a domain event with admin context.
7. Audit trail records the action with admin's user ID.

### Sad Paths

- If purchase does not exist, a 404 Not Found error is returned.
- If purchase is not pending, a 400 Bad Request error is returned.
- If user is not an admin, a 403 Forbidden error is returned.
- If user is not authenticated, a 401 Unauthorized error is returned.

## API Contract

See [Admin confirm purchase](../../design/api-contracts/purchases/admin-confirm-purchase.md) for detailed API specifications.
