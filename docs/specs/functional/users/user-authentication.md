# User Login

IMPORTANT: This is a living document, specs are subject to change.

## User Story

_As a registered user, I want to authenticate using my email and password so that I can obtain an access token and use the platform._

---

## Constraints

### Authentication Constraints

- User account must exist and be active
- Credentials must be validated against stored hash
- JWT token must be issued with appropriate expiration
- Password must match the stored hash exactly

---

## BDD Acceptance Criteria

**Scenario:** Successful authentication with valid credentials
**Given** I send a `POST /api/v1/users/authenticate` request with correct email and password
**When** the user account exists and credentials are valid
**Then** the API responds with `HTTP 200 OK` and returns a valid JWT token

**Scenario:** Authentication with non-existent user
**Given** I send a `POST /api/v1/users/authenticate` request with an email that is not registered
**When** the system attempts to validate credentials
**Then** the API responds with `HTTP 401 Unauthorized` and an error message

**Scenario:** Authentication with incorrect password
**Given** I send a `POST /api/v1/users/authenticate` request with correct email but wrong password
**When** the system validates the password
**Then** the API responds with `HTTP 401 Unauthorized` and an error message

**Scenario:** Authentication with invalid email format
**Given** I send a `POST /api/v1/users/authenticate` request with an invalid email format
**When** the API validates the input
**Then** the API responds with `HTTP 400 Bad Request` and an error message

---

## Use Cases

### Happy Path

A registered user successfully authenticates with valid credentials

1. User submits email and password.
2. System validates email format.
3. System retrieves user by email.
4. System validates credentials against stored hash.
5. System issues JWT token.
6. System returns `HTTP 200 OK` with access token.

### Sad Paths

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

#### Invalid Email Format

1. User submits invalid email and password.
2. System validates email format.
3. System detects invalid email format.
4. System returns `HTTP 400 Bad Request` with validation error.

## API Contracts

- [Authenticate user, return JWT](../../design/api-contracts/users/authenticate-user.md) for login specifications
- [Get current authenticated user info](../../design/api-contracts/users/get-current-user.md) for retrieving user details
