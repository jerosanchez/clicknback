# O-05: Offers Listing (Admin)

IMPORTANT: This is a living document, specs are subject to change.

## User Story

_As an admin, I want to view a list of all offers with their status so that I can monitor and manage cashback promotions._

---

## Constraints

### Authorization Constraints

- Only authenticated admin users can list offers
- Admin role must be verified before allowing access

### Listing Constraints

- Results must be paginated
- Default page size should be appropriate (e.g., 20 items)
- Offer status information must be included
- Support filtering by status, merchant, or date range

---

## BDD Acceptance Criteria

**Scenario:** Admin successfully retrieves offer list with status
**Given** I am an authenticated admin user
**And** offers exist in the system
**When** the authorization is verified
**Then** a paginated list of offers with status information is returned

**Scenario:** Admin filters offer list by status
**Given** I am an authenticated admin user
**When** the request includes a valid `status` filter (`active` or `inactive`)
**Then** only offers matching that status are returned

**Scenario:** Admin filters offer list by merchant
**Given** I am an authenticated admin user
**When** the request includes a valid `merchant_id` filter
**Then** only offers belonging to that merchant are returned

**Scenario:** Admin filters offer list by date range
**Given** I am an authenticated admin user
**When** the request includes `date_from` and/or `date_to` filters
**Then** only offers whose validity window overlaps the specified date range are returned

**Scenario:** Non-admin user attempts to list offers
**Given** I am an authenticated non-admin user
**When** the system checks authorization
**Then** access is denied

**Scenario:** Unauthenticated user attempts to list offers
**Given** I am not authenticated
**When** the system checks authentication
**Then** the request is rejected as unauthorized

**Scenario:** Admin retrieves empty offer list
**Given** I am an authenticated admin user
**And** no offers exist in the system
**When** the system processes the request
**Then** an empty paginated list is returned

**Scenario:** Admin requests offer list with invalid pagination parameters
**Given** I am an authenticated admin user
**When** the request contains invalid pagination parameters (e.g., negative page number)
**Then** a validation error is returned

**Scenario:** Admin provides an invalid status filter value
**Given** I am an authenticated admin user
**When** the request contains a `status` filter value not in `[active, inactive]`
**Then** a validation error is returned identifying the invalid status value

**Scenario:** Admin provides an inverted date range
**Given** I am an authenticated admin user
**When** the request contains `date_from` that is after `date_to`
**Then** a validation error is returned identifying the invalid date range

---

## Use Cases

### Happy Path

An authenticated admin successfully retrieves offer list

1. Admin requests offer list (optionally with `status`, `merchant_id`, `date_from`, or `date_to` filters).
2. System verifies admin authentication and role.
3. System validates all filter values.
4. System retrieves paginated offer records matching the applied filters.
5. System returns paginated offer list with status and validity information.

### Sad Paths

#### Unauthorized - Non-Admin User

1. Non-admin user requests offer list.
2. System verifies authentication.
3. System checks admin role.
4. System finds user does not have admin role.
5. System returns `HTTP 403 Forbidden`.

#### Unauthenticated Request

1. Anonymous user requests offer list.
2. System verifies authentication.
3. System finds no valid credentials.
4. System returns `HTTP 401 Unauthorized`.

#### Empty Results

1. Admin requests offer list.
2. System verifies admin role.
3. System retrieves offer records from database.
4. System finds no offers exist (or none match the applied filters).
5. System returns empty paginated list.

#### Invalid Pagination Parameters

1. Admin requests offer list with invalid pagination values.
2. System verifies admin role.
3. System validates pagination parameters.
4. System detects invalid values (e.g., negative page number or oversized page size).
5. System rejects the request with validation error.

#### Invalid Status Filter Value

1. Admin requests offer list with a `status` value that is not `active` or `inactive`.
2. System verifies admin role.
3. System validates query parameters.
4. System detects the unrecognised status value.
5. System rejects the request with `HTTP 400 Bad Request` and a validation error identifying the `status` field.

#### Invalid Date Range (date_from after date_to)

1. Admin requests offer list with `date_from` set after `date_to`.
2. System verifies admin role.
3. System validates query parameters.
4. System detects that `date_from` is after `date_to`.
5. System rejects the request with `HTTP 400 Bad Request` and a validation error identifying the `date_from` field.

## API Contract

See [List all offers](../../design/api-contracts/offers/list-offers.md) for detailed API specifications.
