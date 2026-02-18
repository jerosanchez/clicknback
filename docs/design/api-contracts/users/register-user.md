# Register a new user

**Endpoint:** `POST /users/register`

**Roles:** Anonymous

## Request

```json
{
  "email": "alice@example.com",
  "password": "S3cureP@ss!"
}
```

## Success Response

**Status:** 201 Created

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

### 400 Bad Request – Password Not Complex Enough

```json
{
  "error": {
    "code": "PASSWORD_NOT_COMPLEX_ENOUGH",
    "message": "Validation failed for request body.",
    "details": {
      "violations": [
        {
          "field": "password",
          "reason": "Password must be at least 8 characters long."
        }
      ]
    }
  }
}
```

### 409 Conflict – Email Already Registered

```json
{
  "error": {
    "code": "EMAIL_ALREADY_REGISTERED",
    "message": "Email 'alice@example.com' is already registered.",
    "details": {
      "email": "alice@example.com"
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
    "details": {
      "request_id": "not available",
      "timestamp": "2026-02-17T14:33:22Z"
    }
  }
}
```
