# PU-05: Purchases Listing (Admin)

IMPORTANT: This is a living document, specs are subject to change.

## User Story

_As an admin, I want to monitor purchase activity across all users so that I can oversee the purchase lifecycle and track transaction patterns._

---

## Constraints

### Authorization Constraints

- Only authenticated admin users can list all purchases
- Admin role must be verified before allowing access

### Listing Constraints

- Results must be paginated and filterable
- Should support filtering by status, date range, user, or merchant
- All purchases from all users should be visible to admin

---

## BDD Acceptance Criteria

**Scenario:** Admin successfully retrieves all purchases
**Given** I am an authenticated admin user
**And** purchases exist in the system
**When** the authorization is verified
**Then** a paginated and filterable list of all purchases is returned

**Scenario:** Non-admin user attempts to list all purchases
**Given** I am an authenticated non-admin user
**When** the system checks authorization
**Then** access is denied

**Scenario:** Unauthenticated user attempts to list purchases
**Given** I am not authenticated
**When** the system checks authentication
**Then** the request is rejected as unauthorized

**Scenario:** Admin filters purchases by status
**Given** I am an authenticated admin user
**When** the system applies filters
**Then** only purchases with the requested status are returned

**Scenario:** Admin requests purchase list with invalid pagination parameters
**Given** I am an authenticated admin user
**When** the request contains invalid pagination parameters (e.g., negative page number)
**Then** a validation error is returned

---

## Use Cases

### Happy Path

Admin successfully retrieves purchase activity

1. Admin requests purchase list.
2. System verifies admin authentication and role.
3. System retrieves paginated purchase records.
4. System applies filters if provided.
5. System returns purchase list.

### Sad Paths

#### Unauthorized - Non-Admin User

1. Non-admin user requests purchase list.
2. System verifies authentication.
3. System checks admin role.
4. System finds user does not have admin role.
5. System returns `HTTP 403 Forbidden`.

#### Unauthenticated Request

1. Anonymous user requests purchase list.
2. System verifies authentication.
3. System finds no valid credentials.
4. System returns `HTTP 401 Unauthorized`.

#### Empty Results

1. Admin requests purchase list with filters.
2. System verifies admin role.
3. System retrieves purchases matching filters.
4. System finds no purchases match criteria.
5. System returns empty paginated list.

#### Invalid Pagination Parameters

1. Admin requests purchase list with invalid pagination values.
2. System verifies admin role.
3. System validates pagination parameters.
4. System detects invalid values (e.g., negative page number or oversized page size).
5. System rejects the request with validation error.
