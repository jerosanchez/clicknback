# Offer Creation

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
- Start date must be before or equal to end date
- Monthly cap per user must be positive
- Valid dates must be in the future (or current date for start)

---

## BDD Acceptance Criteria

**Scenario:** Admin successfully creates a new offer
**Given** I am an authenticated admin user
**And** the merchant exists and is active
**And** I send a `POST /api/v1/offers` request with valid offer details including cashback type, dates, and monthly cap
**When** the offer details are validated
**Then** the API responds with `HTTP 201 Created` and returns the new offer information

**Scenario:** Non-admin user attempts to create an offer
**Given** I am an authenticated non-admin user
**And** I send a `POST /api/v1/offers` request with offer details
**When** the system checks authorization
**Then** the API responds with `HTTP 403 Forbidden`

**Scenario:** Admin creates offer with invalid date range
**Given** I am an authenticated admin user
**And** I send a `POST /api/v1/offers` request where end date is before start date
**When** the API validates the input
**Then** the API responds with `HTTP 400 Bad Request` and an error message describing the date validation issue

**Scenario:** Admin creates offer for non-existent merchant
**Given** I am an authenticated admin user
**And** I send a `POST /api/v1/offers` request referencing a non-existent merchant
**When** the system validates the merchant reference
**Then** the API responds with `HTTP 400 Bad Request` or `HTTP 404 Not Found` indicating merchant not found

---

## Use Cases

### Happy Path

An admin successfully creates a new cashback offer

1. Admin submits offer details including merchant, cashback amount, dates, and monthly cap.
2. System verifies admin authentication and role.
3. System validates merchant exists and is active.
4. System validates offer configuration (dates, amounts, caps).
5. System stores offer record.
6. System returns `HTTP 201 Created` with new offer info.

### Sad Paths

#### Unauthorized - Non-Admin User

1. Non-admin user submits offer details.
2. System verifies authentication.
3. System checks admin role.
4. System finds user does not have admin role.
5. System returns `HTTP 403 Forbidden`.

#### Invalid Date Range

1. Admin submits offer with end date before start date.
2. System verifies admin role.
3. System validates offer configuration.
4. System detects invalid date range.
5. System returns `HTTP 400 Bad Request` with validation error.

#### Non-Existent Merchant

1. Admin submits offer referencing non-existent merchant ID.
2. System verifies admin role.
3. System validates merchant reference.
4. System finds merchant does not exist.
5. System returns `HTTP 400 Bad Request` or `HTTP 404 Not Found`.

#### Invalid Cashback Configuration

1. Admin submits offer with negative or zero cashback amount.
2. System verifies admin role.
3. System validates offer configuration.
4. System detects invalid cashback amount.
5. System returns `HTTP 400 Bad Request` with validation error.
