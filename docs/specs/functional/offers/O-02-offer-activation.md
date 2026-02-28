# O-02: Offer Activation

IMPORTANT: This is a living document, specs are subject to change.

## User Story

_As an admin, I want to control offer availability so that I can enable or disable cashback promotions without deleting them._

---

## Constraints

### Authorization Constraints

- Only authenticated admin users can modify offer status
- Admin role must be verified before allowing status changes

### Offer Constraints

- Offer must exist in the system
- Status can only be toggled between active and inactive states

---

## BDD Acceptance Criteria

**Scenario:** Admin successfully activates an offer
**Given** I am an authenticated admin user
**And** the offer exists with inactive status
**When** the activation request is processed
**Then** the offer status is updated to active

**Scenario:** Admin successfully deactivates an offer
**Given** I am an authenticated admin user
**And** the offer exists with active status
**When** the deactivation request is processed
**Then** the offer status is updated to inactive

**Scenario:** Non-admin user attempts to modify offer status
**Given** I am an authenticated non-admin user
**When** the system checks authorization
**Then** access is denied

**Scenario:** Admin attempts to modify non-existent offer
**Given** I am an authenticated admin user
**When** the system attempts to find the offer
**Then** a not found error is returned

**Scenario:** Admin submits status update with invalid status value
**Given** I am an authenticated admin user
**And** the offer exists in the system
**When** the API validates the request with an unrecognized status value
**Then** the request is rejected with a validation error

---

## Use Cases

### Happy Path

An admin successfully changes offer availability status

1. Admin sends status update request with target status.
2. System verifies admin authentication and role.
3. System retrieves offer record.
4. System updates offer status.
5. System persists change.
6. System returns updated offer info.

### Sad Paths

#### Unauthorized - Non-Admin User

1. Non-admin user sends status update request.
2. System verifies authentication.
3. System checks admin role.
4. System finds user does not have admin role.
5. System returns `HTTP 403 Forbidden`.

#### Offer Not Found

1. Admin sends status update request for non-existent offer ID.
2. System verifies admin role.
3. System attempts to retrieve offer.
4. System finds offer does not exist.
5. System returns not found error.

#### Unauthenticated Request

1. Anonymous user sends status update request.
2. System verifies authentication.
3. System finds no valid credentials.
4. System rejects the request as unauthorized.

#### Invalid Status Value

1. Admin sends status update request with unrecognized status value.
2. System verifies admin role.
3. System validates request parameters.
4. System detects invalid status value.
5. System rejects the request with validation error.

## API Contract

See [Activate/deactivate offer](../../design/api-contracts/offers/activate-deactivate-offer.md) for detailed API specifications.
