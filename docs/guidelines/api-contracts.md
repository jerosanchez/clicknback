# Writing API Contracts

This is the authoritative guide for writing API contract documents. It covers structure, content, validation techniques, HTTP semantics, and common pitfalls to avoid. Every endpoint in the system must have a corresponding API contract before implementation begins.

---

## Purpose

An API contract document specifies the **exact HTTP interface** for a feature. It describes:

- **The endpoint** — HTTP method, path, and parameters
- **The request** — what the client sends (body, headers, query params)
- **The response** — what the server returns (body, status codes)
- **All failure modes** — error codes, status codes, and error response shape

An API contract is **implementation-agnostic but technically precise** — it does not mention code, language, or internal architecture, but it *does* specify JSON fields, HTTP status codes, and headers. This is complementary to the **functional specification** (which describes business logic) and distinct from **code** (which implements it).

---

## One Contract Per Endpoint

An API contract covers **exactly one HTTP endpoint**. Not one domain area, not multiple HTTP methods on the same path.

**Correct:**

- "Set a Feature Flag" (PUT `/api/v1/feature-flags/{key}`) ✅
- "Delete a Feature Flag" (DELETE `/api/v1/feature-flags/{key}`) ✅
- "List Feature Flags" (GET `/api/v1/feature-flags`) ✅

**Incorrect:**

- "Feature Flag Management" ❌ (covers multiple endpoints)
- "Merchant Operations" ❌ (covers multiple methods/paths)

**Naming Convention:** `<verb>-<resource>.md`

- `<verb>` — HTTP operation in lowercase: `get`, `post`, `put`, `patch`, `delete`, `list` (use `list` instead of `get` for collection endpoints)
- `<resource>` — Kebab-case resource name (e.g., `feature-flag`, `merchant`, `offer`, `purchase`)

**Examples:**

- `set-feature-flag.md` (PUT request)
- `delete-feature-flag.md` (DELETE request)
- `list-feature-flags.md` (GET request for collection)
- `create-merchant.md` (POST request)
- `get-offer-details.md` (GET request for single resource)

---

## Mandatory Section Order

Every API contract must include these sections **in this exact order**:

### 1. Title and Endpoint Declaration

```markdown
# Operation Name

**Endpoint:** `METHOD /api/v1/path/{param}`
**Roles:** Admin | User | Public
```

**Operation Name:** A verb–noun phrase describing what the operation does (e.g., "Authenticate User", "Set Feature Flag", "List Merchants").

**Endpoint:** The HTTP method (GET, POST, PUT, PATCH, DELETE) followed by the full path with placeholders in `{curly-braces}`.

**Roles:** Who can call this endpoint? Comma-separated list of: `Admin`, `User`, `Public` (for unauthenticated), or `System` (for internal system calls only). If multiple roles are allowed, list them in order of least privilege first (Public → User → Admin).

---

### 2. Request Section

````markdown
## Request

**Path parameters:**

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `key` | string | ✅ | Feature flag key, e.g. `purchase_confirmation_job` |

**Query parameters:**

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `page` | integer | ❌ | Page number, starts at 1 (default: 1) |
| `page_size` | integer | ❌ | Items per page, max 100 (default: 20) |

**Body:**

```json
{
  "enabled": true,
  "scope_type": "merchant",
  "scope_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "description": "Optional description"
}
```

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `enabled` | boolean | ✅ | Whether the flag is active |
| `scope_type` | string | ❌ | `global` (default), `merchant`, or `user` |
| `scope_id` | UUID | ❌ | Required when `scope_type` is non-global |
| `description` | string | ❌ | Human-readable description, max 500 characters |

````

**Rules for path, query, and body parameters:**

- **Path parameters** – Always required. Never optional. Placed in `{curly_braces}` in the endpoint path.
- **Query parameters** – Optional unless marked with ✅. Used for filtering, pagination, sorting. Never embed secrets or sensitive data in query strings.
- **Body** – For POST, PUT, PATCH requests only. Format as a JSON block followed by a table describing each field. Use realistic but fictional UUIDs and timestamps.
- **Type annotations** – Be precise: `string`, `integer`, `boolean`, `array`, `object`, `UUID`, `decimal`, `datetime` (ISO 8601 format).
- **Descriptions** – Clarify format, constraints, and examples (e.g., "max 100 characters", "lowercase snake_case", "valid email").

**When a section is not needed:** Omit it entirely (e.g., no **Query parameters** section if the endpoint takes no query params, no **Body** section for GET requests).

---

### 3. Success Response

````markdown
## Success Response

**Status:** `200 OK`

```json
{
  "id": "7f3a1234-bc56-7890-def0-1234567890ab",
  "key": "purchase_confirmation_job",
  "enabled": true,
  "scope_type": "merchant",
  "scope_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "description": "Disable for specific merchant during migration",
  "created_at": "2025-01-15T12:00:00Z",
  "updated_at": "2025-01-15T14:30:00Z"
}
```

````

**Rules:**

- Always include the HTTP status code (e.g., `200 OK`, `201 Created`, `204 No Content`).
- Use the correct status code for the operation:
  - `200 OK` – Read operation or successful update (PATCH, PUT on existing resource)
  - `201 Created` – Successful creation (POST)
  - `202 Accepted` – Async operation accepted for processing (job queued, etc.)
  - `204 No Content` – Successful deletion or operation with no response body
- Use realistic but fictional data: valid UUIDs (not `xxx`), real timestamps (ISO 8601), valid enum values.
- Include all fields the response schema will contain, including computed/derived fields.
- For list/paginated responses:

````markdown
**Status:** `200 OK`

```json
{
  "items": [
    { "id": "...", "name": "..." },
    { "id": "...", "name": "..." }
  ],
  "total": 42,
  "page": 1,
  "page_size": 20
}
```

````

---

### 4. Failure Responses

````markdown
## Failure Responses

### 401 Unauthorized — Missing or invalid token

```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Authentication required.",
    "details": {}
  }
}
```

### 403 Forbidden — Caller is not an admin

```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "Admin role required.",
    "details": {}
  }
}
```

### 422 Unprocessable Entity — scope_id required for non-global scope

```json
{
  "error": {
    "code": "FEATURE_FLAG_SCOPE_ID_REQUIRED",
    "message": "scope_id is required when scope_type is 'merchant' or 'user'.",
    "details": {
      "scope_type": "merchant"
    }
  }
}
```

### 400 Bad Request — Invalid request format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request body does not match schema.",
    "details": {}
  }
}
```

### 404 Not Found — Resource does not exist

```json
{
  "error": {
    "code": "MERCHANT_NOT_FOUND",
    "message": "Merchant with ID 'abc123' not found.",
    "details": {
      "merchant_id": "abc123"
    }
  }
}
```

### 409 Conflict — Resource violates a business rule or constraint

```json
{
  "error": {
    "code": "PURCHASE_ALREADY_EXISTS",
    "message": "A purchase with external_id 'ext-123' already exists.",
    "details": {
      "external_id": "ext-123",
      "existing_purchase_id": "uuid-of-existing-purchase"
    }
  }
}
```

### 429 Too Many Requests — Rate limit exceeded

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests. Please retry after 60 seconds.",
    "details": {
      "retry_after_seconds": 60
    }
  }
}
```

### 500 Internal Server Error — Unexpected server error

```json
{
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "An unexpected error occurred. Please try again or contact support.",
    "details": {}
  }
}
```

````

**Rules for failure responses:**

- Every failure mode the endpoint can return must have its own subsection.
- Use the subsection header format: `### <HTTP_CODE> – <Error Code or Short Reason>`
- Mandatory failures for all endpoints:
  - `401 Unauthorized` — if the endpoint requires authentication
  - `403 Forbidden` — if the endpoint has role-based access control (admin-only, etc.)
  - `422 Unprocessable Entity` — if the request has validation errors (invalid field values, malformed JSON, missing required fields)
  - `500 Internal Server Error` — always list this as the catch-all for unexpected errors
- Always include an `error_code` string in the `error.code` field (e.g., `MERCHANT_NOT_FOUND`, not a generic `NOT_FOUND`).
- Include a human-readable `message` in `error.message`.
- Use `details` to provide context about the failure (e.g., which field failed validation, what was expected, IDs involved).
- Realistic examples: use actual UUIDs, actual error codes from the codebase, realistic field values.

---

### 5. Example: Complete Contract

Here's a realistic example covering all sections:

````markdown
# Set Feature Flag

**Endpoint:** `PUT /api/v1/feature-flags/{key}`
**Roles:** Admin

---

## Request

**Path parameters:**

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `key` | string | ✅ | The unique feature flag key to create or update |

**Body:**

```json
{
  "enabled": false,
  "scope_type": "global",
  "description": "Temporarily disable purchase confirmation background job"
}
```

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `enabled` | boolean | ✅ | Whether the flag is active |
| `scope_type` | string | ❌ | `global` (default), `merchant`, or `user` |
| `scope_id` | UUID | ❌ | Required when `scope_type` is `merchant` or `user` |
| `description` | string | ❌ | Human-readable note, max 500 characters |

---

## Success Response

**Status:** `200 OK`

```json
{
  "id": "7f3a1234-bc56-7890-def0-1234567890ab",
  "key": "purchase_confirmation_job",
  "enabled": false,
  "scope_type": "global",
  "scope_id": null,
  "description": "Temporarily disable purchase confirmation background job",
  "created_at": "2025-01-10T08:00:00Z",
  "updated_at": "2025-01-15T14:30:00Z"
}
```

---

## Failure Responses

### 401 Unauthorized — Missing or invalid token

```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Authentication required.",
    "details": {}
  }
}
```

### 403 Forbidden — Caller is not an admin

```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "Admin role required.",
    "details": {}
  }
}
```

### 422 Unprocessable Entity — scope_id is required for non-global scope

```json
{
  "error": {
    "code": "FEATURE_FLAG_SCOPE_ID_REQUIRED",
    "message": "scope_id is required when scope_type is 'merchant' or 'user'.",
    "details": {
      "scope_type": "merchant"
    }
  }
}
```

### 422 Unprocessable Entity — Invalid scope_type

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid value for scope_type. Must be one of: global, merchant, user.",
    "details": {
      "field": "scope_type",
      "value": "store",
      "allowed_values": ["global", "merchant", "user"]
    }
  }
}
```

### 500 Internal Server Error

```json
{
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "An unexpected error occurred. Please try again or contact support.",
    "details": {}
  }
}
```

````

---

## HTTP Status Code Reference

Use this table to choose the correct status code for each scenario:

| Code | Meaning | When to Use |
| --- | --- | --- |
| `200` | OK | Successful read, update, or state-change with a response body |
| `201` | Created | Successful creation (POST) |
| `202` | Accepted | Async operation queued (job submitted but not yet complete) |
| `204` | No Content | Successful operation with **no** response body (e.g., DELETE, or a state-change that should return no body) |
| `400` | Bad Request | Malformed request (invalid JSON, bad format) — use `422` for semantic validation errors |
| `401` | Unauthorized | Missing or invalid authentication token |
| `403` | Forbidden | Authenticated but lacks permission (role-based access control) |
| `404` | Not Found | Resource does not exist |
| `409` | Conflict | Business rule violation (e.g., duplicate key, precondition failed, state conflict) |
| `422` | Unprocessable Entity | Semantic validation error (field value out of range, invalid enum, missing required field) |
| `429` | Too Many Requests | Rate limit exceeded |
| `500` | Internal Server Error | Unexpected server error |

---

## Common Patterns

### Paginated List Response

````markdown
## Success Response

**Status:** `200 OK`

```json
{
  "items": [
    {
      "id": "f1a2b3c4-d5e6-7890-abcd-ef1234567890",
      "name": "Purchase Confirmation Job",
      "enabled": true
    },
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "name": "Fraud Detection",
      "enabled": false
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 20
}
```

````

**Rules:**

- `items` — array of resource objects
- `total` — total count of all items matching the filter (not just this page)
- `page` — current page number (1-indexed)
- `page_size` — items returned in this page

### Filter and Sort Query Parameters

```markdown
## Request

**Query parameters:**

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `status` | string | ❌ | Filter by status: `active`, `inactive`, `all` (default: `all`) |
| `merchant_id` | UUID | ❌ | Filter by merchant ID (e.g. `a1b2c3d4-e5f6-7890-abcd-ef1234567890`) |
| `sort_by` | string | ❌ | Sort field: `created_at`, `name` (default: `created_at`) |
| `sort_order` | string | ❌ | Sort direction: `asc`, `desc` (default: `desc`) |
| `page` | integer | ❌ | Page number, starts at 1 (default: 1) |
| `page_size` | integer | ❌ | Items per page, max 100 (default: 20) |
```

### Error Details Context

Include relevant IDs and context in the `details` object:

```json
{
  "error": {
    "code": "USER_NOT_FOUND",
    "message": "User 'abc123' does not exist.",
    "details": {
      "user_id": "abc123",
      "searched_in_active_users": true
    }
  }
}
```

---

## Validation Checklist

Before committing an API contract, verify:

- [ ] **One endpoint per document** — Does the contract describe exactly one HTTP method on one path?
- [ ] **Naming follows convention** — Is the filename `<verb>-<resource>.md`?
- [ ] **All mandatory sections present** — Are Title & Endpoint, Request, Success Response, and Failure Responses all present in order?
- [ ] **Endpoint declaration is correct** — Is the HTTP method uppercase (GET, POST, PUT, DELETE, PATCH)? Is the path `/api/v1/...`? Are path parameters in `{curly_braces}`?
- [ ] **Roles are specified** — Are the allowed roles (Admin, User, Public, System) listed?
- [ ] **Request is complete** — Path params, query params, and body (if applicable) are all documented with tables and realistic examples?
- [ ] **Success response has correct status** — Is the HTTP code appropriate for the operation (200 for read/update, 201 for create, 204 for delete, 202 for async)?
- [ ] **Success response is realistic** — Does the JSON block include all response fields with realistic (but fictional) data?
- [ ] **Failure responses are comprehensive** — Are 401, 403, 422, and 500 listed (if applicable)? Are error-specific failures (404, 409, etc.) included?
- [ ] **Error codes are specific** — Is each error code domain-specific (e.g., `MERCHANT_NOT_FOUND`, not generic `NOT_FOUND`)? Do they match the codebase error codes?
- [ ] **Details context is useful** — Do the `details` objects in error responses include relevant IDs and context?
- [ ] **Descriptions are clear** — Are field descriptions precise about format, constraints, examples, and edge cases?
- [ ] **No implementation details** — Does the contract avoid mentioning: code files, class names, database tables, internal validation libraries, or technology stack?
- [ ] **Spelling and grammar** — Is the text correct, readable, and consistent?

---

## Common Mistakes

### 1. **Generic Error Codes**

**Wrong:**

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Resource not found."
  }
}
```

**Correct:**

```json
{
  "error": {
    "code": "MERCHANT_NOT_FOUND",
    "message": "Merchant with ID 'abc123' not found.",
    "details": { "merchant_id": "abc123" }
  }
}
```

---

### 2. **Vague Field Descriptions**

**Wrong:**
> `enabled` — boolean flag

**Correct:**
> `enabled` — Whether the feature flag is active (true) or disabled (false). Default: true.

---

### 3. **Missing Failure Modes**

**Wrong:** The contract only lists success and auth failures, but omits business-rule violations.

**Correct:** List all HTTP codes the endpoint returns:

- 401 if unauthenticated
- 403 if unauthorized
- 422 for validation errors
- 404 if a dependency doesn't exist
- 409 for business-rule violations (duplicates, conflicts)
- 500 for unexpected errors

---

### 4. **Inconsistent with Functional Spec**

**Wrong:** The functional spec says "error code MERCHANT_INACTIVE", but the API contract lists only 404.

**Correct:** Every scenario and error code mentioned in the spec has a corresponding response in the contract.

---

### 5. **Unrealistic Example Data**

**Wrong:**

```json
{
  "id": "xxx",
  "created_at": "2099-01-01T00:00:00Z",
  "amount": "999.99"
}
```

**Correct:**

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "created_at": "2025-01-15T14:30:00Z",
  "amount": "45.67"
}
```

---

### 6. **Confusing Required vs. Optional**

**Wrong:** No clear indication of which fields are required.

**Correct:** Use a table with a "Required" column marked with ✅ (required) or ❌ (optional):

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `key` | string | ✅ | The feature flag key |
| `description` | string | ❌ | Optional note |

---

## Examples

Well-formed API contracts serve as templates for future work. See these examples in the repository:

- [Set Feature Flag](../design/api-contracts/feature-flags/set-feature-flag.md) — PUT request, success and failure responses
- [List Feature Flags](../design/api-contracts/feature-flags/list-feature-flags.md) — GET with pagination and filters
- [Create Merchant](../design/api-contracts/merchants/create-merchant.md) — POST request, 201 Created response
- [Get Offer Details](../design/api-contracts/offers/get-offer-details.md) — GET single resource, 404 failure
- [Ingest Purchase](../design/api-contracts/purchases/ingest-purchase.md) — POST request, idempotency, 409 Conflict

Study them. Use them as templates.

---

## Writing Checklist

Use this checklist as you draft:

1. **Decide the operation** — What is the HTTP method and path? Who can call it?
2. **List request parameters** — Path params? Query params? Request body?
3. **Design the success response** — What data is returned? What status code? Realistic example?
4. **Enumerate failure modes** — What can go wrong? What error codes? What details?
5. **Fill in descriptions** — Clarify field meanings, constraints, examples.
6. **Create realistic data** — Use valid UUIDs, timestamps, enum values.
7. **Review against checklist** — Fix any gaps.
8. **Cross-check with functional spec** — Does every scenario and error code have a corresponding response?

---

## Next Steps

After writing an API contract:

1. **Verify consistency with functional spec** — See `build-feature.prompt.md` Step 0b for the cross-check process.
2. **Code reference** — Pass the contract to developers implementing the endpoint. They will follow it to the letter.
3. **Manual testing** — Use the contract to write `.http` files for manual API testing (see `docs/guidelines/http-requests-file.md`).
4. **Documentation** — Reference the contract in the functional spec's "API Contract" section.

---

## Version Control & Maintenance

- **API Contracts are living documents** — When business rules change or a new error case is discovered, update the contract and functional spec together.
- **Never change a published endpoint without versioning** — Existing clients depend on the current contract. Introduce `/api/v2/` paths for breaking changes.
- **Keep examples realistic** — Periodically review example data to ensure it reflects actual domain values (e.g., actual merchant names, realistic amounts).
