# Create a merchant

**Endpoint:** `POST /merchants`

**Roles:** Admin

## Request

```json
{
  "name": "CoolShop",
  "default_cashback_pct": 5
}
```

## Success Response

**Status:** 201 Created

```json
{
  "id": "e3b0c442-98fc-1c14-9afb-4c4e6c2e2a8c",
  "name": "CoolShop",
  "default_cashback_pct": 5,
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
          "field": "name",
          "reason": "Merchant name is required and must be between 1 and 255 characters."
        },
        {
          "field": "default_cashback_pct",
          "reason": "Cashback percentage must be between 0 and 100."
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
    "message": "You do not have permission to create merchants. Admin role required.",
    "details": {
      "required_role": "admin",
      "current_role": "user",
      "action": "Use an admin account to perform this action."
    }
  }
}
```
