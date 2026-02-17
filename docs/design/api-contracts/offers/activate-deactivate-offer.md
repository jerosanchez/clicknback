# Activate/deactivate offer

**Endpoint:** `PATCH /offers/{id}/status`

**Roles:** Admin

## Request

```json
{
  "status": "inactive"
}
```

## Success Response

**Status:** 200 OK

```json
{
  "id": "f4b0c442-98fc-1c14-9afb-4c4e6c2e2a8c",
  "status": "inactive"
}
```

## Failure Responses

### 400 Bad Request – Invalid Status

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid status value. Supported values are: 'active', 'inactive'.",
    "details": {
      "field": "status",
      "received": "archived",
      "supported_values": ["active", "inactive"]
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
    "message": "You do not have permission to modify offers. Admin role required.",
    "details": {
      "required_role": "admin",
      "current_role": "user"
    }
  }
}
```

### 404 Not Found – Offer Does Not Exist

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Offer with ID 'f4b0c442-98fc-1c14-9afb-4c4e6c2e2a8c' does not exist.",
    "details": {
      "resource_type": "offer",
      "resource_id": "f4b0c442-98fc-1c14-9afb-4c4e6c2e2a8c"
    }
  }
}
```
