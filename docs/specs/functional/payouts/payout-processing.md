# Payout Processing

IMPORTANT: This is a living document, specs are subject to change.

## User Story

_As an admin, I want to process pending payout requests so that I can complete or fail payouts and keep wallet balances consistent._

---

## Constraints

### Authorization Constraints

- Only authenticated admin users can process payouts
- Admin role must be verified before allowing processing

### Payout Constraints

- Payout must exist with status `requested`
- Admin can update status to `processing`, `completed`, or `failed`
- If completed: system increases `paid_balance`
- If failed: system refunds amount to `available_balance`
- Wallet balances must remain consistent

---

## BDD Acceptance Criteria

**Scenario:** Admin successfully completes a payout
**Given** I am an authenticated admin user
**And** the payout exists with status `requested`
**And** I send a `PATCH /api/v1/payouts/{id}` request with status `completed`
**When** the authorization is verified
**Then** the API responds with `HTTP 200 OK`, payout status changes to `completed`, and paid balance is increased

**Scenario:** Admin successfully fails a payout
**Given** I am an authenticated admin user
**And** the payout exists with status `requested`
**And** I send a `PATCH /api/v1/payouts/{id}` request with status `failed`
**When** the authorization is verified
**Then** the API responds with `HTTP 200 OK`, payout status changes to `failed`, and amount is refunded to available balance

**Scenario:** Non-admin user attempts to process payout
**Given** I am an authenticated non-admin user
**And** I send a `PATCH /api/v1/payouts/{id}` request
**When** the system checks authorization
**Then** the API responds with `HTTP 403 Forbidden`

**Scenario:** Admin attempts to process non-existent payout
**Given** I am an authenticated admin user
**And** I send a `PATCH /api/v1/payouts/{999}` request for a non-existent payout
**When** the system attempts to find the payout
**Then** the API responds with `HTTP 404 Not Found`

---

## Use Cases

### Happy Path

Admin successfully completes payout processing

1. Admin sends payout status update request.
2. System verifies admin authentication and role.
3. System retrieves payout record.
4. System verifies payout status is `requested`.
5. If completing: system increases `paid_balance` and updates status to `completed`.
6. If failing: system refunds to `available_balance` and updates status to `failed`.
7. System ensures wallet balances remain consistent.
8. System returns `HTTP 200 OK` with updated payout info.

### Sad Paths

#### Mark as Processing

1. Admin sends payout status update to `processing`.
2. System verifies admin role.
3. System retrieves payout record.
4. System updates payout status to `processing`.
5. System returns `HTTP 200 OK` with updated payout.

#### Unauthorized - Non-Admin User

1. Non-admin user sends payout status update request.
2. System verifies authentication.
3. System checks admin role.
4. System finds user does not have admin role.
5. System returns `HTTP 403 Forbidden`.

#### Payout Not Found

1. Admin sends status update for non-existent payout ID.
2. System verifies admin role.
3. System attempts to retrieve payout.
4. System finds payout does not exist.
5. System returns `HTTP 404 Not Found`.

#### Unauthenticated Request

1. Anonymous user sends payout status update request.
2. System verifies authentication.
3. System finds no valid credentials.
4. System returns `HTTP 401 Unauthorized`.
