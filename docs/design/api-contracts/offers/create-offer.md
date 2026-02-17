# Create cashback offer

**Endpoint:** `POST /offers`

**Roles:** Admin

## Request

```json
{
  "merchant_id": "e3b0c442-98fc-1c14-9afb-4c4e6c2e2a8c",
  "cashback_type": "percent",
  "cashback_value": 10,
  "start_date": "2026-02-01T00:00:00Z",
  "end_date": "2026-12-31T23:59:59Z",
  "monthly_cap": 50
}
```

## Success Response

**Status:** 201 Created

```json
{
  "id": "f4b0c442-98fc-1c14-9afb-4c4e6c2e2a8c",
  "merchant_id": "e3b0c442-98fc-1c14-9afb-4c4e6c2e2a8c",
  "cashback_type": "percent",
  "cashback_value": 10,
  "status": "active"
}
```

## Failure Responses

- **400 Bad Request** – invalid fields
- **403 Forbidden** – non-admin
