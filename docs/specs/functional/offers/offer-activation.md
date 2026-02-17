# Offer Activation

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
**And** I send a `PATCH /api/v1/offers/{id}/status` request to activate
**When** the activation request is processed
**Then** the API responds with `HTTP 200 OK` and the offer status is updated to active

**Scenario:** Admin successfully deactivates an offer
**Given** I am an authenticated admin user
**And** the offer exists with active status
**And** I send a `PATCH /api/v1/offers/{id}/status` request to deactivate
**When** the deactivation request is processed
**Then** the API responds with `HTTP 200 OK` and the offer status is updated to inactive

**Scenario:** Non-admin user attempts to modify offer status
**Given** I am an authenticated non-admin user
**And** I send a `PATCH /api/v1/offers/{id}/status` request
**When** the system checks authorization
**Then** the API responds with `HTTP 403 Forbidden`

**Scenario:** Admin attempts to modify non-existent offer
**Given** I am an authenticated admin user
**And** I send a `PATCH /api/v1/offers/{999}/status` request for a non-existent offer
**When** the system attempts to find the offer
**Then** the API responds with `HTTP 404 Not Found`

---

## Use Cases

### Happy Path

An admin successfully changes offer availability status

1. Admin sends status update request with target status.
2. System verifies admin authentication and role.
3. System retrieves offer record.
4. System updates offer status.
5. System persists change.
6. System returns `HTTP 200 OK` with updated offer info.

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
5. System returns `HTTP 404 Not Found`.

#### Unauthenticated Request

1. Anonymous user sends status update request.
2. System verifies authentication.
3. System finds no valid credentials.
4. System returns `HTTP 401 Unauthorized`.

## API Contract

See [Activate/deactivate offer](../../design/api-contracts/offers/activate-deactivate-offer.md) for detailed API specifications.
