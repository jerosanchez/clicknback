# FF-03: List Feature Flags

IMPORTANT: This is a living document, specs are subject to change.

## User Story

_As an admin, I want to list all feature flags with optional filters so that I can inspect which features are enabled or disabled, and how they are scoped across the platform._

---

## Domain Concepts

| Term | Description |
| --- | --- |
| **Flag record** | A single `(key, scope_type, scope_id, enabled, description)` entry in the `feature_flags` table. |
| **Scope variant** | Multiple records can share the same `key` but differ by `scope_type`/`scope_id`, e.g. a global default plus merchant overrides. |
| **Filter** | Optional query parameters that narrow the result set. |

---

## Constraints

### Authorization Constraints

- Only authenticated admin users can list feature flags.

### Filter Constraints

- Supported filter parameters: `key` (exact match), `scope_type`, `scope_id` (UUID).
- Filters are applied with `AND` semantics; providing no filters returns all records.
- `scope_id` without `scope_type` is accepted; the system filters by `scope_id` across all scope types.

### Response Constraints

- An empty result set is valid and returns `{ "items": [], "total": 0 }`.
- Results are not paginated in version 1; all matching records are returned.

---

## BDD Acceptance Criteria

**Scenario:** Admin lists all flags
**Given** several feature flags exist across different scopes
**When** an authenticated admin sends a list request with no filters
**Then** all flag records are returned with their full details

**Scenario:** Admin filters by key
**Given** flags exist with different keys
**When** an authenticated admin sends a list request with `key=purchase_confirmation_job`
**Then** only records with that exact key are returned

**Scenario:** Admin filters by scope type
**Given** flags exist with `global`, `merchant`, and `user` scope types
**When** an authenticated admin sends a list request with `scope_type=merchant`
**Then** only merchant-scoped records are returned

**Scenario:** No flags match the filter
**Given** no flags match the provided filters
**When** an authenticated admin sends a filtered list request
**Then** the response is `200 OK` with `{ "items": [], "total": 0 }`

**Scenario:** Non-admin attempts to list flags
**Given** I am authenticated as a regular user
**When** I send a list-flags request
**Then** the response is `403 Forbidden`

**Scenario:** Unauthenticated request
**Given** no JWT token is provided
**When** I send a list-flags request
**Then** the response is `401 Unauthorized`

---

## Use Cases

### Happy Path — List all flags

1. Admin sends a `GET` request with no query parameters.
2. System verifies admin role.
3. System queries all flag records.
4. System returns `{ "items": [...], "total": N }`.

### Happy Path — Filtered list

1. Admin sends a `GET` request with one or more query filters.
2. System verifies admin role.
3. System applies filters with `AND` semantics.
4. System returns only the matching records.

### Sad Paths

#### Non-admin or unauthenticated

1. Requester lacks admin role or a valid token.
2. System enforces authorization.
3. System returns `403 Forbidden` or `401 Unauthorized`.

## API Contract

See [List feature flags](../../../design/api-contracts/feature-flags/list-feature-flags.md) for detailed API specifications.
