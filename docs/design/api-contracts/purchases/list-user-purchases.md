# List user purchases

**Endpoint:** `GET /users/me/purchases`

**Roles:** Authenticated

## Query Parameters

- `offset` (optional): Pagination offset, 0-based (default: 0, min: 0)
- `limit` (optional): Number of items per page (default: 10, min: 1, max: 100)
- `status` (optional): Filter by status: `pending`, `confirmed`, or `reversed`

**Example:** `?offset=0&limit=10&status=confirmed`

## Success Response

**Status:** 200 OK

```json
{
  "data": [
    {
      "id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
      "merchant_name": "CoolShop",
      "amount": "100.50",
      "status": "confirmed",
      "cashback_amount": "10.05",
      "cashback_status": "available",
      "created_at": "2026-03-01T10:00:00"
    }
  ],
  "pagination": {
    "offset": 0,
    "limit": 10,
    "total": 1
  }
}
```

## Failure Responses

### 401 Unauthorized – Missing or Invalid Authentication

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

### 422 Unprocessable Entity – Invalid Status Filter

```json
{
  "error": {
    "code": "INVALID_PURCHASE_STATUS",
    "message": "'badvalue' is not a valid purchase status. Allowed values: pending, confirmed, reversed.",
    "details": {}
  }
}
```

### 422 Unprocessable Entity – Invalid Pagination Parameters

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed.",
    "details": {
      "violations": [
        {
          "field": "offset",
          "reason": "Input should be greater than or equal to 0"
        }
      ]
    }
  }
}
```
