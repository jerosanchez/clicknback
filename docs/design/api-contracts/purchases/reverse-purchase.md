# Reverse purchase

**Endpoint:** `PATCH /purchases/{id}/reverse`

**Roles:** Admin

## Success Response

**Status:** 200 OK

```json
{
  "id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "status": "reversed",
  "cashback_amount": 0
}
```

## Failure Responses

### 400 Bad Request – Invalid State Transition

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Cannot reverse purchase 'a1b2c3d4-5678-90ab-cdef-1234567890ab'. Purchase is already reversed.",
    "details": {
      "purchase_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
      "current_status": "reversed",
      "allowed_transitions": ["pending", "confirmed"]
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
    "message": "You do not have permission to reverse purchases. Admin role required.",
    "details": {
      "required_role": "admin",
      "current_role": "user"
    }
  }
}
```

### 404 Not Found – Purchase Does Not Exist

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Purchase with ID 'a1b2c3d4-5678-90ab-cdef-1234567890ab' does not exist.",
    "details": {
      "resource_type": "purchase",
      "resource_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab"
    }
  }
}
```
