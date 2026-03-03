# O-01: Offer Creation

IMPORTANT: This is a living document, specs are subject to change.

## User Story

_As an admin, I want to create cashback offers for merchants so that I can define the terms and conditions of cashback promotions._

---

## Constraints

### Authorization Constraints

- Only authenticated admin users can create offers
- Admin role must be verified before allowing creation

### Offer Constraints

- Associated merchant must exist and be active
- Cashback amount must be positive (percentage or fixed)
- Cashback amount (percentage) should not exceed the maximum (20%)
- Start date must be before or equal to end date
- Monthly cap per user must be positive
- Valid dates must be in the future (or current date for start)
- Only one active offer per merchant

---

## BDD Acceptance Criteria

**Scenario:** Admin successfully creates a new offer
**Given** I am an authenticated admin user
**And** the merchant exists and is active
**When** the offer details are validated
**Then** the new offer is successfully created and returned

**Scenario:** Non-admin user attempts to create an offer
**Given** I am an authenticated non-admin user
**When** the system checks authorization
**Then** access is denied

**Scenario:** Admin creates offer for non-existent merchant
**Given** I am an authenticated admin user
**And** I attempt to create an offer referencing a non-existent merchant
**When** the system validates the merchant reference
**Then** an error is returned indicating merchant not found

**Scenario:** Admin creates offer for non-active merchant
**Given** I am an authenticated admin user
**And** I attempt to create an offer referencing a non-active merchant
**When** the system validates the merchant reference
**Then** an error is returned indicating merchant is not active

**Scenario:** Admin creates offer with invalid date range (start date)
**Given** I am an authenticated admin user
**And** I attempt to create an offer where start date is not today or future
**When** the API validates the input
**Then** the request is rejected with a date validation error

**Scenario:** Admin creates offer with invalid date range (end date)
**Given** I am an authenticated admin user
**And** I attempt to create an offer where end date is before start date
**When** the API validates the input
**Then** the request is rejected with a date validation error

**Scenario:** Admin creates offer with invalid cashback configuration (fixed amount)
**Given** I am an authenticated admin user
**And** I attempt to create an offer with zero or negative fixed amount
**When** the API validates the input
**Then** the request is rejected with a validation error

**Scenario:** Admin creates offer with invalid cashback configuration (percentage)
**Given** I am an authenticated admin user
**And** I attempt to create an offer with zero, negative or greater than 20.0%
**When** the API validates the input
**Then** the request is rejected with a validation error

**Scenario**: Admin attempts to create a new offer for a merchant with an existing active offer
**Given** I am an authenticated admin user
**And** the merchant already has an active offer
**When** I submit a request to create a new offer for that merchant
**Then** the system rejects the request with a validation error indicating only one active offer is allowed per merchant

---

## Use Cases

### Happy Path

An admin successfully creates a new cashback offer

1. Admin submits offer details including merchant, cashback amount, dates, and monthly cap.
2. System verifies admin authentication and role.
3. System validates merchant exists and is active.
4. System validates offer configuration (dates, amounts, caps).
5. System stores offer record.
6. System returns new offer info.

### Sad Paths

#### Unauthorized - Non-Admin User

1. Non-admin user submits offer details.
2. System verifies authentication.
3. System checks admin role.
4. System finds user does not have admin role.
5. System returns `HTTP 403 Forbidden`.

#### Merchant Not Active

1. Admin submits offer for a merchant that exists but is not active.
2. System verifies admin role.
3. System validates merchant status.
4. System detects merchant is not active.
5. System rejects the request with a validation error indicating the merchant must be active.

#### Invalid Date Range

1. Admin submits offer with end date before start date.
2. System verifies admin role.
3. System validates offer configuration.
4. System detects invalid date range.
5. System rejects the request with validation error.

#### Non-Existent Merchant

1. Admin submits offer referencing non-existent merchant ID.
2. System verifies admin role.
3. System validates merchant reference.
4. System finds merchant does not exist.
5. System returns error indicating merchant not found.

#### Invalid Cashback Configuration

1. Admin submits offer with negative or zero cashback amount.
2. System verifies admin role.
3. System validates offer configuration.
4. System detects invalid cashback amount.
5. System rejects the request with validation error.

#### Merchant Already Has Active Offer

1. Admin submits offer for a merchant that already has an active offer.
2. System verifies admin role.
3. System validates offer configuration.
4. System detects the merchant already has an active offer.
5. System rejects the request with a validation error indicating only one active offer is allowed per merchant.

## API Contract

See [Create cashback offer](../../design/api-contracts/offers/create-offer.md) for detailed API specifications.
