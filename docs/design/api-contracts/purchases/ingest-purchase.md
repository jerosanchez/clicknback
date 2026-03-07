# Ingest purchase

**Endpoint:** `POST /purchases`

**Roles:** Any authenticated user (valid Bearer token required)

**Note:** This endpoint is idempotent with respect to `external_id`: re-submitting the same
`external_id` always returns a **409 Conflict** with details of the previously ingested purchase.
No duplicate purchase record is ever created.

**Ownership rule:** The `user_id` in the request body must match the authenticated user's ID.
A user may only ingest purchases on behalf of themselves. See ADR 012.

## Request

```json
{
  "external_id": "txn_001",
  "user_id": "b7e6c2e2-8c2a-4e2a-9b1a-2e6c2e2a8c2a",
  "merchant_id": "e3b0c442-98fc-1c14-9afb-4c4e6c2e2a8c",
  "amount": 100.50,
  "currency": "EUR"
}
```

### Field Constraints

| Field | Type | Constraints |
| --- | --- | --- |
| `external_id` | string | Required. Non-empty string. Unique idempotency key. |
| `user_id` | UUID | Required. Must be a valid UUID. Must match the authenticated user's ID. |
| `merchant_id` | UUID | Required. Must be a valid UUID. |
| `amount` | decimal | Required. Must be a positive number (greater than zero). |
| `currency` | string | Required. Must be `EUR`. The platform currently accepts purchases in EUR only. |

**Note:** `offer_id` is **not** provided by the caller. The system resolves the active,
date-valid offer for the given merchant automatically and stores it on the purchase record.

## Success Response

**Status:** 201 Created

```json
{
  "id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "status": "pending",
  "cashback_amount": 0
}
```

**Notes:**

- `status` is always `"pending"` for a newly ingested purchase.
- `cashback_amount` is always `0` at ingestion time. Cashback is calculated and
  credited when the purchase is confirmed in a subsequent flow.

## Failure Responses

### 422 Unprocessable Entity – Validation Error

Returned when the request body fails input validation (missing required fields,
invalid UUID format, non-positive amount, or currency string not exactly 3 characters).

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "external_id"],
      "msg": "Field required"
    }
  ]
}
```

> **Note:** Request body validation errors are returned in FastAPI's native Pydantic
> format (HTTP 422). The custom `VALIDATION_ERROR` error envelope format described in
> the error handling strategy applies to domain-level errors raised by the application
> layer, not framework-level schema validation.

### 401 Unauthorized – Missing or Invalid Authentication

```json
{
  "error": {
    "code": "INVALID_TOKEN",
    "message": "Invalid or expired token, or user has not the permissions to perform this action.",
    "details": {}
  }
}
```

### 403 Forbidden – Purchase Ownership Violation

Returned when the `user_id` in the request body does not match the authenticated user's ID.
Users may only ingest purchases on their own behalf.

```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "You can only ingest purchases on your own behalf.",
    "details": {
      "reason": "The user_id in the request does not match the authenticated user."
    }
  }
}
```

### 409 Conflict – Duplicate Purchase

Returned when a purchase with the same `external_id` has already been ingested.
The caller should treat this as the canonical result for this `external_id`.

```json
{
  "error": {
    "code": "DUPLICATE_PURCHASE",
    "message": "A purchase with external ID 'txn_001' has already been processed.",
    "details": {
      "external_id": "txn_001",
      "previously_created_at": "2026-02-17T13:45:00Z",
      "previously_processed_amount": "100.50",
      "action": "This request is idempotent and safe to retry. You will receive the same result."
    }
  }
}
```

### 422 Unprocessable Entity – User Not Found or Inactive

Returned when the supplied `user_id` does not correspond to an existing, active user.

```json
{
  "error": {
    "code": "UNPROCESSABLE_ENTITY",
    "message": "User with ID 'b7e6c2e2-8c2a-4e2a-9b1a-2e6c2e2a8c2a' does not exist or is inactive.",
    "details": {
      "user_id": "b7e6c2e2-8c2a-4e2a-9b1a-2e6c2e2a8c2a",
      "reason": "Purchase cannot be ingested for non-existent or inactive users."
    }
  }
}
```

### 422 Unprocessable Entity – Merchant Not Found or Inactive

Returned when the supplied `merchant_id` does not correspond to an existing, active merchant.

```json
{
  "error": {
    "code": "UNPROCESSABLE_ENTITY",
    "message": "Merchant with ID 'e3b0c442-98fc-1c14-9afb-4c4e6c2e2a8c' is not active or does not exist.",
    "details": {
      "merchant_id": "e3b0c442-98fc-1c14-9afb-4c4e6c2e2a8c",
      "reason": "Purchases cannot be processed for inactive merchants."
    }
  }
}
```

### 422 Unprocessable Entity – No Active Offer Available for Merchant

Returned when the merchant has no offer that is simultaneously: `active = true` **and**
valid for today's date (`start_date <= today <= end_date`).

This covers three root causes — no offer exists, offer is inactive, or offer is outside
its valid date range (expired or not yet started) — all of which prevent purchase ingestion.

```json
{
  "error": {
    "code": "UNPROCESSABLE_ENTITY",
    "message": "No active offer is available for merchant 'e3b0c442-98fc-1c14-9afb-4c4e6c2e2a8c'.",
    "details": {
      "merchant_id": "e3b0c442-98fc-1c14-9afb-4c4e6c2e2a8c",
      "reason": "Purchases cannot be processed without a valid active offer for the merchant."
    }
  }
}
```

### 422 Unprocessable Entity – Unsupported Currency

Returned when the `currency` field contains a value other than `EUR`.
The platform currently processes purchases in EUR only.

```json
{
  "error": {
    "code": "UNPROCESSABLE_ENTITY",
    "message": "Currency 'USD' is not supported. Only EUR is accepted at this time.",
    "details": {
      "currency": "USD",
      "reason": "The platform currently processes purchases in EUR only."
    }
  }
}
```
