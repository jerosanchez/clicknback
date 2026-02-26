# M-03: Merchants Listing (Admin)

IMPORTANT: This is a living document, specs are subject to change.

## User Story

_As an admin, I want to view a list of all merchants so that I can monitor and manage merchant records._

---

## Constraints

### Authorization Constraints

- Only authenticated admin users can list merchants
- Admin role must be verified before allowing access

### Listing Constraints

- Results must be paginated
- Default page size should be appropriate (e.g., 20 items)
- Support sorting and filtering options if applicable

---

## BDD Acceptance Criteria

**Scenario:** Admin successfully retrieves merchant list
**Given** I am an authenticated admin user
**And** merchants exist in the system
**When** the authorization is verified
**Then** a paginated list of merchants is returned

**Scenario:** Non-admin user attempts to list merchants
**Given** I am an authenticated non-admin user
**When** the system checks authorization
**Then** access is denied

**Scenario:** Unauthenticated user attempts to list merchants
**Given** I am not authenticated
**When** the system checks authentication
**Then** the request is rejected as unauthorized

**Scenario:** Admin retrieves empty merchant list
**Given** I am an authenticated admin user
**And** no merchants exist in the system
**When** the system processes the request
**Then** an empty paginated list is returned

---

## Use Cases

### Happy Path

An authenticated admin successfully retrieves merchant list

1. Admin requests merchant list.
2. System verifies admin authentication and role.
3. System retrieves paginated merchant records.
4. System returns merchant list.

### Sad Paths

#### Unauthorized - Non-Admin User

1. Non-admin user requests merchant list.
2. System verifies authentication.
3. System checks admin role.
4. System finds user does not have admin role.
5. System returns `HTTP 403 Forbidden`.

#### Unauthenticated Request

1. Anonymous user requests merchant list.
2. System verifies authentication.
3. System finds no valid credentials.
4. System rejects the request as unauthorized.

#### Empty ResultsS

1. Admin requests merchant list.
2. System verifies admin role.
3. System retrieves merchant records from database.
4. System finds no merchants exist.
5. System returns empty paginated list.

## API Contract

See [List merchants](../../design/api-contracts/merchants/list-merchants.md) for detailed API specifications.
