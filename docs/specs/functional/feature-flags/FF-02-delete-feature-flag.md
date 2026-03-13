# FF-02: Delete Feature Flag

IMPORTANT: This is a living document, specs are subject to change.

## User Story

_As an admin, I want to delete a feature flag so that I can permanently remove an override that is no longer needed and restore the default behaviour for that feature._

---

## Domain Concepts

| Term | Description |
| --- | --- |
| **Flag key** | A unique string identifier for the feature, e.g. `purchase_confirmation_job`. |
| **Scope type** | `global`, `merchant`, or `user`. Required to identify the exact flag record to delete. |
| **Scope ID** | UUID of the scoped entity; `null` for `global` flags. Required when `scope_type` is `merchant` or `user`. |
| **Default behaviour** | When a flag record is deleted, the system reverts to the built-in default (fail-open: enabled). |

---

## Constraints

### Authorization Constraints

- Only authenticated admin users can delete feature flags.

### Input Constraints

- `key` is a required path parameter.
- `scope_type` is a required query parameter; must be `global`, `merchant`, or `user`.
- `scope_id` is required when `scope_type` is `merchant` or `user`, and must be a valid UUID.
- `scope_id` must be absent (or `null`) when `scope_type` is `global`.

### Behavior Constraints

- Deleting a flag that does not exist returns `404 Not Found`; the operation is not silently ignored.
- Only the exact `(key, scope_type, scope_id)` record is removed; other scoped variants of the same key are unaffected.

---

## BDD Acceptance Criteria

**Scenario:** Admin deletes an existing global flag
**Given** a flag `purchase_confirmation_job` with `scope_type: global` exists
**When** an authenticated admin sends a delete request for that flag
**Then** the flag is removed and the response is `204 No Content`

**Scenario:** Admin deletes a merchant-scoped flag
**Given** a flag `fraud_check` with `scope_type: merchant` and a specific `scope_id` exists
**When** an authenticated admin sends a delete request for that exact flag
**Then** only that scoped record is removed; other scopes remain intact

**Scenario:** Flag not found
**Given** no flag matching `(key, scope_type, scope_id)` exists
**When** an authenticated admin sends a delete request
**Then** the response is `404 Not Found` with code `FEATURE_FLAG_NOT_FOUND`

**Scenario:** Non-admin attempts to delete a flag
**Given** I am authenticated as a regular user
**When** I send a delete-flag request
**Then** the response is `403 Forbidden`

**Scenario:** Unauthenticated request
**Given** no JWT token is provided
**When** I send a delete-flag request
**Then** the response is `401 Unauthorized`

---

## Use Cases

### Happy Path

1. Admin sends a `DELETE` request with the flag `key`, `scope_type`, and (if applicable) `scope_id`.
2. System verifies admin role.
3. System validates scope consistency inputs.
4. System locates the exact `(key, scope_type, scope_id)` record.
5. System deletes the record.
6. System returns `204 No Content`.

### Sad Paths

#### Flag not found

1. Admin sends a delete request for a `(key, scope_type, scope_id)` that does not exist.
2. System queries for the record and finds nothing.
3. System returns `404 Not Found` with error code `FEATURE_FLAG_NOT_FOUND`.

#### Missing scope_id for non-global scope

1. Admin sends `scope_type: merchant` but omits `scope_id`.
2. System enforces scope validation policy.
3. System returns `422` with error code `FEATURE_FLAG_SCOPE_ID_REQUIRED`.

#### Non-admin or unauthenticated

1. Requester lacks admin role or a valid token.
2. System enforces authorization.
3. System returns `403 Forbidden` or `401 Unauthorized`.

## API Contract

See [Delete feature flag](../../../design/api-contracts/feature-flags/delete-feature-flag.md) for detailed API specifications.
