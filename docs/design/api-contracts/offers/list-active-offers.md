# List active offers for users

**Endpoint:** `GET /offers/active`

**Roles:** Authenticated

## Success Response

**Status:** 200 OK

```json
{
  "offers": [
    {
      "id": "f4b0c442-98fc-1c14-9afb-4c4e6c2e2a8c",
      "merchant_name": "CoolShop",
      "cashback_type": "percent",
      "cashback_value": 10,
      "monthly_cap": 50,
      "start_date": "2026-02-01T00:00:00Z",
      "end_date": "2026-12-31T23:59:59Z"
    }
  ]
}
```

## Failure Responses

### 401 Unauthorized – Missing Authentication

```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Authentication token is missing or invalid.",
    "details": {
      "issue": "Token expired or malformed",
      "action": "Include a valid Bearer token in the Authorization header."
    }
  }
}
```
