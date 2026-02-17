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

- **400 Bad Request** – invalid state
- **403 Forbidden** – non-admin
