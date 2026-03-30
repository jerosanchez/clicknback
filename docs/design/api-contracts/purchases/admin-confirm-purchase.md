# Admin confirm purchase

**Endpoint:** `POST /purchases/{id}/confirmation`

**Roles:** Admin

## Request

### Path Parameters

| Parameter | Type   | Required | Description                         |
|-----------|--------|----------|-------------------------------------|
| `id`      | string | Yes      | UUID of the purchase to confirm.    |

## Success Response

**Status:** 200 OK

```json
{
  "id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "user_id": "b2c3d4e5-6789-01bc-defg-2345678901bc",
  "merchant_id": "c3d4e5f6-7890-12cd-efgh-3456789012cd",
  "status": "confirmed",
  "purchase_date": "2026-03-20T14:30:00Z",
  "amount": "99.99",
  "cashback_amount": "9.99",
  "confirmed_at": "2026-03-28T10:15:00Z"
}
```

## Failure Responses

### 400 Bad Request – Invalid State Transition

```json
{
  "error": {
    "code": "PURCHASE_NOT_PENDING",
    "message": "Cannot confirm purchase 'a1b2c3d4-5678-90ab-cdef-1234567890ab'. Purchase status is 'confirmed', not 'pending'.",
    "details": {
      "purchase_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
      "current_status": "confirmed",
      "required_status": "pending"
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
    "message": "You do not have permission to confirm purchases. Admin role required.",
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

### 500 Internal Server Error

```json
{
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "An unexpected error occurred while processing your request.",
    "details": {
      "request_id": "req-1234567890ab"
    }
  }
}
```

## See Also

- [PU-08: Admin Manual Purchase Confirmation](../../../specs/functional/purchases/PU-08-admin-manual-confirm-purchase.md)
- [PU-02: Purchase Confirmation (Async/Event-Driven)](../../../specs/functional/purchases/PU-02-purchase-confirmation.md)
