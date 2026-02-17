# Create cashback offer

**Endpoint:** `POST /offers`

**Roles:** Admin

## Request

```json
{
  "merchant_id": "e3b0c442-98fc-1c14-9afb-4c4e6c2e2a8c",
  "cashback_type": "percent",
  "cashback_value": 10,
  "start_date": "2026-02-01T00:00:00Z",
  "end_date": "2026-12-31T23:59:59Z",
  "monthly_cap": 50
}
```

## Success Response

**Status:** 201 Created

```json
{
  "id": "f4b0c442-98fc-1c14-9afb-4c4e6c2e2a8c",
  "merchant_id": "e3b0c442-98fc-1c14-9afb-4c4e6c2e2a8c",
  "cashback_type": "percent",
  "cashback_value": 10,
  "status": "active"
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
          "field": "cashback_value",
          "reason": "Cashback value must be positive and match cashback_type (percentage 0-100 or fixed amount > 0)."
        },
        {
          "field": "end_date",
          "reason": "End date must be after start date."
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

### 403 Forbidden – Insufficient Permissions

```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "You do not have permission to create offers. Admin role required.",
    "details": {
      "required_role": "admin",
      "current_role": "user"
    }
  }
}
```

### 422 Unprocessable Entity – Merchant Not Active

```json
{
  "error": {
    "code": "UNPROCESSABLE_ENTITY",
    "message": "Cannot create offer for merchant 'e3b0c442-98fc-1c14-9afb-4c4e6c2e2a8c'. Merchant is not active.",
    "details": {
      "merchant_id": "e3b0c442-98fc-1c14-9afb-4c4e6c2e2a8c",
      "merchant_status": "inactive",
      "action": "Activate the merchant before creating offers."
    }
  }
}
```
