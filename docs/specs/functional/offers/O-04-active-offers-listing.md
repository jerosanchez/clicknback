# O-04: Active Offers Listing

IMPORTANT: This is a living document, specs are subject to change.

## User Story

_As an authenticated user, I want to discover available cashback offers so that I can see what promotions are currently active and plan my purchases accordingly._

---

## Constraints

### User Constraints

- User must be authenticated
- User must have a valid, non-expired session token

### Offer Constraints

- Only offers with `active = true` should be included
- Only offers belonging to merchants with `active = true` should be included
- Only offers within the valid time window should be included: `start_date ≤ today ≤ end_date` (both bounds inclusive, using the server's current date in UTC)
- The response exposes `merchant_name` (not a raw `merchant_id`) for user-friendly display
- The response field for the monthly cashback cap is `monthly_cap` (not `monthly_cap_per_user`)

### Pagination Constraints

- Page number must be ≥ 1
- Page size must be ≥ 1 and ≤ `max_page_size` (system setting)
- Default page size is `default_page_size` (system setting)
- Out-of-range page returns an empty result set with correct pagination metadata

---

## BDD Acceptance Criteria

**Scenario:** Authenticated user successfully discovers active offers
**Given** I am an authenticated user
**And** active offers exist for active merchants within the valid time window
**When** I request the active offers list
**Then** a paginated list of active offers is returned with merchant names

**Scenario:** Unauthenticated user attempts to view active offers
**Given** I am not authenticated
**When** the system checks authentication
**Then** the request is rejected as unauthorized (401)

**Scenario:** User retrieves empty active offer list
**Given** I am an authenticated user
**And** no active offers exist, or all matching offers are outside the valid time window
**When** the system processes the request
**Then** an empty paginated list is returned (200 with empty `offers` array)

**Scenario:** Invalid pagination parameters
**Given** I am an authenticated user
**And** I send a request with pagination parameters outside allowed bounds (e.g. `page=0`, `page_size=0`, or `page_size` exceeding `max_page_size`)
**When** the API validates the input
**Then** the request is rejected with a 422 Unprocessable Entity error

**Scenario:** Expired offer is excluded
**Given** I am an authenticated user
**And** an offer's `end_date` is before today
**When** I request the active offers list
**Then** that offer does not appear in the response, even if `active = true`

**Scenario:** Future offer is excluded
**Given** I am an authenticated user
**And** an offer's `start_date` is after today
**When** I request the active offers list
**Then** that offer does not appear in the response, even if `active = true`

**Scenario:** Offer for inactive merchant is excluded
**Given** I am an authenticated user
**And** an offer is active but belongs to an inactive merchant
**When** I request the active offers list
**Then** that offer does not appear in the response

---

## Use Cases

### Happy Path

An authenticated user successfully discovers active offers

1. User requests the active offers list (optionally with pagination parameters).
2. System verifies the user's JWT token and confirms the user is active.
3. System resolves today's date (server UTC).
4. System queries offers joined with merchants, applying all three filters:
   a. `Offer.active = true`
   b. `Merchant.active = true`
   c. `Offer.start_date ≤ today ≤ Offer.end_date`
5. System applies pagination (offset/limit).
6. System returns the paginated offer list; each item includes `merchant_name` from the joined merchant record.

### Sad Paths

#### Unauthenticated Request

1. Anonymous user requests the active offers list.
2. System validates the Authorization header.
3. System finds no valid Bearer token.
4. System rejects the request as unauthorized (401).

#### Expired Offer Present in DB

1. Authenticated user requests the active offers list.
2. System resolves today's date.
3. System filters out any offer where `end_date < today`.
4. Those offers do not appear in the response.

#### Future Offer Present in DB

1. Authenticated user requests the active offers list.
2. System resolves today's date.
3. System filters out any offer where `start_date > today`.
4. Those offers do not appear in the response.

#### Offer Belonging to Inactive Merchant

1. Authenticated user requests the active offers list.
2. System joins offers with merchants.
3. System filters out offers whose merchant has `active = false`.
4. Those offers do not appear in the response.

#### Empty Results

1. Authenticated user requests the active offers list.
2. System applies all filters.
3. No offers match the criteria (all expired, future, or on inactive merchants).
4. System returns an empty paginated list.

#### Invalid Pagination Parameters

1. Authenticated user requests the active offers list with `page=0` or `page_size` out of range.
2. System validates pagination parameters at the API boundary.
3. System rejects the request with 422 Unprocessable Entity.

## API Contract

See [List active offers for users](../../design/api-contracts/offers/list-active-offers.md) for detailed API specifications.
