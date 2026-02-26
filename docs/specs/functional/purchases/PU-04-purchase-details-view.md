# PU-04: Purchase Details View

IMPORTANT: This is a living document, specs are subject to change.

## User Story

_As an authenticated user, I want to view detailed information about a specific purchase so that I can audit individual transactions._

---

## Constraints

### User Constraints

- User must be authenticated
- User can only view details for their own purchases

### Purchase Constraints

- Purchase must exist
- Purchase must belong to the authenticated user

---

## BDD Acceptance Criteria

**Scenario:** User successfully views their purchase details
**Given** I am an authenticated user
**And** the purchase exists and belongs to me
**When** the authorization is verified and ownership is confirmed
**Then** the complete purchase and cashback details are returned

**Scenario:** Unauthenticated user attempts to view purchase details
**Given** I am not authenticated
**When** the system checks authentication
**Then** the request is rejected as unauthorized

**Scenario:** User attempts to view another user's purchase
**Given** I am an authenticated user
**And** the purchase exists but belongs to another user
**When** the system verifies ownership
**Then** access is denied or a not found error is returned

**Scenario:** User attempts to view non-existent purchase
**Given** I am an authenticated user
**When** the system attempts to find the purchase
**Then** a not found error is returned

---

## Use Cases

### Happy Path

Authenticated user successfully views purchase details

1. User requests purchase details by ID.
2. System verifies user authentication.
3. System retrieves purchase record.
4. System verifies purchase belongs to user.
5. System retrieves associated cashback details.
6. System returns detailed purchase information.

### Sad Paths

#### Unauthenticated Request

1. Anonymous user requests purchase details.
2. System verifies authentication.
3. System finds no valid credentials.
4. System rejects the request as unauthorized.

#### Ownership Violation

1. User A requests details for purchase belonging to User B.
2. System verifies user A authentication.
3. System retrieves purchase record.
4. System verifies ownership.
5. System finds purchase does not belong to user A.
6. System denies access or returns not found error.

#### Purchase Not Found

1. User requests purchase details for non-existent purchase ID.
2. System verifies user authentication.
3. System attempts to retrieve purchase.
4. System finds purchase does not exist.
5. System returns not found error.

## API Contract

See [Get purchase details](../../design/api-contracts/purchases/get-purchase-details.md) for detailed API specifications.
