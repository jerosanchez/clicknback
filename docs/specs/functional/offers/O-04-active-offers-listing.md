# O-04: Active Offers Listing

IMPORTANT: This is a living document, specs are subject to change.

## User Story

_As an authenticated user, I want to discover available cashback offers so that I can see what promotions are currently active and plan my purchases accordingly._

---

## Constraints

### User Constraints

- User must be authenticated
- User must have valid session

### Offer Constraints

- Only active merchants should be included
- Only active offers should be included
- Offers must be within valid time window (start date <= now <= end date)
- Results must be paginated

---

## BDD Acceptance Criteria

**Scenario:** Authenticated user successfully discovers active offers
**Given** I am an authenticated user
**And** active offers exist for active merchants within valid time window
**When** the authorization is verified
**Then** a paginated list of active offers is returned

**Scenario:** Unauthenticated user attempts to view active offers
**Given** I am not authenticated
**When** the system checks authentication
**Then** the request is rejected as unauthorized

**Scenario:** User retrieves empty active offer list
**Given** I am an authenticated user
**And** no active offers exist or all offers are outside valid time window
**When** the system processes the request
**Then** an empty paginated list is returned

**Scenario:** User requests with invalid pagination parameters
**Given** I am an authenticated user
**And** I send a request with invalid pagination parameters
**When** the API validates the input
**Then** the request is rejected with a validation error

---

## Use Cases

### Happy Path

An authenticated user successfully discovers active offers

1. User requests active offers list.
2. System verifies user authentication.
3. System filters offers by merchant active status.
4. System filters offers by offer active status.
5. System filters offers by valid time window.
6. System returns paginated offer list.

### Sad Paths

#### Unauthenticated Request

1. Anonymous user requests active offers list.
2. System verifies authentication.
3. System finds no valid credentials.
4. System rejects the request as unauthorized.

#### Empty Results

1. User requests active offers list.
2. System verifies user authentication.
3. System filters offers by active status and time window.
4. System finds no offers match criteria.
5. System returns empty paginated list.

#### Invalid Pagination Parameters

1. User requests active offers with invalid page number or size.
2. System verifies user authentication.
3. System validates pagination parameters.
4. System detects invalid parameters.
5. System rejects the request with validation error.

## API Contract

See [List active offers for users](../../design/api-contracts/offers/list-active-offers.md) for detailed API specifications.
