# Purchase Cancellation

IMPORTANT: This is a living document, specs are subject to change.

## User Story

_As an admin, I want to reverse/cancel purchases so that I can correct errors and adjust cashback allocations._

---

## Constraints

### Authorization Constraints

- Only authenticated admin users can reverse purchases
- Admin role must be verified before allowing reversal

### Purchase Constraints

- Purchase must exist
- Associated wallet balance must be adjusted appropriately

---

## BDD Acceptance Criteria

**Scenario:** Admin successfully reverses a purchase
**Given** I am an authenticated admin user
**And** the purchase exists with any status
**And** I send a `PATCH /api/v1/purchases/{id}/reverse` request
**When** the authorization is verified
**Then** the API responds with `HTTP 200 OK`, purchase status changes to `reversed`, cashback status changes to `reversed`, and wallet balance is adjusted

**Scenario:** Non-admin user attempts to reverse a purchase
**Given** I am an authenticated non-admin user
**And** I send a `PATCH /api/v1/purchases/{id}/reverse` request
**When** the system checks authorization
**Then** the API responds with `HTTP 403 Forbidden`

**Scenario:** Admin attempts to reverse non-existent purchase
**Given** I am an authenticated admin user
**And** I send a `PATCH /api/v1/purchases/{999}/reverse` request for a non-existent purchase
**When** the system attempts to find the purchase
**Then** the API responds with `HTTP 404 Not Found`

**Scenario:** Admin attempts to reverse already reversed purchase
**Given** I am an authenticated admin user
**And** the purchase already has status `reversed`
**And** I send a `PATCH /api/v1/purchases/{id}/reverse` request
**When** the system checks purchase status
**Then** the API responds with `HTTP 400 Bad Request` or `HTTP 409 Conflict`

---

## Use Cases

### Happy Path

Admin successfully reverses a purchase

1. Admin sends reversal request for existing purchase.
2. System verifies admin authentication and role.
3. System retrieves purchase record.
4. System verifies purchase is not already reversed.
5. System updates purchase status to `reversed`.
6. System updates associated cashback status to `reversed`.
7. System adjusts wallet balance to remove cashback.
8. System returns `HTTP 200 OK` with updated purchase info.

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
5. System returns `HTTP 404 Not Found`.

#### Purchase Already Reversed

1. Admin sends reversal request for already reversed purchase.
2. System verifies admin role.
3. System retrieves purchase record.
4. System checks purchase status.
5. System finds purchase is already reversed.
6. System returns `HTTP 400 Bad Request` or `HTTP 409 Conflict`.

#### Unauthenticated Request

1. Anonymous user sends reversal request.
2. System verifies authentication.
3. System finds no valid credentials.
4. System returns `HTTP 401 Unauthorized`.
