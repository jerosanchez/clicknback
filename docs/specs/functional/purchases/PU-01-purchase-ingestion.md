# PU-01: Purchase Ingestion

IMPORTANT: This is a living document, specs are subject to change.

## User Story

_As an external system, I want to record user purchases through a webhook so that the platform can track transactions and calculate cashback._

---

## Constraints

### Request Constraints

- Purchase must include external unique identifier
- User and merchant must exist in the system
- Requests must be idempotent (same external_id returns same result)

### Data Constraints

- External ID must be unique per purchase origin
- Duplicate submissions with same external_id must return existing purchase, not create new one (idempotent operation)

---

## BDD Acceptance Criteria

**Scenario:** External system successfully ingests a new purchase
**Given** I send a `POST /api/v1/purchases/ingest` request with valid user, merchant, and unique external_id
**When** the external_id is not already in system
**Then** the API responds with `HTTP 201 Created` and returns the new purchase with status `pending`

**Scenario:** External system submits duplicate purchase (idempotent)
**Given** I send a `POST /api/v1/purchases/ingest` request with same external_id as previous request
**When** the system checks for existing purchase
**Then** the API responds with `HTTP 200 OK` and returns the existing purchase without creating a duplicate

**Scenario:** External system attempts to ingest for non-existent user
**Given** I send a `POST /api/v1/purchases/ingest` request with non-existent user ID
**When** the system validates user existence
**Then** the API responds with `HTTP 400 Bad Request` or `HTTP 404 Not Found`

**Scenario:** External system attempts to ingest for non-existent merchant
**Given** I send a `POST /api/v1/purchases/ingest` request with non-existent merchant ID
**When** the system validates merchant existence
**Then** the API responds with `HTTP 400 Bad Request` or `HTTP 404 Not Found`

---

## Use Cases

### Happy Path

External system successfully ingests a new purchase

1. System receives purchase with external_id and purchase details.
2. System checks uniqueness constraint for external_id.
3. System validates user exists.
4. System validates merchant exists.
5. System creates purchase with status `pending`.
6. System returns `HTTP 201 Created` with new purchase info.

### Sad Paths

#### Duplicate Purchase (Idempotent Behavior)

1. System receives purchase with external_id.
2. System checks uniqueness constraint.
3. System finds existing purchase with same external_id.
4. System returns `HTTP 200 OK` with existing purchase without creating duplicate.

#### Non-Existent User

1. System receives purchase request for non-existent user ID.
2. System checks uniqueness constraint.
3. System validates user exists.
4. System finds user does not exist.
5. System returns `HTTP 400 Bad Request` or `HTTP 404 Not Found`.

#### Non-Existent Merchant

1. System receives purchase request for non-existent merchant ID.
2. System checks uniqueness constraint.
3. System validates merchant exists.
4. System finds merchant does not exist.
5. System returns `HTTP 400 Bad Request` or `HTTP 404 Not Found`.

#### Invalid Purchase Data

1. System receives purchase with missing or invalid purchase amount.
2. System checks uniqueness constraint.
3. System validates purchase data.
4. System detects invalid data.
5. System returns `HTTP 400 Bad Request` with validation error.

## API Contract

See [Ingest purchase](../../design/api-contracts/purchases/ingest-purchase.md) for detailed API specifications.
