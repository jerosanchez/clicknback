# PU-01: Purchase Ingestion

IMPORTANT: This is a living document, specs are subject to change.

## User Story

_As an external system, I want to record user purchases through a webhook so that the platform can track transactions and calculate cashback._

---

## Constraints

### Request Constraints

- Purchase must include a non-empty external unique identifier (`external_id`)
- Purchase must include a valid UUID for `user_id` and `merchant_id`
- Purchase amount must be a positive number (greater than zero)
- Currency must be `EUR`. The platform currently accepts purchases in EUR only.
  Multi-currency support is deferred to a future release.
- **The `user_id` in the request must match the authenticated user's ID.** Users may only
  ingest purchases on behalf of themselves. Submitting a `user_id` that belongs to another
  user is rejected with a 403 Forbidden error. See ADR 012 for the rationale and the
  intended future extension path for external-system ingestion.
- The referenced user must exist and be active in the system
- The referenced merchant must exist and be active in the system
- A valid offer must be available for the merchant: the merchant must have an active offer
  whose date range includes today (i.e. `start_date <= today <= end_date`, inclusive)
- The offer is resolved automatically by the system from the merchant — it is not passed
  by the caller in the request body
- Requests must be idempotent: re-submitting the same `external_id` yields a conflict
  response; no duplicate record is created

### Data Constraints

- `external_id` must be unique; duplicate submissions are rejected (idempotent operation)
- `offer_id` is stored on the purchase after system resolution; it is not provided by the caller

---

## BDD Acceptance Criteria

**Scenario:** User successfully ingests their own purchase
**Given** I send a purchase ingestion request where `user_id` matches my authenticated identity,
  with a valid merchant and unique external_id
**When** the merchant has an active offer valid for today's date and the external_id is not already in the system
**Then** the new purchase is successfully created with status `pending`, the resolved offer is associated,
  the cashback amount is calculated from the offer and stored on the purchase, and the user's wallet
  `pending_balance` is increased by the cashback amount atomically with the purchase record

**Scenario:** User attempts to ingest a purchase for another user
**Given** I send a purchase ingestion request where `user_id` belongs to a different user
**When** the system enforces the self-ingestion ownership policy
**Then** a 403 Forbidden error is returned

**Scenario:** User submits duplicate purchase (idempotent)
**Given** I send a purchase ingestion request with the same external_id as a previous request
**When** the system checks for an existing purchase
**Then** a conflict error is returned with details about the previously ingested purchase — no duplicate is created

**Scenario:** User submits purchase with invalid data
**Given** I send a purchase ingestion request with missing required fields or invalid values
  (e.g. missing external_id, negative amount, malformed UUID, or currency not exactly 3 characters)
**When** the API validates the input
**Then** the request is rejected with a validation error

**Scenario:** User submits purchase with unsupported currency
**Given** I send a purchase ingestion request with a currency other than EUR (e.g. USD, GBP)
**When** the system applies the currency policy
**Then** an error is returned indicating the currency is not supported

**Scenario:** User attempts to ingest for a non-existent user
**Given** I send a purchase ingestion request where `user_id` matches my identity
  but the account no longer exists in the system
**When** the system validates user existence
**Then** an error is returned indicating user not found

**Scenario:** User attempts to ingest but their account is inactive
**Given** I send a purchase ingestion request where `user_id` matches my identity
  but my account is inactive
**When** the system validates user status
**Then** an error is returned indicating user is inactive

**Scenario:** User attempts to ingest for non-existent merchant
**Given** I send a purchase ingestion request with a merchant ID that does not exist in the system
**When** the system validates merchant existence
**Then** an error is returned indicating merchant not found

**Scenario:** User attempts to ingest for inactive merchant
**Given** I send a purchase ingestion request with a merchant ID that exists but is inactive
**When** the system validates merchant status
**Then** an error is returned indicating merchant is inactive

**Scenario:** User attempts to ingest when no active offer exists for the merchant
**Given** I send a purchase ingestion request for a merchant that has no active offer
**When** the system looks up a valid offer for the merchant
**Then** an error is returned indicating no offer is available for the merchant

**Scenario:** User attempts to ingest when the merchant's offer is inactive
**Given** I send a purchase ingestion request for a merchant whose offer exists but has `active = false`
**When** the system looks up a valid offer for the merchant
**Then** an error is returned indicating no offer is available for the merchant

**Scenario:** User attempts to ingest when the merchant's active offer is expired
**Given** I send a purchase ingestion request for a merchant whose offer has `active = true`
  but `end_date` is before today
**When** the system looks up a valid offer for the merchant
**Then** an error is returned indicating no offer is available for the merchant (offer out of date range)

**Scenario:** User attempts to ingest when the merchant's active offer has not started yet
**Given** I send a purchase ingestion request for a merchant whose offer has `active = true`
  but `start_date` is after today
**When** the system looks up a valid offer for the merchant
**Then** an error is returned indicating no offer is available for the merchant (offer out of date range)

---

## Use Cases

### Happy Path

User successfully ingests their own purchase

1. System receives purchase request with `external_id` and purchase details.
2. System enforces that `user_id` in the request matches the authenticated user — passes.
3. System checks uniqueness constraint for `external_id` — not found, proceed.
4. System validates user exists and is active.
5. System validates merchant exists and is active.
6. System resolves the active, date-valid offer for the merchant.
7. System calculates the cashback amount from the offer (fixed amount if set, otherwise `amount × percentage / 100`, rounded to 2 decimal places).
8. System creates purchase with status `pending`, associating the resolved offer and the calculated `cashback_amount`.
9. System atomically increases the user's wallet `pending_balance` by the cashback amount (creating the wallet row if it does not yet exist).
10. System commits the purchase and wallet update in a single DB transaction.
11. System returns new purchase info.

### Sad Paths

#### Purchase Ownership Violation (Forbidden)

1. System receives purchase request where `user_id` does not match the authenticated user.
2. System enforces ownership — IDs do not match.
3. System returns a 403 Forbidden error.

#### Duplicate Purchase (Conflict Response)

1. System receives purchase request with `external_id`.
2. System enforces ownership — passes (user is ingesting their own purchase).
3. System checks uniqueness constraint.
4. System finds an existing purchase with the same `external_id`.
5. System returns a conflict error with details of the previously ingested purchase.

#### Non-Existent User

1. System receives purchase request where `user_id` matches the authenticated user.
2. System enforces ownership — passes.
3. System checks uniqueness constraint for `external_id` — not found, proceed.
4. System validates user existence.
5. System finds user does not exist.
6. System returns error indicating user not found.

#### Inactive User

1. System receives purchase request for a user ID that exists but is inactive.
2. System enforces ownership — passes.
3. System checks uniqueness constraint for `external_id` — not found, proceed.
4. System validates user status.
5. System finds user is inactive.
6. System returns error indicating user is inactive.

#### Non-Existent Merchant

1. System receives purchase request for a non-existent merchant ID.
2. System enforces ownership — passes.
3. System checks uniqueness constraint for `external_id` — not found, proceed.
4. System validates user existence and status — passes.
5. System validates merchant existence.
6. System finds merchant does not exist.
7. System returns error indicating merchant not found.

#### Inactive Merchant

1. System receives purchase request for a merchant ID that exists but is inactive.
2. System enforces ownership — passes.
3. System checks uniqueness constraint for `external_id` — not found, proceed.
4. System validates user existence and status — passes.
5. System validates merchant status.
6. System finds merchant is inactive.
7. System returns error indicating merchant is inactive.

#### No Active Offer Available for Merchant

Covers three distinct root causes: no offer exists for merchant, offer is inactive,
or offer exists and is active but is outside its valid date range (expired or not yet started).

1. System receives purchase request.
2. System enforces ownership — passes.
3. System checks uniqueness constraint for `external_id` — not found, proceed.
4. System validates user existence and status — passes.
5. System validates merchant existence and status — passes.
6. System looks up an active, date-valid offer for the merchant.
7. System finds no qualifying offer.
8. System returns error indicating no offer is available for the merchant.

#### Invalid Purchase Data

1. System receives purchase request with missing or invalid fields.
2. API layer validates the request body with Pydantic.
3. System detects invalid data (e.g. missing `external_id`, negative amount, malformed UUID,
   or currency not exactly 3 characters).
4. System rejects the request with a validation error before any business logic executes.

#### Unsupported Currency

1. System receives purchase request with a currency other than EUR (e.g. `USD`, `GBP`).
2. System enforces ownership — passes.
3. System checks uniqueness constraint for `external_id` — not found, proceed.
4. System applies the currency policy.
5. System finds the currency is not in the supported set.
6. System returns an error indicating the currency is not supported.

## API Contract

See [Ingest purchase](../../design/api-contracts/purchases/ingest-purchase.md) for detailed API
specifications.
