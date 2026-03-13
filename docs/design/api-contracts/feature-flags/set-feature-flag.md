# Set Feature Flag

**Endpoint:** `PUT /api/v1/feature-flags/{key}`
**Roles:** Admin

---

## Request

**Path parameters**:

| Parameter | Type | Description |
| --- | --- | --- |
| `key` | string | Feature flag key, e.g. `purchase_confirmation_job` |

**Body**:

```json
{
  "enabled": true,
  "scope_type": "merchant",
  "scope_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "description": "Disable for specific merchant during migration"
}
```

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `enabled` | boolean | ✅ | Whether the flag is active |
| `scope_type` | string | ❌ | `global` (default), `merchant`, or `user` |
| `scope_id` | UUID | ❌ | Required when `scope_type` is `merchant` or `user` |
| `description` | string | ❌ | Human-readable description of the flag's intent |

---

## Success Response

**Status:** `200 OK`

```json
{
  "id": "7f3a1234-bc56-7890-def0-1234567890ab",
  "key": "purchase_confirmation_job",
  "enabled": true,
  "scope_type": "merchant",
  "scope_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "description": "Disable for specific merchant during migration",
  "created_at": "2025-01-15T12:00:00Z",
  "updated_at": "2025-01-15T14:30:00Z"
}
```

---

## Failure Responses

### 401 Unauthorized — Missing or invalid token

```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Authentication required.",
    "details": {}
  }
}
```

### 403 Forbidden — Caller is not an admin

```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "Admin role required.",
    "details": {}
  }
}
```

### 422 Unprocessable Entity — scope_id required for non-global scope

```json
{
  "error": {
    "code": "FEATURE_FLAG_SCOPE_ID_REQUIRED",
    "message": "scope_id is required when scope_type is 'merchant' or 'user'.",
    "details": {
      "scope_type": "merchant"
    }
  }
}
```

### 422 Unprocessable Entity — Invalid scope_type

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid value for scope_type.",
    "details": {
      "scope_type": "store"
    }
  }
}
```
