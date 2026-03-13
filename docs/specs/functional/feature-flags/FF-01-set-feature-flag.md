# FF-01: Set Feature Flag

IMPORTANT: This is a living document, specs are subject to change.

## User Story

_As an admin, I want to create or update a feature flag so that I can enable or disable a platform capability at runtime without redeploying the application._

---

## Domain Concepts

| Term | Description |
| --- | --- |
| **Flag key** | A unique string identifier for the feature, e.g. `purchase_confirmation_job`. Convention: `snake_case`, max 100 characters. |
| **Scope type** | `global` (applies platform-wide), `merchant` (applies to one merchant), or `user` (applies to one user). |
| **Scope ID** | UUID of the scoped entity; `null` when `scope_type` is `global`. |
| **Upsert semantics** | If a flag matching `(key, scope_type, scope_id)` already exists it is updated; otherwise a new record is created. |

---

## Constraints

### Authorization Constraints

- Only authenticated admin users can create or update feature flags.

### Input Constraints

- `key` must be non-empty, lowercase `snake_case`, and no longer than 100 characters.
- `scope_type` must be one of: `global`, `merchant`, `user`. Defaults to `global` when omitted.
- `scope_id` is required when `scope_type` is `merchant` or `user`, and must be a valid UUID.
- `scope_id` must be `null` (or omitted) when `scope_type` is `global`.

### Data Constraints

- Exactly one record per `(key, scope_type, scope_id)` triple is enforced via a database unique constraint.

---

## BDD Acceptance Criteria

**Scenario:** Admin sets a global flag
**Given** I am an authenticated admin
**When** I send a valid request to set flag `purchase_confirmation_job` with `scope_type: global` and `enabled: false`
**Then** the flag record is created (or updated) and the response contains `enabled: false`

**Scenario:** Admin sets a merchant-scoped flag
**Given** I am an authenticated admin
**When** I send a request to set flag `fraud_check` with `scope_type: merchant` and a valid `scope_id`
**Then** a scoped flag record is created and the response confirms the scope

**Scenario:** Merchant-scoped flag without scope_id
**Given** I am an authenticated admin
**When** I send a request with `scope_type: merchant` but no `scope_id`
**Then** the request is rejected with a `422` validation error

**Scenario:** Non-admin attempts to set a flag
**Given** I am authenticated as a regular user
**When** I send a set-flag request
**Then** the response is `403 Forbidden`

**Scenario:** Unauthenticated request
**Given** no JWT token is provided
**When** I send a set-flag request
**Then** the response is `401 Unauthorized`

---

## Use Cases

### Happy Path — Create global flag

1. Admin sends request with `key`, `enabled`, and optionally `description`.
2. System verifies admin role.
3. System validates inputs (key format, scope consistency).
4. System upserts the flag record.
5. System returns the full flag record.

### Happy Path — Update existing flag

1. Admin sends request for a key that already exists with the same scope.
2. System finds the existing record via `(key, scope_type, scope_id)`.
3. System updates `enabled` and/or `description`.
4. System returns the updated record.

### Sad Paths

#### Missing scope_id for non-global scope

1. Admin sends request with `scope_type: merchant` but omits `scope_id`.
2. System enforces scope validation policy.
3. System returns `422` with error code `FEATURE_FLAG_SCOPE_ID_REQUIRED`.

#### Non-admin or unauthenticated

1. Requester lacks admin role or a valid token.
2. System enforces authorization.
3. System returns `403 Forbidden` or `401 Unauthorized`.

## API Contract

See [Set feature flag](../../../design/api-contracts/feature-flags/set-feature-flag.md) for detailed API specifications.
