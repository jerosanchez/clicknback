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

### 401 Unauthorized – Expired Access Token

**When:** Access token has expired

```json
{
  "error": {
    "code": "EXPIRED_TOKEN",
    "message": "Access token has expired. Please refresh your token.",
    "details": {}
  }
}
```

### 401 Unauthorized – Invalid Token

**When:** Token is malformed, tampered, or has invalid signature

```json
{
  "error": {
    "code": "INVALID_TOKEN",
    "message": "Invalid or malformed authentication token.",
    "details": {}
  }
}
```

### 401 Unauthorized – User Inactive

**When:** Token is valid but the user account is inactive (disabled/suspended)

```json
{
  "error": {
    "code": "USER_INACTIVE",
    "message": "User account is inactive.",
    "details": {
      "user_id": "b7e6c2e2-8c2a-4e2a-9b1a-2e6c2e2a8c2a"
    }
  }
}
```
