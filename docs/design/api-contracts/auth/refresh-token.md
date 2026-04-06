# Refresh Access Token

**Endpoint:** `POST /api/v1/auth/refresh`

**Roles:** Anonymous (public endpoint)

**Related Spec:** [JWT Refresh Token Support - Issue #72](https://github.com/jerosanchez/clicknback/issues/72)

## Request

**Body (application/json):**

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Field Descriptions:**

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `refresh_token` | string | ✅ | Valid refresh token obtained from login or previous refresh |

**Example:**

```bash
curl -X POST http://localhost:8001/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

## Success Response

**Status Code:** `200 OK`

**Response Body (application/json):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Field Descriptions:**

| Field | Type | Description |
| --- | --- | --- |
| `access_token` | string | New short-lived JWT access token (15 min default) |
| `refresh_token` | string | New refresh token for future refreshes (30 days default); old token is invalidated |
| `token_type` | string | Always "bearer" |

## Failure Responses

### 400 Bad Request – Validation Error

**When:** Request body is malformed or `refresh_token` field is missing

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed for request body.",
    "details": {
      "violations": [
        {
          "field": "refresh_token",
          "reason": "refresh_token is required."
        }
      ]
    }
  }
}
```

### 401 Unauthorized – Invalid Refresh Token

**When:** Refresh token is invalid (tampered, malformed, or wrong token type)

```json
{
  "error": {
    "code": "INVALID_REFRESH_TOKEN",
    "message": "Invalid or malformed refresh token.",
    "details": {}
  }
}
```

### 401 Unauthorized – Expired Refresh Token

**When:** Refresh token has passed its expiration time (30 days)

```json
{
  "error": {
    "code": "EXPIRED_REFRESH_TOKEN",
    "message": "Refresh token has expired. Please log in again.",
    "details": {}
  }
}
```

### 401 Unauthorized – Token Revoked

**When:** Refresh token was already used in a previous refresh (single-use enforcement) and has been revoked

```json
{
  "error": {
    "code": "TOKEN_REVOKED",
    "message": "Refresh token has been revoked. Please log in again.",
    "details": {}
  }
}
```

### 500 Internal Server Error

**When:** Unexpected server error

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

## Implementation Details

**Token Rotation (Single-Use):**

- Each successful refresh invalidates the old refresh token and returns a new one
- Attempting to reuse an old refresh token results in a 401 error
- This prevents token replay attacks and constrains the window for token theft

**Access Token Lifecycle:**

- Access tokens are short-lived (15 minutes by default)
- Refresh tokens are long-lived (30 days by default)
- Users can maintain long-lived sessions (30+ days) by periodically refreshing before access token expiration

**Concurrency Safety:**

- Multiple concurrent refresh requests are handled correctly
- Database constraints prevent duplicate token usage
- Clients should implement exponential backoff on 401 responses
