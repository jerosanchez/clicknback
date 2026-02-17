# List wallet transactions

**Endpoint:** `GET /users/wallet/transactions`

**Roles:** Authenticated

## Query Parameters

- `limit` (optional): Number of items per page (default: 10)
- `offset` (optional): Pagination offset (default: 0)

**Example:** `?limit=10&offset=0`

## Success Response

**Status:** 200 OK

```json
{
  "transactions": [
    {
      "id": "c1b2c3d4-5678-90ab-cdef-1234567890ab",
      "type": "cashback_credit",
      "amount": 10.05,
      "status": "available",
      "related_purchase_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab"
    }
  ],
  "total": 1
}
```
