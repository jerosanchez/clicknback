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
          "reason": "Invalid email format."
        },
        {
          "field": "password",
          "reason": "Password must be at least 12 characters."
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
    "message": "Email 'alice@example.com' is already registered. Use a different email or recover your account.",
    "details": {
      "email": "alice@example.com",
      "timestamp": "2026-02-17T14:33:22Z"
    }
  }
}
```

### 422 Unprocessable Entity – Password Not Complex Enough

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Password does not meet complexity requirements.",
    "details": {
      "field": "password",
      "violations": [
        "Password must be at least 12 characters.",
        "Must contain at least one special character (e.g., !@#$%^&*).",
        "Must contain at least one uppercase letter.",
        "Must contain at least one digit."
      ]
    }
  }
}
```
