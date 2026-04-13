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
  "data": [
    {
      "id": "c1b2c3d4-5678-90ab-cdef-1234567890ab",
      "type": "cashback_credit",
      "amount": 10.05,
      "status": "available",
      "related_purchase_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab"
    },
    {
      "id": "d2c3d4e5-6789-01bc-defa-2345678901bc",
      "type": "cashback_credit",
      "amount": 5.00,
      "status": "reversed",
      "related_purchase_id": "b2c3d4e5-6789-01bc-defa-2345678901bc"
    }
  ],
  "pagination": {
    "offset": 0,
    "limit": 10,
    "total": 2
  }
}
```

### Response fields

| Field | Type | Description |
| --- | --- | --- |
| `data` | array | Ordered newest-first. |
| `data[].id` | UUID | Cashback transaction ID. |
| `data[].type` | string | Always `cashback_credit`. Future releases may add `payout_deduction`. |
| `data[].amount` | decimal | Cashback amount, always positive. |
| `data[].status` | string | Lifecycle state: `pending` (awaiting purchase confirmation), `available` (confirmed, in spendable balance), or `reversed` (purchase was reversed, cashback clawed back). |
| `data[].related_purchase_id` | UUID | The purchase this cashback was earned from. |
| `pagination.total` | integer | Total number of transactions for the user across all pages. |
| `pagination.offset` | integer | The current pagination offset. |
| `pagination.limit` | integer | The current page size limit. |

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

### 422 Unprocessable Entity – Invalid Query Parameters

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid query parameters.",
    "details": {
      "violations": [
        {
          "field": "limit",
          "reason": "Limit must be a positive integer between 1 and 100."
        },
        {
          "field": "offset",
          "reason": "Offset must be a non-negative integer."
        }
      ]
    }
  }
}
```

### 500 Internal Server Error

```json
{
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "An unexpected error occurred. Our team has been notified. Please retry later.",
    "details": {}
  }
}
```
