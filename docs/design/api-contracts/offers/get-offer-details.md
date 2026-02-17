# Get offer details

**Endpoint:** `GET /offers/{id}`

**Roles:** Authenticated / Admin

## Success Response

**Status:** 200 OK

```json
{
  "id": "f4b0c442-98fc-1c14-9afb-4c4e6c2e2a8c",
  "merchant_name": "CoolShop",
  "cashback_type": "percent",
  "cashback_value": 10,
  "monthly_cap": 50,
  "start_date": "2026-02-01T00:00:00Z",
  "end_date": "2026-12-31T23:59:59Z",
  "status": "active"
}
```

## Failure Responses

- **404 Not Found** – offer does not exist
- **403 Forbidden** – user not authorized
