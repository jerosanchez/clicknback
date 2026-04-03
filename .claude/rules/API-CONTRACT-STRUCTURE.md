---
name: api-contract-structure
type: rule
description: Structure and mandatory sections for API contract documents
---

# API-CONTRACT-STRUCTURE

## Overview

An API contract specifies the **exact HTTP interface** for an endpoint. It describes the request, response, and all failure modes. Contracts are implementation-agnostic but technically precise — they specify JSON fields, HTTP status codes, and headers.

**Note on Front Matter:** API contracts are regular Markdown files (`.md`) stored in `docs/design/api-contracts/`. Do not add YAML front matter. Per [MARKDOWN-STANDARDS.md](./MARKDOWN-STANDARDS.md), only use official front matter keys (name, type, description) for files in `.claude/` folder. Contract files themselves should not have front matter.

## One Contract Per Endpoint

One contract covers exactly one HTTP endpoint (one method + path combination).

**Correct:**
- `get-purchase.md` (GET /api/v1/purchases/{id})
- `list-purchases.md` (GET /api/v1/purchases)
- `create-purchase.md` (POST /api/v1/purchases)

**Incorrect:**
- `purchases.md` (covers multiple methods/paths)

## Naming Convention

```
docs/design/api-contracts/<domain>/<verb-resource>.md
```

- **verb** — HTTP operation: `get`, `post`, `put`, `patch`, `delete`, `list`
- **resource** — Kebab-case resource name

Example: `docs/design/api-contracts/purchases/create-purchase.md`

## Mandatory Sections (In Order)

### 1. Title and Endpoint Declaration

```markdown
# Create Purchase

**Endpoint:** `POST /api/v1/purchases`  
**Roles:** User, Admin  
**Related Spec:** [PU-01 Purchase Ingestion](../../specs/functional/purchases/PU-01-purchase-ingestion.md)
```

**Roles:** Who can call this? `Admin`, `User`, `Public` (unauthenticated), `System` (internal).

### 2. Request Section

```markdown
## Request

**Path Parameters:** (none for this endpoint)

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| - | - | - | (none) |

**Body (application/json):**

```json
{
  "merchant_id": "uuid",
  "amount": "123.45",
  "currency": "EUR",
  "external_id": "EXT-ABC-123",
  "purchase_date": "2024-01-15"
}
```

**Field Descriptions:**

| Field | Type | Required | Valid Values | Description |
|-------|------|----------|--------------|-------------|
| `merchant_id` | string (UUID) | ✅ | Valid merchant ID | Merchant where purchase occurred |
| `amount` | string (decimal) | ✅ | > 0, ≤ 10000 | Purchase amount in EUR |
| `currency` | string | ✅ | "EUR" | Currency code; only EUR supported |
| `external_id` | string | ✅ | 1-255 chars | Unique idempotency key |
| `purchase_date` | string (ISO 8601) | ✅ | YYYY-MM-DD | Date of purchase |

**Authentication:**

Bearer token (JWT). Include `Authorization: Bearer <token>` header.

**Example:**

```bash
curl -X POST http://localhost:8001/api/v1/purchases \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "merchant_id": "550e8400-e29b-41d4-a716-446655440000",
    "amount": "123.45",
    "currency": "EUR",
    "external_id": "EXT-ABC-123",
    "purchase_date": "2024-01-15"
  }'
```

---

### 3. Success Response

```markdown
## Success Response

**Status Code:** `201 Created`

**Response Body (application/json):**

```json
{
  "id": "uuid",
  "merchant_id": "uuid",
  "user_id": "uuid",
  "amount": "123.45",
  "currency": "EUR",
  "external_id": "EXT-ABC-123",
  "status": "pending",
  "purchase_date": "2024-01-15",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Field Descriptions:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique purchase ID (system-generated) |
| `status` | string | Current status: `pending`, `confirmed`, `reversed` |
| `created_at` | ISO 8601 | Server timestamp of creation |
```

### 4. Failure Responses

```markdown
## Failure Responses

### 400 Bad Request

**When:** Request malformed (invalid JSON)

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "JSON is malformed",
    "details": {}
  }
}
```

### 401 Unauthorized

**When:** Missing or invalid authentication

```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Missing or invalid token",
    "details": {}
  }
}
```

### 422 Unprocessable Entity

**When:** Validation fails (invalid amount, unknown merchant, etc.)

```json
{
  "error": {
    "code": "INVALID_PURCHASE_AMOUNT",
    "message": "Amount must be > 0 and ≤ 10000 EUR",
    "details": { "amount": "123.45", "max": 10000 }
  }
}
```

### 404 Not Found

**When:** Merchant does not exist

```json
{
  "error": {
    "code": "MERCHANT_NOT_FOUND",
    "message": "Merchant 550e8400... not found",
    "details": { "merchant_id": "550e8400-e29b-41d4-a716-446655440000" }
  }
}
```

### 409 Conflict

**When:** Duplicate external_id (idempotency conflict)

```json
{
  "error": {
    "code": "DUPLICATE_PURCHASE",
    "message": "Purchase with external_id EXT-ABC-123 already exists",
    "details": { "external_id": "EXT-ABC-123", "existing_id": "uuid" }
  }
}
```

### 500 Internal Server Error

**When:** Unexpected server error

```json
{
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "An unexpected error occurred",
    "details": {}
  }
}
```
```

## Guidelines

- **One endpoint per contract**: Never combine multiple HTTP methods in one document.
- **Realistic data**: Use valid UUIDs, ISO 8601 timestamps, actual enum values. No lorem ipsum.
- **Error codes are specific**: Use `MERCHANT_NOT_FOUND`, not `ERROR`.
- **Always include 401, 403 (if applicable), and 500**: These apply to all endpoints.
- **Status codes must match intent**: `201 Created` for new resources, `200 OK` for updates, `204 No Content` for deletes, etc.
- **After creating/modifying**: Update `docs/design/api-contracts-index.md`.

---
