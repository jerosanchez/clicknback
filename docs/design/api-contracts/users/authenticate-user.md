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

- **401 Unauthorized** – wrong credentials

  ```json
  { "error": "Invalid email or password" }
  ```
