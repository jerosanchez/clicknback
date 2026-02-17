# List all offers

**Endpoint:** `GET /offers`

**Roles:** Admin

## Query Parameters

- `limit` (optional): Number of items per page (default: 10)
- `offset` (optional): Pagination offset (default: 0)
- `status` (optional): Filter by status (e.g., "active")

**Example:** `?limit=10&offset=0&status=active`

## Success Response

**Status:** 200 OK

```json
{
  "offers": [
    {
      "id": "f4b0c442-98fc-1c14-9afb-4c4e6c2e2a8c",
      "merchant_id": "e3b0c442-98fc-1c14-9afb-4c4e6c2e2a8c",
      "cashback_type": "percent",
      "cashback_value": 10,
      "status": "active"
    }
  ],
  "total": 1
}
```
