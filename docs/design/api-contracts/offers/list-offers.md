# List all offers

**Endpoint:** `GET /offers`

**Roles:** Admin

## Query Parameters

- `limit` (optional): Number of items per page (default: 10)
- `offset` (optional): Pagination offset (default: 0)
- `status` (optional): Filter by status (e.g., "active")

**Example:** `?limit=10&offset=0&status=active`

## Success Response

**Status:** 200 OK

```json
{
  "offers": [
    {
      "id": "f4b0c442-98fc-1c14-9afb-4c4e6c2e2a8c",
      "merchant_id": "e3b0c442-98fc-1c14-9afb-4c4e6c2e2a8c",
      "cashback_type": "percent",
      "cashback_value": 10,
      "status": "active"
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
    "message": "You do not have permission to list offers. Admin role required.",
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
          "reason": "Status must be one of: active, inactive."
        }
      ]
    }
  }
}
```
