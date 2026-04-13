# List all purchases (Admin)

**Endpoint:** `GET /purchases`

**Roles:** Admin (valid Bearer token with `admin` role required)

## Query Parameters

| Parameter | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| `status` | string | No | — | One of: `pending`, `confirmed`, `reversed` |
| `user_id` | string (UUID) | No | — | Valid UUID; unrecognised IDs return an empty list |
| `merchant_id` | string (UUID) | No | — | Valid UUID; unrecognised IDs return an empty list |
| `start_date` | string (date) | No | — | ISO 8601 format (`YYYY-MM-DD`); inclusive lower bound on `created_at` |
| `end_date` | string (date) | No | — | ISO 8601 format (`YYYY-MM-DD`); inclusive upper bound on `created_at` |
| `offset` | integer | No | `0` | Must be ≥ 0 |
| `limit` | integer | No | `10` | Must be between 1 and 100 (inclusive) |

**Example:** `?status=confirmed&start_date=2026-01-01&end_date=2026-03-31&offset=0&limit=10`

Results are ordered by `created_at` descending (newest first).

## Success Response

**Status:** 200 OK

```json
{
  "data": [
    {
      "id": "aa000001-0000-0000-0000-000000000005",
      "external_id": "txn_seed_005",
      "user_id": "b7e2c1a2-4f3a-4e2b-9c1a-8d2e3f4b5c6d",
      "merchant_id": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
      "offer_id": "f0e1d2c3-b4a5-4678-9012-3456789abcde",
      "amount": "300.00",
      "currency": "EUR",
      "status": "confirmed",
      "created_at": "2026-02-27T10:00:00"
    }
  ],
  "pagination": {
    "offset": 0,
    "limit": 10,
    "total": 1
  }
}
```

**Notes:**

- `offer_id` may be `null` if no active offer was matched at ingestion time.
- `pagination.total` reflects the total number of purchases matching the applied filters, not just the current page.
- `data` is an empty array when no purchases match the filters; this is not an error.

## Failure Responses

### 401 Unauthorized – Missing or Invalid Authentication

Returned when the request has no Bearer token, the token is expired, or the authenticated user is
not an admin.

```json
{
  "error": {
    "code": "INVALID_TOKEN",
    "message": "Invalid or expired token, or user has not the permissions to perform this action.",
    "details": {}
  }
}
```

### 422 Unprocessable Entity – Invalid Pagination Parameters

Returned when `offset` or `limit` violate their numeric constraints.

```json
{
  "detail": [
    {
      "type": "greater_than_equal",
      "loc": ["query", "offset"],
      "msg": "Input should be greater than or equal to 0",
      "input": "-1"
    }
  ]
}
```

> **Note:** Pagination constraint errors are returned in FastAPI's native Pydantic
> format (HTTP 422). The custom error envelope applies to domain-level errors only.
