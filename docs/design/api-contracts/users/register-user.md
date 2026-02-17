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

- **409 Conflict** – email already registered

  ```json
  { "detail": "Email already registered." }
  ```

- **422 Unprocessable Entity** – password not complex enough

  ```json
  { "detail": "Password must contain at least one special character." }
  ```
