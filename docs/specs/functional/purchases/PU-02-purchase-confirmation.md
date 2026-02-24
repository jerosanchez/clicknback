# PU-02: Purchase Confirmation

IMPORTANT: This is a living document, specs are subject to change.

## User Story

_As an admin, I want to confirm pending purchases so that I can release cashback to users' available balance._

---

## Constraints

### Authorization Constraints

- Only authenticated admin users can confirm purchases
- Admin role must be verified before allowing confirmation

### Purchase Constraints

- Purchase must exist with status `pending`
- Associated cashback transaction must exist

---

## BDD Acceptance Criteria

**Scenario:** Admin successfully confirms a pending purchase
**Given** I am an authenticated admin user
**And** the purchase exists with status `pending`
**When** the authorization is verified
**Then** purchase status changes to `confirmed`, cashback status changes to `available`, and wallet balance is updated

**Scenario:** Non-admin user attempts to confirm a purchase
**Given** I am an authenticated non-admin user
**When** the system checks authorization
**Then** access is denied

**Scenario:** Admin attempts to confirm non-existent purchase
**Given** I am an authenticated admin user
**When** the system attempts to find the purchase
**Then** a not found error is returned

**Scenario:** Admin attempts to confirm already confirmed purchase
**Given** I am an authenticated admin user
**And** the purchase already has status `confirmed`
**When** the system checks purchase status
**Then** an error is returned indicating invalid operation

---

## Use Cases

### Happy Path

Admin successfully confirms a pending purchase

1. Admin sends confirmation request for pending purchase.
2. System verifies admin authentication and role.
3. System retrieves purchase record.
4. System verifies purchase status is `pending`.
5. System transitions purchase to `confirmed`.
6. System transitions associated cashback to `available`.
7. System moves wallet balance from pending to available.
8. System returns updated purchase info.

### Sad Paths

#### Unauthorized - Non-Admin User

1. Non-admin user sends confirmation request.
2. System verifies authentication.
3. System checks admin role.
4. System finds user does not have admin role.
5. System returns `HTTP 403 Forbidden`.

#### Purchase Not Found

1. Admin sends confirmation request for non-existent purchase ID.
2. System verifies admin role.
3. System attempts to retrieve purchase.
4. System finds purchase does not exist.
5. System returns not found error.

#### Purchase Already Confirmed

1. Admin sends confirmation request for already confirmed purchase.
2. System verifies admin role.
3. System retrieves purchase record.
4. System checks purchase status.
5. System finds purchase is already confirmed.
6. System returns error indicating invalid operation.

#### Unauthenticated Request

1. Anonymous user sends confirmation request.
2. System verifies authentication.
3. System finds no valid credentials.
4. System rejects the request as unauthorized.

## API Contract

See [Confirm purchase](../../design/api-contracts/purchases/confirm-purchase.md) for detailed API specifications.
