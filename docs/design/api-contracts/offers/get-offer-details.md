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

### 403 Forbidden – Insufficient Permissions

```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "You do not have permission to view this offer.",
    "details": {
      "resource_type": "offer",
      "resource_id": "f4b0c442-98fc-1c14-9afb-4c4e6c2e2a8c",
      "reason": "Only admin users and merchants can view inactive offers."
    }
  }
}
```

### 404 Not Found – Offer Does Not Exist

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Offer with ID 'f4b0c442-98fc-1c14-9afb-4c4e6c2e2a8c' does not exist.",
    "details": {
      "resource_type": "offer",
      "resource_id": "f4b0c442-98fc-1c14-9afb-4c4e6c2e2a8c"
    }
  }
}
```
