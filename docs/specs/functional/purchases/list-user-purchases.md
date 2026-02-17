# List User Purchases

IMPORTANT: This is a living document, specs are subject to change.

## User Story

_As an authenticated user, I want to view my purchase history so that I can audit my transactions and see associated cashback._

---

## Constraints

### User Constraints

- User must be authenticated
- User can only view their own purchases

### Listing Constraints

- Results must be paginated
- Only purchases belonging to the user should be returned
- Each purchase should include merchant, amount, status, cashback amount, and cashback status

---

## BDD Acceptance Criteria

**Scenario:** User successfully retrieves their purchase history
**Given** I am an authenticated user
**And** I have purchases in the system
**And** I send a `GET /api/v1/purchases` request
**When** the authorization is verified
**Then** the API responds with `HTTP 200 OK` and returns a paginated list of my purchases with merchant, amount, purchase status, cashback amount, and cashback status

**Scenario:** Unauthenticated user attempts to view purchases
**Given** I am not authenticated
**And** I send a `GET /api/v1/purchases` request
**When** the system checks authentication
**Then** the API responds with `HTTP 401 Unauthorized`

**Scenario:** User with no purchases retrieves empty list
**Given** I am an authenticated user
**And** I have no purchases in the system
**And** I send a `GET /api/v1/purchases` request
**When** the system retrieves purchases
**Then** the API responds with `HTTP 200 OK` and returns an empty paginated list

**Scenario:** User requests purchases with invalid pagination
**Given** I am an authenticated user
**And** I send a `GET /api/v1/purchases?page=abc` request with invalid parameters
**When** the API validates the input
**Then** the API responds with `HTTP 400 Bad Request` and an error message

---

## Use Cases

### Happy Path

Authentication user successfully retrieves purchase history

1. User requests their purchase list.
2. System verifies user authentication.
3. System retrieves paginated purchases for the user.
4. System includes merchant, amount, status, and cashback details.
5. System returns `HTTP 200 OK` with purchase list.

### Sad Paths

**Unauthenticated Request**

1. Anonymous user requests purchase list.
2. System verifies authentication.
3. System finds no valid credentials.
4. System returns `HTTP 401 Unauthorized`.

**Empty Results**

1. User requests purchase list.
2. System verifies user authentication.
3. System retrieves purchases for the user.
4. System finds user has no purchases.
5. System returns `HTTP 200 OK` with empty paginated list.

**Invalid Pagination Parameters**

1. User requests purchases with invalid page number or size.
2. System verifies user authentication.
3. System validates pagination parameters.
4. System detects invalid parameters.
5. System returns `HTTP 400 Bad Request` with validation error.
