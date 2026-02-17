# Ingest purchase

**Endpoint:** `POST /purchases`

**Roles:** External / System

**Note:** This endpoint is idempotent.

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

## Success Response

**Status:** 201 Created or 200 OK if duplicate

```json
{
  "id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "status": "pending",
  "cashback_amount": 0
}
```

## Failure Responses

### 400 Bad Request – Validation Error

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed for request body.",
    "details": {
      "violations": [
        {
          "field": "external_id",
          "reason": "External ID is required and must be a non-empty string."
        },
        {
          "field": "amount",
          "reason": "Amount must be a positive number."
        },
        {
          "field": "user_id",
          "reason": "User ID is required and must be a valid UUID."
        }
      ]
    }
  }
}
```

### 401 Unauthorized – Missing Authentication

```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Authentication token is missing or invalid.",
    "details": {
      "issue": "Token expired or malformed",
      "action": "Include a valid Bearer token in the Authorization header."
    }
  }
}
```

### 409 Conflict – Duplicate Purchase (Idempotent)

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

### 422 Unprocessable Entity – User Not Found

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
