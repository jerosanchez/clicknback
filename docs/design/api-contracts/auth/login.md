# Authenticate user, return JWT

**Endpoint:** `POST /api/v1/auth/login`

**Roles:** Anonymous

## Request

```json
{
  "email": "alice@example.com",
  "password": "S3cureP@ss!"
}
```

## Success Response

**Status:** 200 OK

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6...",
  "token_type": "bearer"
}
```

**Field Descriptions:**

| Field | Type | Description |
| --- | --- | --- |
| `access_token` | string | Short-lived JWT access token (15 min default) |
| `refresh_token` | string | Long-lived refresh token (30 days default) for obtaining new access tokens |
| `token_type` | string | Always "bearer" |

## Failure Responses

### 400 Bad Request – Validation Error

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed for request body.",
    "details": {
      "violations": [
        {
          "field": "email",
          "reason": "Email is required."
        },
        {
          "field": "password",
          "reason": "Password is required."
        }
      ]
    }
  }
}
```

### 401 Unauthorized – Invalid Credentials

```json
{
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Email or password is incorrect. Please check your credentials and try again.",
    "details": {}
  }
}
```

### 500 Internal Server Error

```json
{
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "An unexpected error occurred. Our team has been notified. Please retry later.",
    "details": {
      "request_id": "not available",
      "timestamp": "2026-04-05T13:00:00Z"
    }
  }
}
```
