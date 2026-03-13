# HTTP Request Files — Authoring Guidelines

This document describes the conventions, structure, and coverage expectations for the `.http` files that live under `http/` at the project root. These files serve as lightweight smoke tests and living API documentation that any developer or AI agent can run directly from VS Code (REST Client extension) or any tool that supports the RFC 7230 HTTP request format.

---

## 1. Location and naming

```text
http/
  <module>/
    <verb>-<resource>.http   ← one file per endpoint (or closely related group)
```

- One file per endpoint. If a single resource has several distinct operations
  (create, list, get-details, set-status), each gets its own file.
- File names follow the pattern `<verb>-<resource>.http`, all lowercase with
  hyphens: `create-merchant.http`, `list-offers.http`, `get-purchase-details.http`.
- Module directories mirror the domain modules under `app/` (e.g., `http/auth/`,
  `http/users/`, `http/merchants/`).

---

## 2. File header

Every file starts with a comment block that documents the file at a glance:

```http
# <Module> – <Short endpoint title>
# Smoke tests for <HTTP verb> <path pattern>.
#
# One-paragraph description of what the endpoint does, who can call it,
# and any preconditions (auth roles, seed data, business rules).
#
# Relevant seed data (IDs, emails, states) should be listed here so the
# reader knows exactly which rows in seeds/all.sql are exercised.
```

Keep the header concise — it should be skimmable in under 30 seconds.

---

## 3. Variable declarations

Immediately after the header, declare all variables the requests in this file will reference. Variables are declared with `@name = value` and referenced as `{{name}}`.

```http
@baseUrl = http://localhost:8001/api/v1          # always first

# Resource IDs — use real UUIDs from seeds/all.sql
@merchantId = a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d

# Auth tokens — paste fresh values from the helper login requests below.
# The placeholder values here are EXPIRED local-dev tokens from seed data;
# they are never real production credentials.
@adminToken = Bearer <expired-placeholder>
@userToken  = Bearer <expired-placeholder>
```

**Rules:**

- `@baseUrl` is always the first variable, set to `http://localhost:8001/api/v1` (the local dev server). Never hardcode this value inside request lines.
- Token variables (`@adminToken`, `@userToken`) are included as expired placeholder JWTs sourced from local seed data. This lets a developer paste in a fresh token without hunting for the right variable name.
  **Never commit real tokens, API keys, or production credentials.**
- Resource ID variables (`@offerId`, `@merchantId`, etc.) should use real IDs from `seeds/all.sql` and include a short comment identifying the seed row.
- Declare a variable for every value that appears in more than one request in the file. Single-use literals can stay inline.

---

## 4. Auth helper requests

For any file whose requests require authentication, place **one or more helper login requests directly below the variable declarations**, before the feature requests. These helpers let the developer obtain a fresh token in a single click and paste it into the variable block above.

```http
### Helper – obtain a fresh admin token (carol)
# Returns access_token — paste as "Bearer <token>" into @adminToken above.
POST {{baseUrl}}/auth/login
Content-Type: application/json

{
  "email": "carol@clicknback.com",
  "password": "Str0ng!Pass"
}

### Helper – obtain a fresh user token (alice)
# Returns access_token — paste as "Bearer <token>" into @userToken above.
POST {{baseUrl}}/auth/login
Content-Type: application/json

{
  "email": "alice@clicknback.com",
  "password": "Str0ng!Pass"
}
```

**Rules:**

- Helpers always use seed user credentials (`seeds/all.sql`). Never use production or staging credentials.
- Use role-appropriate helpers: include helpers only for roles that are actually exercised in the file (admin for admin-only endpoints, user for user-facing endpoints, both for endpoints with role-differentiated behaviour).
- Label each helper clearly: `### Helper – obtain a fresh <role> token (<seed username>)`.
- Add a comment on the next line telling the reader exactly where to paste the result: `# Returns access_token — paste as "Bearer <token>" into @<varname> above.`

---

## 5. Request block structure

Each request is a `###`-separated block. The separator line is the title and must follow a consistent format:

```markdown
### <HTTP status code> – <Happy/Sad path label>: <brief description>
```

Examples:

```markdown
### 201 – Happy path: create a new active merchant (admin)
### 403 – Sad path: authenticated as a non-admin user
### 422 – Sad path: password missing uppercase letter
### Helper – obtain a fresh admin token (carol)
```

Immediately below the separator title, add a `#` comment line (or a short multi-line comment block) that explains:

- **What scenario this tests** and why it matters
- **What the expected response is** (status code + error code if applicable)
- **Any precondition or seed data dependency** that is not obvious from the request body (e.g., "alice is owner of this purchase", "Shoply has an active offer")

```http
### 409 – Sad path: duplicate external_id
# Re-submitting txn_smoke_001 after it was already ingested.
# Expects: 409 Conflict with DUPLICATE_PURCHASE error code.
POST {{baseUrl}}/purchases
Authorization: {{userToken}}
Content-Type: application/json

{
  "external_id": "txn_smoke_001",
  ...
}
```

---

## 6. Coverage checklist

Every `.http` file should cover **all distinct HTTP responses the endpoint can return**. Walk through the following checklist when writing a new file:

### Happy paths (cover all)

- [ ] Nominal request with the minimum required fields — verifies 200/201 response shape.
- [ ] Request exercising optional fields / filters (if any).
- [ ] Pagination boundary — first page, non-default `page_size`, page beyond total (empty list), and the minimum/maximum `page_size` for list endpoints.
- [ ] Each meaningful filter combination for list endpoints (single filter, combined filters, filter yielding zero results).
- [ ] Round-trip for state-toggling endpoints: deactivate → activate (or vice versa), always leaving the system in its original seeded state.

### Auth failures (always include)

- [ ] **401** – no `Authorization` header (auth middleware rejects before the handler).
- [ ] **403** – authenticated with the wrong role (e.g., user calls an admin-only endpoint). Note: some implementations return 401 for RBAC failures for security reasons — match the actual endpoint behaviour.

### Validation failures (Pydantic / schema layer)

- [ ] **422** – each required field omitted individually (one request per field).
- [ ] **422** – each field with a domain constraint violated (negative amount, out-of-range percentage, malformed UUID, invalid enum value, etc.).
- [ ] **422** – cross-field constraint violated (e.g., `end_date` before `start_date`).
- [ ] **422** – pagination bounds violated (`page=0`, `page_size` above max).

### Business rule failures (domain / service layer)

- [ ] **400** or **409** – domain-specific rejections (duplicate key, entity in wrong state, policy violation). Cover each distinct error code introduced by the feature.
- [ ] **404** – resource not found (use the all-zero UUID
  `00000000-0000-0000-0000-000000000000` as a guaranteed nonexistent row).

### Ordering

Place requests in this order within the file:

1. Helper login requests
2. Happy paths (most important scenario first)
3. Sad paths — ordered from least specific to most specific: 401 → 403 → 422 (validation) → 400/409 (business rules) → 404

---

## 7. Descriptions per request

Every `###` block that is not a "Helper" must include at least one comment line below the title. The comment should answer:

1. **What is being tested?** (the scenario in plain English)
2. **What is the expected outcome?** (status code + error code where applicable)
3. **Why does this case exist?** (if not obvious from the title)

For happy paths, also note any seed data or state the request depends on:

```http
### 200 – Happy path: admin views an inactive offer (admin bypass)
# Admin can retrieve offers with status=inactive that regular users cannot see.
# Uses @inactiveOfferId (b2c3d4e5-...) which is seeded with status=inactive.
GET {{baseUrl}}/offers/{{inactiveOfferId}}
Authorization: {{adminToken}}
```

For sad paths, name the specific error code when one is defined in `errors.py`:

```http
### 409 – Sad path: duplicate external_id
# Re-submitting txn_smoke_001 after it was already ingested.
# Expects: 409 Conflict with DUPLICATE_PURCHASE error code.
```

---

## 8. Token and credential hygiene

- **Never commit real tokens.** The `@adminToken` / `@userToken` variables must always hold expired local-dev placeholder values taken from seed data (`seeds/all.sql`). Their only purpose is to preserve the variable names so the developer knows what to paste after running a helper login request.
- **Never commit production, staging, or CI passwords.** The seed passwords (`Str0ng!Pass`) are safe because they are used only against the local dev database populated by `seeds/all.sql`.
- Local dev tokens are short-lived JWTs; once expired they are harmless. Still, keep the pattern consistent so reviewers can tell at a glance that no real secrets are present.

---

## 9. Seed data alignment

The requests in `.http` files must reference IDs and states that are actually present and stable in `seeds/all.sql`. When adding or changing seed data:

- Update the affected `.http` files to reflect the new IDs or states.
- Add a comment in the request body pointing to the seed row if the relationship is not immediately obvious (e.g., `# Shoply — active merchant with active offer`).

If a scenario requires a specific state that `seeds/all.sql` does not yet provide (e.g., a confirmed purchase or an inactive merchant), add the row to `seeds/all.sql` and document it as part of the feature's Step 10 commit.

---

## 10. Full annotated example

```http
# Merchants – Activate / Deactivate Merchant
# Smoke tests for PATCH /merchants/{id}/status.
#
# Admin-only endpoint. Toggles a merchant between "active" and "inactive".
# Run the helper login requests to obtain a fresh token, then paste it into
# @adminToken above.

@baseUrl    = http://localhost:8001/api/v1
@merchantId = a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d  # Shoply (seeded active)

# Expired local-dev placeholders — never real credentials.
@adminToken = Bearer eyJ...
@userToken  = Bearer eyJ...

### Helper – obtain a fresh admin token (carol)
# Returns access_token — paste as "Bearer <token>" into @adminToken above.
POST {{baseUrl}}/auth/login
Content-Type: application/json

{
  "email": "carol@clicknback.com",
  "password": "Str0ng!Pass"
}

### Helper – obtain a fresh user token (alice)
# Returns access_token — paste as "Bearer <token>" into @userToken above.
POST {{baseUrl}}/auth/login
Content-Type: application/json

{
  "email": "alice@clicknback.com",
  "password": "Str0ng!Pass"
}

### 200 – Happy path: deactivate an active merchant
# Sets Shoply to inactive. Run the activate request below to restore it.
PATCH {{baseUrl}}/merchants/{{merchantId}}/status
Authorization: {{adminToken}}
Content-Type: application/json

{
  "status": "inactive"
}

### 200 – Happy path: activate an inactive merchant
# Restores Shoply to active. Verifies the round-trip.
PATCH {{baseUrl}}/merchants/{{merchantId}}/status
Authorization: {{adminToken}}
Content-Type: application/json

{
  "status": "active"
}

### 401 – Sad path: missing authentication token
PATCH {{baseUrl}}/merchants/{{merchantId}}/status
Content-Type: application/json

{
  "status": "active"
}

### 403 – Sad path: authenticated as a non-admin user
# alice has role=user; expects 403 FORBIDDEN.
PATCH {{baseUrl}}/merchants/{{merchantId}}/status
Authorization: {{userToken}}
Content-Type: application/json

{
  "status": "active"
}

### 404 – Sad path: merchant does not exist
# All-zero UUID is guaranteed to have no database row.
PATCH {{baseUrl}}/merchants/00000000-0000-0000-0000-000000000000/status
Authorization: {{adminToken}}
Content-Type: application/json

{
  "status": "active"
}

### 422 – Sad path: invalid status value
# Pydantic rejects values outside the allowed enum (active | inactive).
PATCH {{baseUrl}}/merchants/{{merchantId}}/status
Authorization: {{adminToken}}
Content-Type: application/json

{
  "status": "unknown_status"
}
```
