# O-05: Offers Listing

IMPORTANT: This is a living document, specs are subject to change.

## User Story

_As an authenticated user, I want to view a paginated list of all offers so that I can browse and filter available and past cashback promotions._

---

## Constraints

### Authorization Constraints

- Any authenticated user (user or admin role) can list offers
- Unauthenticated requests are rejected

### Listing Constraints

- Results must be paginated; default page size is 20, maximum is 100
- Optional filtering by `status` (`active` / `inactive`), `merchant_id`, `date_from`, and `date_to`
- `date_from` and `date_to` filters use ISO 8601 date format (`YYYY-MM-DD`)
- `date_from` must not be after `date_to` when both are provided

---

## BDD Acceptance Criteria

**Scenario:** Authenticated user successfully retrieves offer list

**Given** I am an authenticated user
**And** offers exist in the system
**When** I send `GET /api/v1/offers`
**Then** a paginated list of offers with full details is returned with HTTP 200

**Scenario:** User filters offer list by status

**Given** I am an authenticated user
**When** the request includes `status=active` or `status=inactive`
**Then** only offers matching that status are returned

**Scenario:** User filters offer list by merchant

**Given** I am an authenticated user
**When** the request includes a valid `merchant_id` filter
**Then** only offers belonging to that merchant are returned

**Scenario:** User filters offer list by date range

**Given** I am an authenticated user
**When** the request includes `date_from` and/or `date_to` filters
**Then** only offers whose validity window overlaps the specified date range are returned

**Scenario:** Unauthenticated user attempts to list offers

**Given** I am not authenticated
**When** I send `GET /api/v1/offers`
**Then** the request is rejected with HTTP 401 Unauthorized

**Scenario:** Empty offer list

**Given** I am an authenticated user
**And** no offers exist or no offers match the applied filters
**When** I send `GET /api/v1/offers`
**Then** an empty paginated list is returned with HTTP 200

**Scenario:** Invalid pagination parameters

**Given** I am an authenticated user
**When** the request contains invalid pagination parameters (e.g. `offset=-1`, `limit=0`)
**Then** HTTP 422 is returned with `VALIDATION_ERROR` and a `violations` list

**Scenario:** Invalid status filter value

**Given** I am an authenticated user
**When** the request contains a `status` value not in `[active, inactive]`
**Then** HTTP 400 is returned with `VALIDATION_ERROR` identifying the `status` field

**Scenario:** Inverted date range

**Given** I am an authenticated user
**When** the request contains `date_from` that is after `date_to`
**Then** HTTP 400 is returned with `VALIDATION_ERROR` identifying the `date_from` field

---

## Use Cases

### Use Case 1: List Offers (Happy Path)

1. Authenticated user sends `GET /api/v1/offers` with optional filters.
2. System verifies authentication.
3. System validates all filter values (`status`, `date_from`/`date_to` cross-field check).
4. System retrieves paginated offer records matching the applied filters.
5. System returns paginated offer list with status and validity information.

### Use Case 2: Unauthenticated Request

1. Anonymous user sends `GET /api/v1/offers`.
2. System checks for a valid Bearer token.
3. No valid token is found.
4. System returns HTTP 401 Unauthorized.

### Use Case 3: Empty Results

1. Authenticated user sends `GET /api/v1/offers` with filters that match nothing.
2. System verifies authentication and validates parameters.
3. System finds no matching offers.
4. System returns HTTP 200 with an empty `data` array.

### Use Case 4: Invalid Status Filter

1. Authenticated user sends `GET /api/v1/offers?status=pending`.
2. System verifies authentication.
3. System detects `status` value is not `active` or `inactive`.
4. System returns HTTP 400 with `VALIDATION_ERROR` and a `violations` list identifying `status`.

### Use Case 5: Inverted Date Range

1. Authenticated user sends `GET /api/v1/offers?date_from=2026-12-31&date_to=2026-01-01`.
2. System verifies authentication.
3. System detects `date_from` is after `date_to`.
4. System returns HTTP 400 with `VALIDATION_ERROR` and a `violations` list identifying `date_from`.

## API Contract

See [List Offers (API contract)](../../design/api-contracts/offers/list-offers.md) for detailed API specifications.
