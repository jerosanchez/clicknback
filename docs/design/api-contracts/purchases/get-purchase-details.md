# Get purchase details

**Endpoint:** `GET /purchases/{id}`

**Roles:** Authenticated

## Success Response

**Status:** 200 OK

```json
{
  "id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "merchant_name": "CoolShop",
  "amount": 100.50,
  "status": "confirmed",
  "cashback_amount": 10.05,
  "cashback_status": "available",
  "created_at": "2026-02-13T12:00:00Z"
}
```

> `cashback_amount` is `0` and `cashback_status` is `null` when no cashback transaction exists for this purchase yet.

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
    "message": "You do not have permission to view this purchase. Purchase belongs to another user.",
    "details": {
      "purchase_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
      "resource_owner": "different_user_id",
      "current_user": "your_user_id"
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

### 500 Internal Server Error – Unexpected Error

```json
{
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "An unexpected error occurred. Please try again later.",
    "details": null
  }
}
```
