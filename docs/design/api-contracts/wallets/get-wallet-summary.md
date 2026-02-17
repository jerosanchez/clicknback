# Get wallet summary

**Endpoint:** `GET /users/wallet`

**Roles:** Authenticated

## Success Response

**Status:** 200 OK

```json
{
  "pending_balance": 5.00,
  "available_balance": 25.50,
  "paid_balance": 100.00
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
