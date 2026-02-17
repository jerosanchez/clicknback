# User Registration

IMPORTANT: This is a living document, specs are subject to change.

## User Story

_As a new user, I want to register so that I can create an account and access the platform._

---

## Constraints

### Password Constraints

- Minimum length: 8 characters
- Must contain at least one uppercase letter
- Must contain at least one lowercase letter
- Must contain at least one digit
- Must contain at least one special character (e.g., !@#$%^&*)

### Email Constraints

- Must be a valid email address format
- Must be unique in the system

---

## BDD Acceptance Criteria

**Scenario:** Successful registration with valid credentials
**Given** I send a `POST /api/v1/users` request with a valid email and password
**When** the email is not already registered and password meets complexity requirements
**Then** the API responds with `HTTP 201 Created` and returns the new user information

**Scenario:** Registration with already registered email
**Given** I send a `POST /api/v1/users` request with an email that is already registered
**When** the API processes the request
**Then** the API responds with `HTTP 409 Conflict` and an error message indicating the email is already in use

**Scenario:** Registration with invalid email format
**Given** I send a `POST /api/v1/users` request with an invalid email format
**When** the API validates the input
**Then** the API responds with `HTTP 400 Bad Request` and an error message describing the issue

**Scenario:** Registration with password not meeting complexity requirements
**Given** I send a `POST /api/v1/users` request with a password that does not meet security requirements
**When** the API validates the password
**Then** the API responds with `HTTP 422 Unproccesable Content` and an error message describing the password requirements

---

## Use Cases

### Happy Path

A new user successfully registers with valid email and password

1. User submits email and password.
2. System validates email format.
3. System validates password complexity.
4. System enforces unique email constraint.
5. System hashes password.
6. System creates user record.
7. System returns `HTTP 201 Created` with new user info.

### Sad Paths

#### Duplicate Email Registration

1. User submits email and password.
2. System validates email format.
3. System checks if email already exists.
4. System finds email is already registered.
5. System returns `HTTP 409 Conflict` with error message.

#### Invalid Email Format

1. User submits invalid email and password.
2. System validates email format.
3. System detects invalid email format.
4. System returns `HTTP 400 Bad Request` with validation error.

#### Weak Password

1. User submits valid email and weak password.
2. System validates email format.
3. System enforces password complexity.
4. System detects password does not meet requirements.
5. System returns `HTTP 422 Unprocessable Content` with password requirements error.

## API Contract

See [Register a new user](../../design/api-contracts/users/register-user.md) for detailed API specifications.
