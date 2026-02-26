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
**Given** I have correct email and password
**When** the user account exists and credentials are valid
**Then** a valid JWT token is issued

**Scenario:** Authentication with non-existent user
**Given** I attempt to login with an email that is not registered
**When** the system attempts to validate credentials
**Then** an authentication error is returned

**Scenario:** Authentication with incorrect password
**Given** I attempt to login with correct email but wrong password
**When** the system validates the password
**Then** an authentication error is returned

**Scenario:** Authentication with invalid email format
**Given** I attempt to login with an invalid email format
**When** the API validates the input
**Then** a validation error is returned

---

## Use Cases

### Happy Path

A registered user successfully authenticates with valid credentials via the auth module:

1. User submits email and password.
2. System validates email format.
3. System retrieves user by email.
4. System validates credentials against stored hash.
5. System issues access token.
6. System returns the access token.

### Sad Paths

#### Invalid Email Format

1. User submits invalid email and password.
2. System validates email format.
3. System detects invalid email format.
4. System rejects the request with validation error.

#### Non-Existent User

1. User submits email and password.
2. System validates email format.
3. System attempts to retrieve user by email.
4. System finds user does not exist.
5. System rejects the request with authentication error.

#### Incorrect Password

1. User submits correct email and incorrect password.
2. System validates email format.
3. System retrieves user by email.
4. System validates password against stored hash.
5. System finds password does not match.
6. System rejects the request with authentication error.

## API Contract

- [Authenticate user, return JWT](../../../design/api-contracts/auth/login.md)
