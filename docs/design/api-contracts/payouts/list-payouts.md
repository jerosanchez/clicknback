# List all payouts

**Endpoint:** `GET /admin/payouts`

**Roles:** Admin

## Query Parameters

- `limit` (optional): Number of items per page (default: 10)
- `offset` (optional): Pagination offset (default: 0)
- `status` (optional): Filter by status (e.g., "completed")

**Example:** `?limit=10&offset=0&status=completed`

## Success Response

**Status:** 200 OK

```json
{
  "payouts": [
    {
      "id": "d1b2c3d4-5678-90ab-cdef-1234567890ab",
      "user_id": "b7e6c2e2-8c2a-4e2a-9b1a-2e6c2e2a8c2a",
      "amount": 20.00,
      "status": "completed"
    }
  ],
  "total": 1
}
```
