# Active Offers Listing

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
**And** I send a `GET /api/v1/offers/active` request
**When** the authorization is verified
**Then** the API responds with `HTTP 200 OK` and returns a paginated list of active offers

**Scenario:** Unauthenticated user attempts to view active offers
**Given** I am not authenticated
**And** I send a `GET /api/v1/offers/active` request
**When** the system checks authentication
**Then** the API responds with `HTTP 401 Unauthorized`

**Scenario:** User retrieves empty active offer list
**Given** I am an authenticated user
**And** no active offers exist or all offers are outside valid time window
**And** I send a `GET /api/v1/offers/active` request
**When** the system processes the request
**Then** the API responds with `HTTP 200 OK` and returns an empty paginated list

**Scenario:** User requests with invalid pagination parameters
**Given** I am an authenticated user
**And** I send a `GET /api/v1/offers/active?page=abc` request with invalid pagination parameters
**When** the API validates the input
**Then** the API responds with `HTTP 400 Bad Request` and an error message

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
7. System returns `HTTP 200 OK` with active offers.

### Sad Paths

#### Unauthenticated Request

1. Anonymous user requests active offers list.
2. System verifies authentication.
3. System finds no valid credentials.
4. System returns `HTTP 401 Unauthorized`.

#### Empty Results

1. User requests active offers list.
2. System verifies user authentication.
3. System filters offers by active status and time window.
4. System finds no offers match criteria.
5. System returns `HTTP 200 OK` with empty paginated list.

#### Invalid Pagination Parameters

1. User requests active offers with invalid page number or size.
2. System verifies user authentication.
3. System validates pagination parameters.
4. System detects invalid parameters.
5. System returns `HTTP 400 Bad Request` with validation error.

## API Contract

See [List active offers for users](../../design/api-contracts/offers/list-active-offers.md) for detailed API specifications.
