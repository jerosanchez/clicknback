# List Feature Flags

**Endpoint:** `GET /api/v1/feature-flags`
**Roles:** Admin

---

## Request

**Query parameters**:

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `key` | string | ❌ | Filter by exact flag key |
| `scope_type` | string | ❌ | Filter by `global`, `merchant`, or `user` |
| `scope_id` | UUID | ❌ | Filter by scope entity UUID |
| `offset` | integer | ❌ | Pagination offset (default: 0, min: 0) |
| `limit` | integer | ❌ | Number of items per page (default: 10, min: 1, max: 100) |

All filters are optional. When multiple filters are provided they are combined with `AND` semantics.

**Example — no filter:**

```http
GET /api/v1/feature-flags
```

**Example — filtered by key:**

```http
GET /api/v1/feature-flags?key=purchase_confirmation_job
```

**Example — filtered by scope:**

```http
GET /api/v1/feature-flags?scope_type=merchant&scope_id=a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

---

## Success Response

**Status:** `200 OK`

```json
{
  "data": [
    {
      "id": "7f3a1234-bc56-7890-def0-1234567890ab",
      "key": "purchase_confirmation_job",
      "enabled": false,
      "scope_type": "global",
      "scope_id": null,
      "description": "Disables the purchase confirmation background job globally",
      "created_at": "2025-01-10T08:00:00Z",
      "updated_at": "2025-01-15T14:30:00Z"
    },
    {
      "id": "9c8b7654-fe32-1098-dcba-fedcba987654",
      "key": "purchase_confirmation_job",
      "enabled": true,
      "scope_type": "merchant",
      "scope_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "description": "Override: keep job enabled for this merchant",
      "created_at": "2025-01-12T09:00:00Z",
      "updated_at": "2025-01-12T09:00:00Z"
    }
  ],
  "pagination": {
    "offset": 0,
    "limit": 10,
    "total": 2
  }
}
```

**Empty result:**

```json
{
  "data": [],
  "pagination": {
    "offset": 0,
    "limit": 10,
    "total": 0
  }
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
