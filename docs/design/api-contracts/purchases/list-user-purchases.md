# List user purchases

**Endpoint:** `GET /users/purchases`

**Roles:** Authenticated

## Query Parameters

- `limit` (optional): Number of items per page (default: 10)
- `offset` (optional): Pagination offset (default: 0)
- `status` (optional): Filter by status (e.g., "confirmed")

**Example:** `?limit=10&offset=0&status=confirmed`

## Success Response

**Status:** 200 OK

```json
{
  "purchases": [
    {
      "id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
      "merchant_name": "CoolShop",
      "amount": 100.50,
      "status": "confirmed",
      "cashback_amount": 10.05,
      "cashback_status": "available"
    }
  ],
  "total": 1
}
```

## Failure Responses

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

### 400 Bad Request – Invalid Query Parameters

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid query parameters.",
    "details": {
      "violations": [
        {
          "field": "limit",
          "reason": "Limit must be a positive integer between 1 and 100."
        },
        {
          "field": "status",
          "reason": "Status must be one of: pending, confirmed, reversed."
        }
      ]
    }
  }
}
```
