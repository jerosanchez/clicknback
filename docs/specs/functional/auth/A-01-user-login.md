# A-01: User Login

IMPORTANT: This is a living document, specs are subject to change.

## User Story

_As a registered user, I want to authenticate using my email and password so that I can obtain an access token and use the platform._

---

## Constraints

### Authentication Constraints

> **Note:** This functional requirement does not currently include scenarios for account lockout (e.g., too many failed attempts, 423 Locked) or rate limiting (429 Too Many Requests) to keep the implementation simple. These may be added in the future as security requirements evolve.

## BDD Acceptance Criteria

**Scenario:** Successful authentication with valid credentials
**Given** I send a login request with correct email and password
**When** the user account exists and credentials are valid
**Then** the API responds successfully and returns a valid JWT token

**Scenario:** Authentication with non-existent user
**Given** I send a login request with an email that is not registered
**When** the system attempts to validate credentials
**Then** the API responds with an error code and returns a message

**Scenario:** Authentication with incorrect password
**Given** I send a login request with correct email but wrong password
**When** the system validates the password
**Then** the API responds with an error code an returns a message

**Scenario:** Authentication with invalid email format
**Given** I send a login request with an invalid email format
**When** the API validates the input
**Then** the API responds with an error code and returns a message

---

## Use Cases

### Happy Path

A registered user successfully authenticates with valid credentials via the auth module:

1. User submits email and password.
2. System validates email format.
3. System retrieves user by email.
4. System validates credentials against stored hash.
5. System issues access token.
6. System returns `HTTP 200 OK` with access token.

### Sad Paths

#### Invalid Email Format

1. User submits invalid email and password.
2. System validates email format.
3. System detects invalid email format.
4. System returns `HTTP 400 Bad Request` with validation error.

#### Non-Existent User

1. User submits email and password.
2. System validates email format.
3. System attempts to retrieve user by email.
4. System finds user does not exist.
5. System returns `HTTP 401 Unauthorized` with error message.

#### Incorrect Password

1. User submits correct email and incorrect password.
2. System validates email format.
3. System retrieves user by email.
4. System validates password against stored hash.
5. System finds password does not match.
6. System returns `HTTP 401 Unauthorized` with error message.

## API Contract

- [Authenticate user, return JWT](../../../design/api-contracts/auth/login.md)
