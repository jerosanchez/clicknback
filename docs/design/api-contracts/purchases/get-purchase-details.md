# Get purchase details

**Endpoint:** `GET /users/purchases/{id}`

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

## Failure Responses

- **404 Not Found**
- **403 Forbidden** – purchase belongs to another user
