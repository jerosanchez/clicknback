# Create a merchant

**Endpoint:** `POST /merchants`

**Roles:** Admin

## Request

```json
{
  "name": "CoolShop",
  "default_cashback_pct": 5
}
```

## Success Response

**Status:** 201 Created

```json
{
  "id": "e3b0c442-98fc-1c14-9afb-4c4e6c2e2a8c",
  "name": "CoolShop",
  "default_cashback_pct": 5,
  "status": "active"
}
```

## Failure Responses

- **400 Bad Request** – missing fields
- **403 Forbidden** – non-admin
