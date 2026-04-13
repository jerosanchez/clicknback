# M-03: Merchants Listing

IMPORTANT: This is a living document, specs are subject to change.

## User Story

_As an admin, I want to list all merchants with optional filters so that I can monitor and manage merchant records._

---

## Domain Concepts

| Term | Description |
| --- | --- |
| **Merchant record** | A single merchant entity with `id`, `name`, `active` status, and metadata. |
| **Filter** | Optional query parameters that narrow the result set. |

---

## Constraints

### Authorization Constraints

- Only authenticated admin users can list merchants.

### Filter Constraints

- Supported filter parameters: `active` (boolean).
- Filters are applied with `AND` semantics; providing no filters returns all records.

### Response Constraints

- An empty result set is valid and returns `{ "data": [], "pagination": { "offset": 0, "limit": 10, "total": 0 } }`.
- Results are paginated; `offset` (default: 0) and `limit` (default: 10, max: 100) control the page window.

---

## BDD Acceptance Criteria

**Scenario:** Admin lists all merchants
**Given** several merchants exist in the system
**When** an authenticated admin sends a list request with no filters
**Then** all merchant records are returned with their full details

**Scenario:** Admin filters by active status
**Given** merchants exist with both active and inactive statuses
**When** an authenticated admin sends a list request with `active=true`
**Then** only active merchant records are returned

**Scenario:** No merchants match the filter
**Given** no merchants match the provided filters
**When** an authenticated admin sends a filtered list request
**Then** the response is `200 OK` with `{ "data": [], "pagination": { "offset": 0, "limit": 10, "total": 0 } }`

**Scenario:** Non-admin attempts to list merchants
**Given** I am authenticated as a regular user
**When** I send a list-merchants request
**Then** the response is `403 Forbidden`

**Scenario:** Unauthenticated request
**Given** no JWT token is provided
**When** I send a list-merchants request
**Then** the response is `401 Unauthorized`

---

## Use Cases

### Happy Path — List all merchants

1. Admin sends a `GET` request with no query parameters.
2. System verifies admin role.
3. System queries all merchant records.
4. System returns `{ "data": [...], "pagination": { "offset": 0, "limit": 10, "total": N } }`.

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

See [List merchants](../../design/api-contracts/merchants/list-merchants.md) for detailed API specifications.
