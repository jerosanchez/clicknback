# List merchants

**Endpoint:** `GET /merchants`

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
  "merchants": [
    {
      "id": "e3b0c442-98fc-1c14-9afb-4c4e6c2e2a8c",
      "name": "CoolShop",
      "status": "active"
    }
  ],
  "total": 1
}
```
