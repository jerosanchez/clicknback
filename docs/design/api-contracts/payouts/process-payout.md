# Complete/fail payout

**Endpoint:** `PATCH /admin/payouts/{id}/process`

**Roles:** Admin

## Request

```json
{
  "status": "completed"
}
```

## Success Response

**Status:** 200 OK

```json
{
  "id": "d1b2c3d4-5678-90ab-cdef-1234567890ab",
  "status": "completed"
}
```

## Failure Responses

### 400 Bad Request – Invalid Status

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid status value. Supported values are: 'completed', 'failed'.",
    "details": {
      "field": "status",
      "received": "pending",
      "supported_values": ["completed", "failed"]
    }
  }
}
```

### 400 Bad Request – Invalid State Transition

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Cannot process payout 'd1b2c3d4-5678-90ab-cdef-1234567890ab'. Payout is already completed.",
    "details": {
      "payout_id": "d1b2c3d4-5678-90ab-cdef-1234567890ab",
      "current_status": "completed",
      "allowed_transitions": ["requested"]
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
    "message": "You do not have permission to process payouts. Admin role required.",
    "details": {
      "required_role": "admin",
      "current_role": "user"
    }
  }
}
```

### 404 Not Found – Payout Does Not Exist

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Payout with ID 'd1b2c3d4-5678-90ab-cdef-1234567890ab' does not exist.",
    "details": {
      "resource_type": "payout",
      "resource_id": "d1b2c3d4-5678-90ab-cdef-1234567890ab"
    }
  }
}
```
