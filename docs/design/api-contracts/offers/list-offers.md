# List Offers

**Endpoint:** `GET /api/v1/offers`

**Roles:** Any authenticated user (User, Admin)

**Related Spec:** [O-05 Offers Listing](../../../specs/functional/offers/O-05-offers-listing.md)

## Request

**Path Parameters:** (none)

**Query Parameters:**

| Parameter | Type | Required | Description |
| --------- | ---- | -------- | ----------- |
| `offset` | integer | No | Number of results to skip. Default: `0`. Minimum: `0`. |
| `limit` | integer | No | Results per page. Default: `20`. Range: `1`–`100`. |
| `status` | string | No | Filter by offer status. One of: `active`, `inactive`. |
| `merchant_id` | string (UUID) | No | Return only offers for this merchant. |
| `date_from` | string (ISO 8601 date) | No | Return offers whose validity window ends on or after this date. |
| `date_to` | string (ISO 8601 date) | No | Return offers whose validity window starts on or before this date. |

**Authentication:**

Bearer token (JWT). Include `Authorization: Bearer <token>` header.

**Example:**

```bash
curl -X GET "http://localhost:8001/api/v1/offers?offset=0&limit=20&status=active" \
  -H "Authorization: Bearer <token>"
```

---

## Success Response

**Status Code:** `200 OK`

**Response Body (application/json):**

```json
{
  "data": [
    {
      "id": "f4b0c442-98fc-1c14-9afb-4c4e6c2e2a8c",
      "merchant_id": "e3b0c442-98fc-1c14-9afb-4c4e6c2e2a8c",
      "cashback_type": "percent",
      "cashback_value": 10.0,
      "start_date": "2026-01-01",
      "end_date": "2026-12-31",
      "monthly_cap_per_user": 50.0,
      "status": "active"
    }
  ],
  "pagination": {
    "offset": 0,
    "limit": 20,
    "total": 1
  }
}
```

**Field Descriptions:**

| Field | Type | Description |
| ----- | ---- | ----------- |
| `data[].id` | UUID | Unique offer ID |
| `data[].merchant_id` | UUID | Merchant this offer belongs to |
| `data[].cashback_type` | string | `percent` or `fixed` |
| `data[].cashback_value` | number | Cashback percentage or fixed EUR amount |
| `data[].start_date` | ISO 8601 date | First day the offer is valid |
| `data[].end_date` | ISO 8601 date | Last day the offer is valid |
| `data[].monthly_cap_per_user` | number | Maximum cashback per user per month (EUR) |
| `data[].status` | string | `active` or `inactive` |
| `pagination.offset` | integer | Number of results skipped |
| `pagination.limit` | integer | Page size used |
| `pagination.total` | integer | Total matching records across all pages |

Returns an empty `data` array when no offers match the filters.

---

## Failure Responses

### 400 Bad Request — Invalid Query Parameters

**When:** `status` is not `active` or `inactive`; or `date_from` is after `date_to`.

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid query parameters.",
    "details": {
      "violations": [
        {
          "field": "status",
          "reason": "Status must be one of: active, inactive."
        }
      ]
    }
  }
}
```

Multiple violations may be returned in a single response.

### 401 Unauthorized — Missing or Invalid Token

**When:** No `Authorization` header, expired token, revoked token, or invalid token.

```json
{
  "error": {
    "code": "INVALID_TOKEN",
    "message": "Invalid token, or user does not have permissions to perform this action.",
    "details": {}
  }
}
```

Other 401 codes: `EXPIRED_TOKEN`, `TOKEN_REVOKED`, `USER_INACTIVE`.

### 422 Unprocessable Entity — Parameter Type Validation Failed

**When:** A query parameter has the wrong type (e.g. `offset=abc`, `merchant_id=not-a-uuid`, `offset=-1`).

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed.",
    "details": {
      "violations": [
        {
          "field": "offset",
          "reason": "Input should be greater than or equal to 0"
        }
      ]
    }
  }
}
```

### 500 Internal Server Error

**When:** Unexpected server error.

```json
{
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "An unexpected error occurred. Our team has been notified. Please retry later.",
    "details": {
      "request_id": "not available",
      "timestamp": "2026-04-21T10:00:00.000000"
    }
  }
}
```
