# List user purchases

**Endpoint:** `GET /users/purchases`

**Roles:** Authenticated

## Query Parameters

- `limit` (optional): Number of items per page (default: 10)
- `offset` (optional): Pagination offset (default: 0)
- `status` (optional): Filter by status (e.g., "confirmed")

**Example:** `?limit=10&offset=0&status=confirmed`

## Success Response

**Status:** 200 OK

```json
{
  "purchases": [
    {
      "id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
      "merchant_name": "CoolShop",
      "amount": 100.50,
      "status": "confirmed",
      "cashback_amount": 10.05,
      "cashback_status": "available"
    }
  ],
  "total": 1
}
```
