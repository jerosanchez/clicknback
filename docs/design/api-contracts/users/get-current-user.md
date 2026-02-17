# Get current authenticated user info

**Endpoint:** `GET /users/me`

**Roles:** Authenticated (JWT required)

## Request Headers

- `Authorization: Bearer <token>`

## Success Response

**Status:** 200 OK

```json
{
  "id": "b7e6c2e2-8c2a-4e2a-9b1a-2e6c2e2a8c2a",
  "email": "alice@example.com",
  "active": true,
  "role": "user",
  "created_at": "2026-02-13T12:00:00Z"
}
```

## Failure Responses

### 401 Unauthorized – Missing or Invalid Token

```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Authentication token is missing or invalid.",
    "details": {
      "issue": "Token expired or malformed",
      "action": "Re-authenticate to obtain a fresh token."
    }
  }
}
```
