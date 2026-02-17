# List all payouts

**Endpoint:** `GET /admin/payouts`

**Roles:** Admin

## Query Parameters

- `limit` (optional): Number of items per page (default: 10)
- `offset` (optional): Pagination offset (default: 0)
- `status` (optional): Filter by status (e.g., "completed")

**Example:** `?limit=10&offset=0&status=completed`

## Success Response

**Status:** 200 OK

```json
{
  "payouts": [
    {
      "id": "d1b2c3d4-5678-90ab-cdef-1234567890ab",
      "user_id": "b7e6c2e2-8c2a-4e2a-9b1a-2e6c2e2a8c2a",
      "amount": 20.00,
      "status": "completed"
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

### 403 Forbidden – Insufficient Permissions

```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "You do not have permission to list payouts. Admin role required.",
    "details": {
      "required_role": "admin",
      "current_role": "user"
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
