# FF-04: Evaluate Feature Flag

IMPORTANT: This is a living document, specs are subject to change.

## User Story

_As a platform component (background job, event handler, or API route), I want to evaluate whether a feature flag is currently enabled for a given scope so that I can gate behaviour without duplicating the resolution logic in every consumer._

---

## Domain Concepts

| Term | Description |
| --- | --- |
| **Resolution order** | When evaluating, the system checks for a matching scoped record first (`key + scope_type + scope_id`), then falls back to the global record (`key + scope_type: global`), and finally returns `true` if neither record exists. |
| **Fail-open default** | The absence of a flag record is not an error — it means "enabled". This preserves backward compatibility when a flag is deleted or has never been set. |
| **Consumer client** | The per-domain client abstraction through which a consuming module queries flag state. Each consuming module owns a `clients/feature_flags.py` in its own `clients/` package; the initial in-process implementation calls `FeatureFlagService` directly; a future remote implementation calls this evaluate endpoint, enabling `feature_flags` to be extracted to a microservice with changes confined to that one file. |

---

## Constraints

### Authorization Constraints

- Only authenticated admin users can call the evaluate endpoint in **v1**.
- When the feature flag system is extracted to a standalone microservice, this endpoint will accept machine tokens (service-to-service auth). The admin-only restriction is a v1 simplification driven by the absence of machine-token infrastructure.

### Input Constraints

- `key` is a required path parameter.
- `scope_type` must be `global`, `merchant`, or `user` when provided; defaults to `global` when omitted.
- `scope_id` is required when `scope_type` is `merchant` or `user`, and must be a valid UUID.
- `scope_id` must be absent (or `null`) when `scope_type` is `global`.

### Resolution Constraints

- The resolution algorithm must be consistent with the priority defined above; consumers must not implement their own resolution logic.
- Returning the fail-open default (`true`) when no record exists must not be treated as an error by the caller or logged as a warning.

---

## BDD Acceptance Criteria

**Scenario:** Global flag is disabled
**Given** a flag `purchase_confirmation_job` with `scope_type: global` and `enabled: false` exists
**When** an authenticated admin evaluates the flag with no scope filters
**Then** the response is `200 OK` with `{ "key": "purchase_confirmation_job", "enabled": false }`

**Scenario:** Merchant-scoped flag overrides a disabled global flag
**Given** a global flag `purchase_confirmation_job` is `enabled: false`
**And** a merchant-scoped flag for the same key with `scope_id: <merchant_id>` is `enabled: true`
**When** an authenticated admin evaluates the flag with `scope_type: merchant` and that `scope_id`
**Then** the response is `200 OK` with `enabled: true`

**Scenario:** Merchant-scoped flag absent — falls back to global
**Given** a global flag `purchase_confirmation_job` is `enabled: false`
**And** no merchant-scoped flag exists for the same key
**When** an authenticated admin evaluates the flag with `scope_type: merchant` and any `scope_id`
**Then** the response is `200 OK` with `enabled: false` (global fallback)

**Scenario:** No flag record exists — fail-open default
**Given** no flag record of any scope exists for key `new_cashback_rules`
**When** an authenticated admin evaluates the flag
**Then** the response is `200 OK` with `{ "key": "new_cashback_rules", "enabled": true }`

**Scenario:** Non-admin attempt
**Given** I am authenticated as a regular user
**When** I send an evaluate request
**Then** the response is `403 Forbidden`

**Scenario:** Unauthenticated request
**Given** no JWT token is provided
**When** I send an evaluate request
**Then** the response is `401 Unauthorized`

---

## Use Cases

### Happy Path — Evaluate with resolution fallback

1. Admin (or service-to-service caller) sends a `GET` request with `key`, optional `scope_type`, optional `scope_id`.
2. System verifies credentials.
3. System executes the resolution algorithm in order:
   - If `scope_type` is not `global`: query for the exact scoped record `(key, scope_type, scope_id)`. Return its `enabled` if found.
   - Query for the global record `(key, global, null)`. Return its `enabled` if found.
   - No record found — return `true` (fail-open default).
4. System returns `{ "key": "...", "enabled": true | false }`.

### Sad Paths

#### scope_id missing for non-global scope

1. Caller sends `scope_type: merchant` but omits `scope_id`.
2. System enforces scope validation.
3. System returns `422` with error code `FEATURE_FLAG_SCOPE_ID_REQUIRED`.

#### Non-admin or unauthenticated

1. Requester lacks admin role or a valid token.
2. System enforces authorization.
3. System returns `403 Forbidden` or `401 Unauthorized`.

## API Contract

See [Evaluate feature flag](../../../design/api-contracts/feature-flags/evaluate-feature-flag.md) for detailed API specifications.
