# PA-02: Payout Processing

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
**When** the authorization is verified
**Then** payout status changes to `completed` and paid balance is increased

**Scenario:** Admin successfully fails a payout
**Given** I am an authenticated admin user
**And** the payout exists with status `requested`
**When** the authorization is verified
**Then** payout status changes to `failed` and amount is refunded to available balance

**Scenario:** Non-admin user attempts to process payout
**Given** I am an authenticated non-admin user
**When** the system checks authorization
**Then** access is denied

**Scenario:** Admin attempts to process non-existent payout
**Given** I am an authenticated admin user
**When** the system attempts to find the payout
**Then** a not found error is returned

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
8. System returns updated payout info.

### Sad Paths

#### Mark as Processing

1. Admin sends payout status update to `processing`.
2. System verifies admin role.
3. System retrieves payout record.
4. System updates payout status to `processing`.
5. System returns updated payout.

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
5. System returns not found error.

#### Unauthenticated Request

1. Anonymous user sends payout status update request.
2. System verifies authentication.
3. System finds no valid credentials.
4. System rejects the request as unauthorized.

## API Contract

See [Complete/fail payout](../../design/api-contracts/payouts/process-payout.md) for detailed API specifications.
