# A-02: Refresh Access Token

IMPORTANT: This is a living document. Specifications are subject to change.

## User Story

_As an authenticated user with an expired or expiring access token, I want to refresh my access token using a refresh token so that I can continue using the platform without having to log in again._

---

## Constraints

### Token Lifecycle

- Access tokens are short-lived (15 minutes by default).
- Refresh tokens are long-lived (30 days by default).
- Refresh tokens are single-use; each successful refresh invalidates the old refresh token and returns a new one.
- Old refresh tokens (after use) cannot be reused; attempting to reuse results in a 401 Unauthorized error.

### Validation

- Request must include a valid `refresh_token` field.
- Refresh token must not be expired.
- Refresh token must not have been previously used (single-use enforcement).

### Security

- Token rotation prevents token replay attacks and limits the window for token theft.
- Multiple concurrent refresh requests are handled safely using database constraints.
- Clients should implement exponential backoff on 401 responses.

### Authorization

- Public endpoint; no authentication header required.
- Any caller with a valid refresh token can obtain a new access token.

---

## Acceptance Criteria

### Happy Path Scenario: Valid Refresh Token

**Given:** A user has a valid, non-expired, unused refresh token  
**When:** POST `/api/v1/auth/refresh` with the refresh token in the request body  
**Then:** HTTP 200 with new access token, new refresh token, and token_type="bearer"

### Failure Mode 1: Missing Refresh Token Field

**Given:** A valid user has a refresh token  
**When:** POST `/api/v1/auth/refresh` without the `refresh_token` field  
**Then:** HTTP 400 VALIDATION_ERROR with violations detail

### Failure Mode 2: Malformed Request Body

**Given:** A request is made with invalid JSON  
**When:** POST `/api/v1/auth/refresh` with malformed body  
**Then:** HTTP 400 VALIDATION_ERROR

### Failure Mode 3: Invalid Refresh Token

**Given:** A user attempts refresh with a token that is not a valid JWT or wrong token type  
**When:** POST `/api/v1/auth/refresh` with invalid token string  
**Then:** HTTP 401 INVALID_REFRESH_TOKEN

### Failure Mode 4: Expired Refresh Token

**Given:** A refresh token has passed its expiration time (30 days)  
**When:** POST `/api/v1/auth/refresh` with the expired token  
**Then:** HTTP 401 EXPIRED_REFRESH_TOKEN

### Failure Mode 5: Previously Used Refresh Token (Single-Use Enforcement)

**Given:** A refresh token was already successfully used in a previous refresh operation  
**When:** POST `/api/v1/auth/refresh` with the old (used) refresh token  
**Then:** HTTP 401 TOKEN_REVOKED

---

## Use Cases

### Happy Path: Token Refresh

1. User has a valid, non-expired, unused refresh token (obtained from login or previous refresh).
2. User submits refresh token via POST `/api/v1/auth/refresh`.
3. System validates the token format (valid JWT).
4. System checks if the token is expired.
5. System checks if the token has been previously used (single-use enforcement).
6. System marks the old refresh token as used (invalidates it).
7. System generates a new access token (15 min lifetime).
8. System generates a new refresh token (30 day lifetime).
9. System returns both tokens with `token_type="bearer"`.
10. User receives HTTP 200 with new tokens and can use the new access token for subsequent requests.

### Sad Path: Token Already Used

1. User attempts to refresh with a refresh token that was already used in a previous refresh.
2. System validates the token format (valid JWT).
3. System checks if the token has been previously used.
4. System detects the token is already marked as used.
5. System rejects the request with HTTP 401 INVALID_REFRESH_TOKEN.
6. User receives error and must log in again.

### Sad Path: Expired Token

1. User attempts to refresh with a refresh token that has passed its 30-day expiration.
2. System validates the token format (valid JWT).
3. System checks if the token is expired by comparing the `exp` claim to current time.
4. System detects the token is expired.
5. System rejects the request with HTTP 401 INVALID_REFRESH_TOKEN.
6. User receives error and must log in again.

---

## API Contract

[Refresh Access Token (API contract)](../../design/api-contracts/auth/refresh-token.md)
