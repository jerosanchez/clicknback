# W-02: Wallet Transactions Listing

IMPORTANT: This is a living document, specs are subject to change.

## User Story

_As an authenticated user, I want to list my wallet transactions so that I can audit and track all cashback credits and reversals._

---

## Domain Concepts

| Term | Description |
| --- | --- |
| **Wallet transaction** | A record of a cashback credit or reversal; includes amount, type, status, and related purchase ID. |
| **Transaction status** | Lifecycle state: `pending` (awaiting purchase confirmation), `available` (confirmed, spendable), or `reversed` (clawed back). |
| **User isolation** | Users can only view their own transaction history; the system enforces per-user scoping. |

---

## Constraints

### Authorization Constraints

- User must be authenticated.
- User can only view their own transactions; the system enforces per-user isolation.

### Filter Constraints

- No optional filters; all transactions for the user are returned by default.
- Transaction types currently include: `cashback_credit` and reversals. (Payout deductions are deferred to a future release.)

### Response Constraints

- Results are paginated; `offset` (default: 0) and `limit` (default: 10, max: 100) control the page window.
- An empty result set is valid and returns `{ "data": [], "pagination": { "offset": 0, "limit": 10, "total": 0 } }`.

---

## BDD Acceptance Criteria

**Scenario:** User lists all transactions
**Given** I am an authenticated user with wallet transactions
**When** I send a list request with no filters
**Then** all my transaction records are returned with their full details

**Scenario:** User receives empty transaction list
**Given** I am an authenticated user with no wallet transactions
**When** I send a list request
**Then** the response is `200 OK` with `{ "data": [], "pagination": { "offset": 0, "limit": 10, "total": 0 } }`

**Scenario:** Unauthenticated user attempts to list transactions
**Given** no JWT token is provided
**When** I send a list-transactions request
**Then** the response is `401 Unauthorized`

**Scenario:** User requests transactions with invalid pagination
**Given** I am an authenticated user
**And** I send a request with invalid parameters (e.g., `limit=0` or `offset=-1`)
**When** the API validates the input
**Then** the request is rejected with a `VALIDATION_ERROR`

---

## Use Cases

### Happy Path — List all transactions

1. User sends a `GET` request with optional pagination parameters.
2. System verifies user authentication.
3. System retrieves transactions belonging to the user.
4. System applies pagination and returns the page.
5. System returns `{ "data": [...], "pagination": { "offset": ..., "limit": ..., "total": N } }`.

### Sad Paths

#### Unauthenticated request

1. Requester lacks a valid authentication token.
2. System enforces authentication.
3. System returns `401 Unauthorized`.

#### Invalid pagination parameters

1. User sends a list request with invalid pagination values (e.g., `limit=0`, `limit > 100`, `offset < 0`).
2. System validates pagination parameters.
3. System rejects the request with `VALIDATION_ERROR` and details on the violation.

## API Contract

See [List wallet transactions](../../design/api-contracts/wallets/list-wallet-transactions.md) for detailed API specifications.
