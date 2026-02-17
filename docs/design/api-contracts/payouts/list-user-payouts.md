# List user payouts

**Endpoint:** `GET /users/payouts`

**Roles:** Authenticated

## Success Response

**Status:** 200 OK

```json
{
  "payouts": [
    {
      "id": "d1b2c3d4-5678-90ab-cdef-1234567890ab",
      "status": "requested",
      "amount": 20.00
    }
  ],
  "total": 1
}
```
