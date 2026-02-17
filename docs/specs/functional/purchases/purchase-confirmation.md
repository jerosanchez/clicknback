# Purchase Confirmation

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
**And** I send a `PATCH /api/v1/purchases/{id}/confirm` request
**When** the authorization is verified
**Then** the API responds with `HTTP 200 OK`, purchase status changes to `confirmed`, cashback status changes to `available`, and wallet balance is updated

**Scenario:** Non-admin user attempts to confirm a purchase
**Given** I am an authenticated non-admin user
**And** I send a `PATCH /api/v1/purchases/{id}/confirm` request
**When** the system checks authorization
**Then** the API responds with `HTTP 403 Forbidden`

**Scenario:** Admin attempts to confirm non-existent purchase
**Given** I am an authenticated admin user
**And** I send a `PATCH /api/v1/purchases/{999}/confirm` request for a non-existent purchase
**When** the system attempts to find the purchase
**Then** the API responds with `HTTP 404 Not Found`

**Scenario:** Admin attempts to confirm already confirmed purchase
**Given** I am an authenticated admin user
**And** the purchase already has status `confirmed`
**And** I send a `PATCH /api/v1/purchases/{id}/confirm` request
**When** the system checks purchase status
**Then** the API responds with `HTTP 400 Bad Request` or `HTTP 409 Conflict`

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
8. System returns `HTTP 200 OK` with updated purchase info.

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
5. System returns `HTTP 404 Not Found`.

#### Purchase Already Confirmed

1. Admin sends confirmation request for already confirmed purchase.
2. System verifies admin role.
3. System retrieves purchase record.
4. System checks purchase status.
5. System finds purchase is already confirmed.
6. System returns `HTTP 400 Bad Request` or `HTTP 409 Conflict`.

#### Unauthenticated Request

1. Anonymous user sends confirmation request.
2. System verifies authentication.
3. System finds no valid credentials.
4. System returns `HTTP 401 Unauthorized`.
