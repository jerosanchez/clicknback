# M-02: Merchant Activation

IMPORTANT: This is a living document, specs are subject to change.

## User Story

_As an admin, I want to change merchant availability status so that I can control which merchants are actively offering cashback._

---

## Constraints

### Authorization Constraints

- Only authenticated admin users can modify merchant status
- Admin role must be verified before allowing status changes

### Merchant Constraints

- Merchant must exist in the system
- Status can only be toggled between active and inactive states

---

## BDD Acceptance Criteria

**Scenario:** Admin successfully activates a merchant
**Given** I am an authenticated admin user
**And** the merchant exists with inactive status
**When** the activation request is processed
**Then** the merchant status is updated to active

**Scenario:** Admin successfully deactivates a merchant
**Given** I am an authenticated admin user
**And** the merchant exists with active status
**When** the deactivation request is processed
**Then** the merchant status is updated to inactive

**Scenario:** Non-admin user attempts to modify merchant status
**Given** I am an authenticated non-admin user
**When** the system checks authorization
**Then** access is denied

**Scenario:** Admin attempts to modify non-existent merchant
**Given** I am an authenticated admin user
**When** the system attempts to find the merchant
**Then** a not found error is returned

---

## Use Cases

### Happy Path

An admin successfully changes merchant availability status

1. Admin sends status update request with target status.
2. System verifies admin authentication and role.
3. System retrieves merchant record.
4. System updates merchant status.
5. System persists status change.
6. System returns updated merchant info.

### Sad Paths

#### Unauthorized - Non-Admin User

1. Non-admin user sends status update request.
2. System verifies authentication.
3. System checks admin role.
4. System finds user does not have admin role.
5. System denies access.

#### Merchant Not Found

1. Admin sends status update request for non-existent merchant ID.
2. System verifies admin role.
3. System attempts to retrieve merchant.
4. System finds merchant does not exist.
5. System returns not found error.

#### Unauthenticated Request

1. Anonymous user sends status update request.
2. System verifies authentication.
3. System finds no valid credentials.
4. System rejects the request as unauthorized.

## API Contract

See [Activate/deactivate merchant](../../design/api-contracts/merchants/activate-deactivate-merchant.md) for detailed API specifications.
