# List wallet transactions

**Endpoint:** `GET /users/wallet/transactions`

**Roles:** Authenticated

## Query Parameters

- `limit` (optional): Number of items per page (default: 10)
- `offset` (optional): Pagination offset (default: 0)

**Example:** `?limit=10&offset=0`

## Success Response

**Status:** 200 OK

```json
{
  "transactions": [
    {
      "id": "c1b2c3d4-5678-90ab-cdef-1234567890ab",
      "type": "cashback_credit",
      "amount": 10.05,
      "status": "available",
      "related_purchase_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab"
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
          "field": "offset",
          "reason": "Offset must be a non-negative integer."
        }
      ]
    }
  }
}
```
