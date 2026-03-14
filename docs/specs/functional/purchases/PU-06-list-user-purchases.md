# PU-06: List User Purchases

IMPORTANT: This is a living document, specs are subject to change.

## User Story

_As an authenticated user, I want to view my purchase history so that I can audit my transactions and see associated cashback._

---

## Constraints

### Authorization Constraints

- User must be authenticated.
- User can only view their own purchases; the system automatically scopes results to the authenticated user.

### Input Constraints

- `page` must be a positive integer (≥ 1); defaults to 1 if omitted.
- `page_size` must be between 1 and 100 (inclusive); defaults to 10 if omitted.
- `status` filter, if provided, must be one of: `pending`, `confirmed`, `reversed`.

### Data Constraints

- Only purchases belonging to the authenticated user are returned.
- Each purchase must include: merchant name, amount, purchase status, cashback amount, and cashback status.

### Behavior Constraints

- Results must be paginated using a page/page_size envelope.
- Purchases are returned in reverse chronological order (newest first).

---

## BDD Acceptance Criteria

**Scenario:** User successfully retrieves their purchase history
**Given** I am an authenticated user
**And** I have purchases in the system
**When** the authorization is verified
**Then** a paginated list of my purchases with merchant name, amount, purchase status, cashback amount, and cashback status is returned

**Scenario:** Unauthenticated user attempts to view purchases
**Given** I am not authenticated
**When** the system checks authentication
**Then** the request is rejected as unauthorized

**Scenario:** User with no purchases retrieves empty list
**Given** I am an authenticated user
**And** I have no purchases in the system
**When** the system retrieves purchases
**Then** an empty paginated list is returned

**Scenario:** User requests purchases with invalid pagination parameters
**Given** I am an authenticated user
**And** I send a request with a `page` value below the minimum (e.g., `page=0`)
**When** the API validates the input
**Then** the request is rejected with a validation error

**Scenario:** User requests purchases with an invalid status filter
**Given** I am an authenticated user
**And** I send a request with `status=badvalue`
**When** the API validates the status parameter
**Then** the request is rejected with error code `INVALID_PURCHASE_STATUS`

---

## Use Cases

### Happy Path

Authenticated user successfully retrieves purchase history

1. User requests their purchase list.
2. System verifies user authentication.
3. System retrieves paginated purchases for the user.
4. System batch-loads merchant names for all returned purchases.
5. System includes merchant name, amount, status, and cashback details in each item.
6. System returns the paginated purchase list.

### Sad Paths

#### Unauthenticated Request

1. Anonymous user requests purchase list.
2. System verifies authentication.
3. System finds no valid credentials.
4. System rejects the request as unauthorized.

#### Empty Results

1. User requests purchase list.
2. System verifies user authentication.
3. System retrieves purchases for the user.
4. System finds the user has no purchases.
5. System returns an empty paginated list.

#### Invalid Pagination Parameters

1. User requests purchases with an out-of-range page number or page size (e.g., `page=0`).
2. System verifies user authentication.
3. System validates the pagination parameters.
4. System detects that the parameters fall outside the allowed range.
5. System rejects the request with error code `VALIDATION_ERROR`.

#### Invalid Status Filter

1. User requests purchases with a status value that is not recognised (e.g., `status=badvalue`).
2. System verifies user authentication.
3. System validates the status parameter.
4. System detects that the status is not one of `pending`, `confirmed`, `reversed`.
5. System rejects the request with error code `INVALID_PURCHASE_STATUS`.

## API Contract

See [List user purchases](../../design/api-contracts/purchases/list-user-purchases.md) for detailed API specifications.
