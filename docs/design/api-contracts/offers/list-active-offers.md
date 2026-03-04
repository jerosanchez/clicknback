# List active offers for users

**Endpoint:** `GET /offers/active`

**Roles:** Authenticated (any valid user)

## Query Parameters

- `page` (optional, integer, default `1`, min `1`): Page number, 1-indexed.
- `page_size` (optional, integer, default `default_page_size`, min `1`, max `max_page_size`): Number of results per page.

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
      "start_date": "2026-02-01",
      "end_date": "2026-12-31"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

## Filtering Logic

The endpoint applies all three conditions simultaneously (AND logic):

1. `Offer.active = true` — the offer must be explicitly activated
2. `Merchant.active = true` — the offer's merchant must be active
3. `Offer.start_date ≤ today ≤ Offer.end_date` — the offer must be within its valid date range (server UTC date)

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

### 422 Unprocessable Entity – Invalid Pagination Parameters

```json
{
  "error": {
    "code": "UNPROCESSABLE_ENTITY",
    "message": "Request validation failed.",
    "details": {}
  }
}
```
