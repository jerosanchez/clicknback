# Delete Feature Flag

**Endpoint:** `DELETE /api/v1/feature-flags/{key}`
**Roles:** Admin

---

## Request

**Path parameters**

| Parameter | Type | Description |
| --- | --- | --- |
| `key` | string | Feature flag key, e.g. `purchase_confirmation_job` |

**Query parameters**

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `scope_type` | string | ✅ | `global`, `merchant`, or `user` |
| `scope_id` | UUID | ❌ | Required when `scope_type` is `merchant` or `user` |

**Example:**

```
DELETE /api/v1/feature-flags/purchase_confirmation_job?scope_type=merchant&scope_id=a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

---

## Success Response

**Status:** `204 No Content`

No response body.

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

### 404 Not Found — Flag record does not exist

```json
{
  "error": {
    "code": "FEATURE_FLAG_NOT_FOUND",
    "message": "Feature flag 'purchase_confirmation_job' with the given scope was not found.",
    "details": {
      "key": "purchase_confirmation_job",
      "scope_type": "merchant",
      "scope_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    }
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
