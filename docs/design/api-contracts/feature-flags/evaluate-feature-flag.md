# Evaluate Feature Flag

**Endpoint:** `GET /api/v1/feature-flags/{key}/evaluate`
**Roles:** Admin *(v1; machine tokens when extracted to a microservice)*

---

## Request

**Path parameters**:

| Parameter | Type | Description |
| --- | --- | --- |
| `key` | string | Feature flag key to evaluate, e.g. `purchase_confirmation_job` |

**Query parameters**:

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `scope_type` | string | ❌ | `global` (default), `merchant`, or `user` |
| `scope_id` | UUID | ❌ | Required when `scope_type` is `merchant` or `user` |

**Examples:**

```http
GET /api/v1/feature-flags/purchase_confirmation_job/evaluate
GET /api/v1/feature-flags/purchase_confirmation_job/evaluate?scope_type=merchant&scope_id=a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

---

## Success Response

**Status:** `200 OK`

Resolution follows strict priority: scoped flag → global flag → default (`true`).

```json
{
  "key": "purchase_confirmation_job",
  "enabled": false
}
```

**Fail-open response (no flag record exists):**

```json
{
  "key": "new_cashback_rules",
  "enabled": true
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
