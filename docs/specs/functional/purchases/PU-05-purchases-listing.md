# PU-05: Purchases Listing (Admin)

IMPORTANT: This is a living document, specs are subject to change.

## User Story

_As an admin, I want to monitor purchase activity across all users so that I can oversee the purchase lifecycle and track transaction patterns._

---

## Constraints

### Authorization Constraints

- Only authenticated admin users can list all purchases
- Admin role must be verified before allowing access
- A valid Bearer token with admin role is required; missing or non-admin tokens are rejected with `HTTP 401 Unauthorized`

### Listing Constraints

- Results must be paginated and filterable
- Supports filtering by `status`, `start_date`, `end_date`, `user_id`, and `merchant_id`
- All purchases from all users should be visible to admin
- Results are ordered by `created_at` descending (newest first)
- Default page size is 10; maximum page size is 100
- Page number is 1-based; must be ≥ 1

### Filter Constraints

- `status`: must be one of `pending`, `confirmed`, `reversed` (case-sensitive)
- `start_date` / `end_date`: ISO 8601 date format (`YYYY-MM-DD`); both are inclusive bounds on `created_at`
- `user_id` / `merchant_id`: valid UUID strings; unrecognised IDs yield an empty result set (not an error)
- If no filters are provided, all purchases are returned (paginated)

### Response Constraints

- Each item in the response includes: `id`, `external_id`, `user_id`, `merchant_id`, `offer_id`, `amount`, `currency`, `status`, `created_at`
- The envelope includes: `items`, `total` (total matching count), `page`, `page_size`

---

## BDD Acceptance Criteria

**Scenario:** Admin successfully retrieves all purchases
**Given** I am an authenticated admin user
**And** purchases exist in the system
**When** the authorization is verified
**Then** a paginated list of all purchases is returned ordered by `created_at` descending

**Scenario:** Non-admin user attempts to list all purchases
**Given** I am an authenticated non-admin user
**When** the system checks authorization
**Then** access is denied with `HTTP 401 Unauthorized`

**Scenario:** Unauthenticated user attempts to list purchases
**Given** I am not authenticated
**When** the system checks authentication
**Then** the request is rejected with `HTTP 401 Unauthorized`

**Scenario:** Admin filters purchases by status
**Given** I am an authenticated admin user
**When** the request includes `status=confirmed`
**Then** only purchases with `status = confirmed` are returned

**Scenario:** Admin filters purchases by user
**Given** I am an authenticated admin user
**When** the request includes a valid `user_id`
**Then** only purchases belonging to that user are returned

**Scenario:** Admin filters purchases by merchant
**Given** I am an authenticated admin user
**When** the request includes a valid `merchant_id`
**Then** only purchases associated with that merchant are returned

**Scenario:** Admin filters purchases by date range
**Given** I am an authenticated admin user
**When** the request includes `start_date` and/or `end_date`
**Then** only purchases whose `created_at` falls within the specified range are returned

**Scenario:** Admin requests purchase list with invalid pagination parameters
**Given** I am an authenticated admin user
**When** the request contains invalid pagination parameters (e.g., `page=0` or `page_size=0`)
**Then** a `422 Unprocessable Entity` validation error is returned

**Scenario:** Admin requests purchase list and no results match
**Given** I am an authenticated admin user
**And** no purchases match the applied filters
**When** the authorization is verified and filters are applied
**Then** an empty paginated list is returned with `total = 0`

---

## Use Cases

### Happy Path

Admin successfully retrieves purchase activity

1. Admin requests purchase list (optionally with filters and pagination parameters).
2. System verifies admin authentication and role.
3. System validates pagination parameters.
4. System applies filters to the purchase dataset.
5. System retrieves the total matching count and the current page of records.
6. System returns paginated purchase list ordered newest first.

### Sad Paths

#### Unauthorized - Non-Admin User

1. Non-admin user requests purchase list.
2. System validates the Bearer token.
3. System extracts role from token.
4. System finds role is not `admin`.
5. System returns `HTTP 401 Unauthorized` with code `INVALID_TOKEN`.

#### Unauthenticated Request

1. Anonymous user requests purchase list without a Bearer token.
2. System detects missing credentials.
3. System returns `HTTP 401 Unauthorized`.

#### Empty Results

1. Admin requests purchase list with filters that match no records.
2. System verifies admin role.
3. System applies filters.
4. System finds no purchases match criteria.
5. System returns `{ "items": [], "total": 0, "page": 1, "page_size": 10 }`.

#### Invalid Pagination Parameters

1. Admin sends request with `page=0` or `page_size=0` or `page_size=200`.
2. System verifies admin role.
3. System validates pagination query parameters.
4. System detects out-of-range values.
5. System returns `HTTP 422 Unprocessable Entity` with field-level validation details.

#### Admin Filters by User

1. Admin requests purchase list filtered by a specific `user_id`.
2. System verifies admin role.
3. System applies `user_id` filter.
4. System returns only purchases belonging to that user.

#### Admin Filters by Date Range

1. Admin requests purchase list with `start_date` and `end_date`.
2. System verifies admin role.
3. System applies date bounds to `created_at`.
4. System returns only purchases created within the specified range (both bounds inclusive).
