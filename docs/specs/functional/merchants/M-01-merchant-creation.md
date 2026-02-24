# M-01: Merchant Creation

IMPORTANT: This is a living document, specs are subject to change.

## User Story

_As an admin, I want to register a new merchant in the system so that I can manage their cashback offers and track their transactions._

---

## Constraints

### Authorization Constraints

- Only authenticated admin users can create merchants
- Admin role must be verified before allowing creation

### Merchant Constraints

- Merchant details must be valid and complete
- Merchant name should be unique (if applicable)

---

## BDD Acceptance Criteria

**Scenario:** Admin successfully creates a new merchant
**Given** I am an authenticated admin user
**And** I create a merchant with valid details
**When** the merchant details are validated
**Then** the merchant is successfully created and returned

**Scenario:** Non-admin user attempts to create a merchant
**Given** I am an authenticated non-admin user
**And** I attempt to create a merchant with merchant details
**When** the system checks authorization
**Then** access is denied

**Scenario:** Unauthenticated user attempts to create a merchant
**Given** I am not authenticated
**And** I attempt to create a merchant with merchant details
**When** the system checks authentication
**Then** the request is rejected as unauthorized

**Scenario:** Admin creates merchant with invalid data
**Given** I am an authenticated admin user
**And** I attempt to create a merchant with incomplete or invalid details
**When** the API validates the input
**Then** the request is rejected with a validation error message

---

## Use Cases

### Happy Path

An authenticated admin successfully creates a new merchant

1. Admin submits merchant details.
2. System verifies admin authentication and role.
3. System validates merchant input.
4. System stores merchant record.
5. System returns the new merchant information.

### Sad Paths

#### Unauthorized - Non-Admin User

1. Non-admin user submits merchant details.
2. System verifies authentication.
3. System checks admin role.
4. System finds user does not have admin role.
5. System denies access.

#### Unauthenticated Request

1. Anonymous user submits merchant details.
2. System verifies authentication.
3. System finds no valid credentials.
4. System rejects the request as unauthorized.

#### Invalid Merchant Data

1. Admin submits merchant details with missing or invalid fields.
2. System verifies admin role.
3. System validates merchant input.
4. System detects validation errors.
5. System rejects the request with validation error details.

## API Contract

See [Create a merchant](../../design/api-contracts/merchants/create-merchant.md) for detailed API specifications.
