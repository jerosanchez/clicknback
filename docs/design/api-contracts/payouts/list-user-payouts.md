# List user payouts

**Endpoint:** `GET /users/payouts`

**Roles:** Authenticated

## Success Response

**Status:** 200 OK

```json
{
  "payouts": [
    {
      "id": "d1b2c3d4-5678-90ab-cdef-1234567890ab",
      "status": "requested",
      "amount": 20.00
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
          "reason": "Status must be one of: requested, completed, failed."
        }
      ]
    }
  }
}
```
