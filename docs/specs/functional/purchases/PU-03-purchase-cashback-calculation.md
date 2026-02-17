# PU-03: Purchase Cashback Calculation

IMPORTANT: This is a living document, specs are subject to change.

## User Story

_As a system process, I want to automatically calculate and allocate cashback for purchases so that users can earn rewards based on active offers._

---

## Constraints

### Purchase Constraints

- Purchase must exist with status `pending`
- Merchant must be active

### Cashback Constraints

- Cashback calculation must respect offer eligibility rules
- Monthly cap per user must be enforced
- Pending balance must be updated atomically

---

## BDD Acceptance Criteria

**Scenario:** System successfully calculates cashback for eligible purchase
**Given** the purchase exists with status `pending`
**And** an active offer exists for the merchant
**And** the monthly cap has not been exceeded
**When** the system evaluates eligibility and applies calculation rules
**Then** the cashback transaction is created with status `pending` and wallet `pending_balance` is increased

**Scenario:** System skips cashback for inactive merchant
**Given** the purchase exists with status `pending`
**And** the merchant is inactive
**When** the system evaluates eligibility
**Then** no cashback transaction is created and the purchase remains `pending`

**Scenario:** System enforces monthly cap limit
**Given** the purchase exists with status `pending`
**And** the user has already reached the monthly cashback cap for this merchant
**When** the system applies cashback calculation rules
**Then** cashback is calculated but capped at the remaining monthly limit

**Scenario:** System handles multiple competing offers
**Given** the purchase exists with status `pending`
**And** multiple active offers exist for the merchant
**When** the system evaluates offer eligibility
**Then** the system applies appropriate offer selection logic (highest value, first active, etc.)

---

## Use Cases

### Happy Path

System successfully calculates and allocates cashback

1. System receives purchase with status `pending`.
2. System retrieves merchant record.
3. System verifies merchant is active.
4. System retrieves active offers for merchant.
5. System evaluates offer eligibility for user.
6. System applies cashback calculation rules.
7. System checks monthly cap policy.
8. System creates pending cashback transaction.
9. System increases wallet `pending_balance`.
10. System returns success.

### Sad Paths

#### Inactive Merchant

1. System receives purchase with status `pending`.
2. System retrieves merchant record.
3. System verifies merchant status.
4. System finds merchant is inactive.
5. System skips cashback calculation and exits.

#### No Active Offer

1. System receives purchase with status `pending`.
2. System retrieves merchant record.
3. System verifies merchant is active.
4. System searches for active offers.
5. System finds no active offers for merchant.
6. System skips cashback calculation and exits.

#### Monthly Cap Exceeded

1. System receives purchase with status `pending`.
2. System retrieves merchant record and active offers.
3. System calculates base cashback amount.
4. System checks monthly cap for user/merchant combination.
5. System finds user has already hit monthly limit.
6. System either caps the amount or skips calculation based on policy.

#### Invalid Purchase Amount

1. System receives purchase with invalid or negative amount.
2. System validates purchase data.
3. System detects invalid amount.
4. System exits without creating cashback transaction.
