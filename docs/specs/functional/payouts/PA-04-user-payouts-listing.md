# PA-04: User Payouts Listing

IMPORTANT: This is a living document, specs are subject to change.

## User Story

_As an authenticated user, I want to view my withdrawal history so that I can audit all payout requests and their status._

---

## Constraints

### User Constraints

- User must be authenticated
- User can only view their own payouts

### Listing Constraints

- Results must be paginated
- Only payouts belonging to the user should be returned

---

## BDD Acceptance Criteria

**Scenario:** User successfully retrieves their payout history
**Given** I am an authenticated user
**And** I have payouts in the system
**When** the authorization is verified
**Then** a paginated list of my payouts with status and amount information is returned

**Scenario:** Unauthenticated user attempts to view payouts
**Given** I am not authenticated
**When** the system checks authentication
**Then** the request is rejected as unauthorized

**Scenario:** User with no payouts retrieves empty list
**Given** I am an authenticated user with no payout requests
**When** the system retrieves payouts
**Then** an empty paginated list is returned

**Scenario:** User requests payouts with invalid pagination
**Given** I am an authenticated user
**And** I send a request with invalid parameters
**When** the API validates the input
**Then** the request is rejected with a validation error

---

## Use Cases

### Happy Path

Authenticated user successfully retrieves payout history

1. User requests their payout list.
2. System verifies user authentication.
3. System retrieves paginated payouts for the user.
4. System includes amount, status, and date information.
5. System returns payout list.

### Sad Paths

#### Unauthenticated Request

1. Anonymous user requests payout history.
2. System verifies authentication.
3. System finds no valid credentials.
4. System rejects the request as unauthorized.

#### Empty Results

1. User requests payout history.
2. System verifies user authentication.
3. System retrieves payouts for the user.
4. System finds user has no payouts.
5. System returns empty paginated list.

#### Invalid Pagination Parameters

1. User requests payouts with invalid page number or size.
2. System verifies user authentication.
3. System validates pagination parameters.
4. System detects invalid parameters.
5. System rejects the request with validation error.

## API Contract

See [List user payouts](../../design/api-contracts/payouts/list-user-payouts.md) for detailed API specifications.
