# PU-07: Reverse Purchase

IMPORTANT: This is a living document, specs are subject to change.

## User Story

_As an admin, I want to reverse/cancel purchases so that I can correct errors
and adjust cashback allocations._

---

## Constraints

### Authorization Constraints

- Only authenticated admin users can reverse purchases.
- Admin role must be verified before allowing reversal.

### Purchase Constraints

- Purchase must exist.
- Purchase must not already be in `reversed` status; only `pending` and
  `confirmed` purchases may be reversed.
- On reversal, the associated cashback transaction status changes to `reversed`.
- On reversal, the purchase `cashback_amount` is zeroed out.
- Wallet balance is adjusted based on the purchase's current status at the time
  of reversal:
  - `pending` → deduct from `pending_balance`.
  - `confirmed` → deduct from `available_balance`.
- The reversal is recorded in the audit trail.

---

## BDD Acceptance Criteria

**Scenario:** Admin successfully reverses a pending purchase

**Given** I am an authenticated admin user

**And** the purchase exists with status `pending`

**When** the admin submits a reversal request

**Then** purchase status changes to `reversed`, cashback transaction status
changes to `reversed`, `cashback_amount` is set to `0`, and `pending_balance`
is decremented by the original cashback amount

**Scenario:** Admin successfully reverses a confirmed purchase

**Given** I am an authenticated admin user

**And** the purchase exists with status `confirmed`

**When** the admin submits a reversal request

**Then** purchase status changes to `reversed`, cashback transaction status
changes to `reversed`, `cashback_amount` is set to `0`, and `available_balance`
is decremented by the original cashback amount

**Scenario:** Non-admin user attempts to reverse a purchase

**Given** I am an authenticated non-admin user

**When** the system checks authorization

**Then** access is denied with 403 Forbidden

**Scenario:** Admin attempts to reverse non-existent purchase

**Given** I am an authenticated admin user

**When** the system attempts to find the purchase

**Then** a 404 Not Found error is returned

**Scenario:** Admin attempts to reverse already reversed purchase

**Given** I am an authenticated admin user

**And** the purchase already has status `reversed`

**When** the system checks purchase status

**Then** a 400 Bad Request error is returned with code `PURCHASE_ALREADY_REVERSED`

---

## Use Cases

### Happy Path

Admin successfully reverses a purchase

1. Admin sends reversal request for existing purchase.
2. System verifies admin authentication and role.
3. System retrieves purchase record.
4. System verifies purchase status is not `reversed`.
5. System updates associated cashback transaction status to `reversed`.
6. System decrements the appropriate wallet balance bucket (pending or available)
   by the original cashback amount.
7. System updates purchase status to `reversed` and zeros `cashback_amount`.
8. System records an audit trail entry.
9. System returns updated purchase info.

### Sad Paths

#### Unauthorized - Non-Admin User

1. Non-admin user sends reversal request.
2. System verifies authentication.
3. System checks admin role.
4. System finds user does not have admin role.
5. System returns `HTTP 403 Forbidden`.

#### Purchase Not Found

1. Admin sends reversal request for non-existent purchase ID.
2. System verifies admin role.
3. System attempts to retrieve purchase.
4. System finds purchase does not exist.
5. System returns not found error.

#### Purchase Already Reversed

1. Admin sends reversal request for already reversed purchase.
2. System verifies admin role.
3. System retrieves purchase record.
4. System checks purchase status.
5. System finds purchase is already reversed.
6. System returns error indicating invalid operation.

#### Unauthenticated Request

1. Anonymous user sends reversal request.
2. System verifies authentication.
3. System finds no valid credentials.
4. System rejects the request as unauthorized.

## API Contract

See [Reverse purchase](../../design/api-contracts/purchases/reverse-purchase.md) for detailed API specifications.
