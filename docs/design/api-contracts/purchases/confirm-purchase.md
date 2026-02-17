# Confirm purchase

**Endpoint:** `PATCH /purchases/{id}/confirm`

**Roles:** Admin

## Success Response

**Status:** 200 OK

```json
{
  "id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "status": "confirmed",
  "cashback_amount": 10.05
}
```

## Failure Responses

- **400 Bad Request** – invalid state
- **403 Forbidden** – non-admin
