# Payout Request

IMPORTANT: This is a living document, specs are subject to change.

## User Story

_As an authenticated user, I want to request a payout of my available cashback so that I can withdraw my earnings._

---

## Constraints

### User Constraints

- User must be authenticated
- User can only request payouts for their own account

### Payout Constraints

- Available balance must be sufficient for requested amount
- Withdrawal policy must be satisfied (e.g., minimum amount, frequency limits)
- Wallet row must be locked during balance deduction for concurrency safety

---

## BDD Acceptance Criteria

**Scenario:** User successfully requests payout
**Given** I am an authenticated user
**And** my available balance is at least the requested amount
**And** I meet withdrawal policy requirements
**And** I send a `POST /api/v1/payouts/request` request with the payout amount
**When** the system validates policy and locks the wallet
**Then** the API responds with `HTTP 201 Created`, the available balance is deducted, and payout status is `requested`

**Scenario:** Unauthenticated user attempts to request payout
**Given** I am not authenticated
**And** I send a `POST /api/v1/payouts/request` request
**When** the system checks authentication
**Then** the API responds with `HTTP 401 Unauthorized`

**Scenario:** User requests payout exceeding available balance
**Given** I am an authenticated user
**And** my available balance is less than the requested amount
**And** I send a `POST /api/v1/payouts/request` request
**When** the system validates the balance
**Then** the API responds with `HTTP 400 Bad Request` indicating insufficient balance

**Scenario:** User requests payout below minimum withdrawal amount
**Given** I am an authenticated user
**And** the requested amount is below the minimum withdrawal policy threshold
**And** I send a `POST /api/v1/payouts/request` request
**When** the system validates the withdrawal policy
**Then** the API responds with `HTTP 400 Bad Request` with policy violation error

---

## Use Cases

### Happy Path

Authenticated user successfully requests payout

1. User submits payout request with amount.
2. System verifies user authentication.
3. System validates requested amount.
4. System validates withdrawal policy.
5. System locks wallet row for atomicity.
6. System deducts available balance.
7. System creates payout with status `requested`.
8. System returns `HTTP 201 Created` with payout info.

### Sad Paths

#### Unauthenticated Request

1. Anonymous user submits payout request.
2. System verifies authentication.
3. System finds no valid credentials.
4. System returns `HTTP 401 Unauthorized`.

#### Insufficient Balance

1. User submits payout request exceeding available balance.
2. System verifies user authentication.
3. System validates requested amount.
4. System checks available balance.
5. System finds insufficient balance.
6. System returns `HTTP 400 Bad Request` with error message.

#### Withdrawal Policy Violation - Minimum Amount

1. User requests payout below minimum withdrawal amount.
2. System verifies user authentication.
3. System validates requested amount.
4. System checks withdrawal policy.
5. System finds amount below minimum threshold.
6. System returns `HTTP 400 Bad Request` with policy error.

#### Invalid Amount

1. User submits payout request with zero or negative amount.
2. System verifies user authentication.
3. System validates requested amount.
4. System detects invalid amount.
5. System returns `HTTP 400 Bad Request` with validation error.
