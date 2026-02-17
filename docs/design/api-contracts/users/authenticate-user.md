# Authenticate user, return JWT

**Endpoint:** `POST /users/login`

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
  "token_type": "Bearer",
  "expires_in": 3600
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
    "code": "UNAUTHORIZED",
    "message": "Email or password is incorrect. Please check your credentials and try again.",
    "details": {
      "issue": "Authentication failed",
      "action": "Verify your email and password. If you forgot your password, use the password recovery option."
    }
  }
}
```
