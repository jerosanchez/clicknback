# Wallet Summary View

IMPORTANT: This is a living document, specs are subject to change.

## User Story

_As an authenticated user, I want to see my wallet balances so that I can understand how much cashback is pending, available, and already paid out._

---

## Constraints

### User Constraints

- User must be authenticated
- User can only view their own wallet

### Wallet Balances

- Pending balance: cashback awaiting admin confirmation
- Available balance: cashback ready for withdrawal
- Paid balance: cashback that has been withdrawn

---

## BDD Acceptance Criteria

**Scenario:** User successfully views wallet summary
**Given** I am an authenticated user
**And** I send a `GET /api/v1/wallet/summary` request
**When** the authorization is verified
**Then** the API responds with `HTTP 200 OK` and returns my pending balance, available balance, and paid balance

**Scenario:** Unauthenticated user attempts to view wallet
**Given** I am not authenticated
**And** I send a `GET /api/v1/wallet/summary` request
**When** the system checks authentication
**Then** the API responds with `HTTP 401 Unauthorized`

**Scenario:** New user with no balance activity
**Given** I am an authenticated user with no previous cashback activity
**And** I send a `GET /api/v1/wallet/summary` request
**When** the system retrieves wallet information
**Then** the API responds with `HTTP 200 OK` with all balances set to zero

---

## Use Cases

### Happy Path

Authenticated user successfully views wallet summary

1. User requests wallet summary.
2. System verifies user authentication.
3. System retrieves wallet record for user.
4. System returns pending, available, and paid balances.
5. System returns `HTTP 200 OK` with accurate financial overview.

### Sad Paths

#### Unauthenticated Request

1. Anonymous user requests wallet summary.
2. System verifies authentication.
3. System finds no valid credentials.
4. System returns `HTTP 401 Unauthorized`.

#### New User with Zero Balance

1. User requests wallet summary.
2. System verifies user authentication.
3. System retrieves wallet record.
4. System finds user has no balance activity.
5. System returns `HTTP 200 OK` with all balances as zero.

## API Contract

See [Get wallet summary](../../design/api-contracts/wallets/get-wallet-summary.md) for detailed API specifications.
