# Feature Architecture

This document describes how feature modules are organized and designed. It covers module anatomy, layer responsibilities, design patterns, and cross-cutting concerns. For step-by-step implementation instructions, see [build-feature.prompt.md](.github/prompts/build-feature.prompt.md).

---

## 1. Module Anatomy

Every feature lives in its own package under `app/`. Each module follows a consistent layered structure:

```text
app/<feature>/
  __init__.py          ← Empty; marks the package
  models.py            ← SQLAlchemy ORM models (DB tables)
  schemas.py           ← Pydantic schemas (API input/output)
  repositories.py      ← DB access layer (ABC + concrete impl)
  services.py          ← Business logic orchestration
  policies.py          ← Pure business rule enforcement functions
  exceptions.py        ← Domain-specific exceptions (no HTTP knowledge)
  errors.py            ← Module-specific ErrorCode enum (HTTP error codes)
  composition.py       ← Dependency wiring (FastAPI Depends factories)
  api.py               ← FastAPI router (HTTP layer only); or api/ package when split
  clients/             ← Cross-module client abstractions (only when needed)
    __init__.py        ← Re-exports all DTOs, ABCs, and concrete clients
    <foreign>.py       ← One file per collaborating module (e.g., users.py, merchants.py)
```

Not every module needs all files (e.g., `auth` has no `repositories.py` — it delegates to `users` via a client). The `clients/` package is only present when the module reads data owned by another module.

As a module grows, individual files may be replaced by packages (e.g., `api/`, `services/`, `schemas/`). For the full decision framework — thresholds, split strategies, naming conventions, and the decoupling rules — see `docs/guidelines/code-organization.md`.

### Layer Responsibilities

Each layer has a clearly defined responsibility and boundary. This separation ensures that code is testable, maintainable, and follows the Dependency Inversion Principle.

#### `models.py` – ORM Models

Defines the data schema using SQLAlchemy. Models are the single source of truth for table structure. All models must be imported in `app/models.py` so Alembic's autogenerate feature can detect schema changes. Schema changes are tracked as migrations under `alembic/versions/`.

#### `schemas.py` – Pydantic Input/Output Schemas

Defines the API contract for request payloads and response bodies. Separates API concerns from persistence concerns — what the API accepts and returns is decoupled from how data is stored. Validators enforce field-level and cross-field constraints. ORM models are never returned directly; they are converted to schema instances before being sent to clients.

#### `repositories.py` – Data Access Layer

Encapsulates all database queries. Only this layer knows SQL or SQLAlchemy internals. Two classes per entity: an abstract interface (`<Entity>RepositoryABC`) and a concrete implementation (`<Entity>Repository`).

- **Interface segregation:** The abstract class defines the contract; concrete implementations satisfy it. This enables unit tests to mock repositories without touching the DB.
- **No business logic:** Repositories query, insert, update, and delete — nothing more. Validation and decision-making belong in `policies.py` and `services.py`.
- **Async by default:** New modules use `AsyncSession` and `async def` methods (see [ADR-010](../design/adr/010-async-database-layer.md)).

#### `policies.py` – Business Rule Enforcement

Pure functions that validate business invariants. Each function enforces exactly one rule. They raise domain exceptions on violation and return `None` on success. No side effects, no I/O.

Design benefits:

- **Testability:** Test business rules in isolation without mocking or DB fixtures.
- **Reusability:** The same rule can be called from multiple services or other code paths.
- **Clarity:** Business logic is explicit and easy to locate.

#### `exceptions.py` – Domain Exceptions

Plain Python exceptions representing domain-specific failure modes. They carry context as instance attributes (e.g., `self.email` in `EmailAlreadyRegisteredException`). No HTTP or FastAPI knowledge.

Exceptions flow from `services.py` → `api.py` → `core/errors/builders.py`, where they are converted to HTTP responses. This ensures the domain layer remains agnostic to transport concerns.

#### `errors.py` – Module Error Codes

A string enum of semantic error codes specific to this module's HTTP responses (e.g., `PASSWORD_NOT_COMPLEX_ENOUGH`, `EMAIL_ALREADY_REGISTERED`). Separate from `core/errors/codes.py`, which holds global codes.

#### `composition.py` – Dependency Injection

Factory functions used with FastAPI's `Depends()` that assemble and wire all dependencies for services, repositories, and other components. This is the single place where concrete implementations are instantiated and connected.

Benefits:

- **Testability:** Tests override dependencies by providing mocks to the factories.
- **Clarity:** The application's wiring is explicit and centralized.
- **Modularity:** Swapping implementations (e.g., replacing a concrete client with an HTTP client) requires changes only here.

#### `api.py` – HTTP Router

The HTTP boundary layer. Route handlers:

1. Declare request/response schemas and status codes.
2. Resolve dependencies via `Depends()`.
3. Call services or repositories.
4. Catch domain exceptions and convert them to HTTP responses using `core/errors/builders.py`.
5. Catch unexpected exceptions, log errors, and raise generic `internal_server_error()`.

**Design principle: No business logic in routes.** The handler translates between HTTP and the domain model; orchestration belongs in services.

As routes accumulate (typically when `api.py` exceeds ~200 lines), split into an `api/` sub-package with per-feature routers. See `docs/guidelines/code-organization.md` §3 for conventions.

#### `clients/` – Cross-Module Data Access (when needed)

When this module needs to read data owned by another module, instead of importing that module's ORM models directly, create a `clients/` package. This package contains:

- **DTOs** (plain `@dataclass`): Lightweight representations of foreign data carrying only the fields needed.
- **Abstract client** (`<Foreign>ClientABC`): Interface defining the contract.
- **Concrete implementation** (`<Foreign>Client`): Queries the shared DB and returns DTOs.

This pattern isolates cross-module coupling to the `clients/` package. If a collaborating module is extracted into a microservice, only its concrete client changes; services and repositories remain untouched.

---

## 2. Cross-Cutting Concerns – The `core` Module

`app/core/` houses shared infrastructure used by all feature modules and handles concerns that don't belong to any single domain feature.

### Configuration (`core/config.py`)

Centralized settings loaded from environment variables. All configuration is read here; feature modules import `settings` to access it. This ensures a single source of truth for all runtime configuration.

### Database (`core/database.py`)

Provides the SQLAlchemy `Base` (imported by all ORM models), session factories, and dependency injection helpers.

- **New modules:** Use `get_async_db()` for `AsyncSession`. All repository methods are `async def` using SQLAlchemy 2.0 Core `select()` statements.
- **Migration note:** Older modules still use synchronous `get_db()` and are being incrementally migrated (see [ADR-010](../design/adr/010-async-database-layer.md)).
- **Do not mix** `get_db` and `get_async_db` within the same module.

### Logging (`core/logging.py`)

Configures Python's standard logging with a custom formatter that supports structured context via `extra={}` keyword arguments. All modules import `logger` from here to ensure consistent formatting and routing of log messages.

### Authentication (`core/current_user.py`)

Provides FastAPI dependency functions for Role-Based Access Control (RBAC):

- `get_current_user()`: Validates the Bearer token and returns the authenticated user.
- `get_current_admin_user()`: Extends `get_current_user()` and asserts `role == admin`.

Route handlers inject these to require authentication or admin privileges.

### Error Response Handling

**`core/errors/codes.py`** — Global error codes shared across modules (e.g., `INVALID_CREDENTIALS`, `FORBIDDEN`).

**`core/errors/builders.py`** — Factory functions that create `HTTPException` objects with a standardized JSON error response shape: `{ "error": { "code", "message", "details" } }`. Each builder corresponds to an HTTP status (e.g., `validation_error` → 422, `business_rule_violation_error` → 409, etc.).

**`core/errors/handlers.py`** — Registers global FastAPI exception handlers. Ensures all exceptions (including domain exceptions caught in `api.py`) are normalized to the standard JSON response shape. Called once during application startup in `main.py`.

### Audit Trail (`core/audit/`)

Audit trail is a self-contained infrastructure sub-package that follows the standard layered architecture of domain modules, but lives in `core/` because it is shared infrastructure:

```text
app/core/audit/
  __init__.py       ← Public API re-exports
  enums.py          ← AuditActorType, AuditAction
  models.py         ← AuditLog ORM model
  repositories.py   ← Data access
  services.py       ← AuditTrail service
  composition.py    ← Dependency wiring
```

**Design:** When a critical state-changing operation succeeds in a service (e.g., purchase confirmation), the service calls `audit_trail.record(...)` to atomically write both a database row and a structured log line. This creates an immutable audit log capturing who did what and when.

For details on which operations require auditing and how to integrate audit calls, see [ADR-015](../design/adr/015-persistent-audit-trail.md).

---

## 3. Authentication – The `auth` Module

The `auth` module is a special-case feature module that demonstrates the cross-module client pattern. It does not own a user database; instead, it accesses user data through a `UsersClient` abstraction.

### Design Pattern: Cross-Module Boundary

The `auth` module imports `users` module data indirectly via `clients/users.py`, creating a clear boundary:

- `auth` focuses on token creation, validation, and session management.
- `users` focuses on user identity and profile data.
- If the `users` module is extracted to a microservice in the future, only the `UsersClient` concrete implementation changes to make HTTP calls instead of direct DB queries.

### Module Structure

- **`models.py`**: Python dataclasses (not ORM) representing auth domain concepts (`TokenPayload`, `Token`).
- **`exceptions.py`**: Auth-specific exceptions (e.g., `InvalidTokenException`).
- **`token_provider.py`**: `OAuth2TokenProviderABC` interface and `JwtOAuth2TokenProvider` default implementation.  A single ABC+impl file kept in the root of `core/` (e.g., `app/core/token_provider.py`), following the pattern for small infrastructure components as documented in build-feature.prompt.md Known Constraints.
- **`clients/users.py`**: `UsersClientABC` and concrete `UsersClient` for reading user data.

### Extension: Feature Flags

Similar to how `auth` accesses the `users` module through a client, modules that need runtime feature control should use a `clients/feature_flags.py` client. See the Known Constraints section of [build-feature.prompt.md](.github/prompts/build-feature.prompt.md) for the full pattern and [ADR-018](../design/adr/018-feature-flag-system.md) for design rationale.

---

## 4. Application Wiring – `main.py`

The FastAPI application is assembled in `main.py`:

1. **Error handlers:** `register_error_handlers(app)` sets up global exception handling.
2. **Routers:** Each feature module's router is registered with `app.include_router(...)`.
3. **ORM discovery:** All ORM models are imported into `app/models.py` so Alembic can detect migrations.

When implementing a new feature module:

- Add its router import and registration to `main.py`.
- Import the ORM model (if any) in `app/models.py`.

All routers use the API prefix `/api/v1`.

---

## 5. Error Handling Flow

All errors follow a consistent path to ensure a uniform API response shape:

```
Domain Exception (from exceptions.py)
  ↓
Caught in api.py route handler
  ↓
Converted to HTTPException via core/errors/builders.py
  ↓
Normalized by core/errors/handlers.py
  ↓
Client receives: { "error": { "code", "message", "details" } }
```

**Design principle:** Domain and service layers have no knowledge of HTTP. They raise plain domain exceptions carrying context. Only the API layer knows about HTTP status codes and response shapes.

---

## 6. Logging Conventions

All logging is centralized through `core/logging.py`, which provides a configured root logger with a custom `ExtraDictFormatter`. This ensures:

- Consistent formatting and routing across all modules.
- Structured context via `extra={}` keyword arguments (not string interpolation).

### Structured Logging Pattern

Always pass contextual data through `extra={}`:

```python
# ✅ Correct: context is structured
logger.info("Login attempt successful.", extra={"email": email, "user_id": user_id})

# ❌ Avoid: context is baked into the message
logger.info(f"Login attempt successful for {email}.")
```

Structured context lets you search and filter logs efficiently and maintains a stable message key for use in log aggregation and alerting systems.

### When to Log

- **Successful state-changing operations:** Use `logger.info(...)`.
- **Expected negative paths and business rule violations:** Use `logger.debug(...)` or skip if not actionable.
- **Unexpected errors:** `logger.error(...)` in the API layer (domain/service layers don't know about HTTP, so they don't log `*Error` cases — that's the caller's responsibility).
- **Read-only operations:** Generally skip; they clutter logs and offer little value.

For audit-critical operations (e.g., purchase confirmation, withdrawal processing), the `AuditTrail` service automatically emits both a DB row and a structured `INFO` log — do not add additional logging for these operations.

### Log Levels and When to Use Them

| Level | When to use | Examples in the codebase |
| --- | --- | --- |
| `DEBUG` | Expected negative paths and step-by-step tracing. Safe to emit on every request. Should never surface in production unless diagnosing a specific issue. | Login with non-existent email; login with wrong password; password failing a complexity check; token verification steps |
| `INFO` | Successful significant domain events — things worth having a permanent audit trail for. | Successful login; merchant created; user registered |
| `WARNING` | Unexpected-but-handled anomalies: the system recovers, but the event is suspicious or abnormal. | Token payload missing required fields |
| `ERROR` | Unexpected exceptions that are caught at the API boundary (the catch-all `except Exception` block). The request fails; there is no domain explanation. | Any unhandled exception in `api.py` before raising `internal_server_error()` |

### Where Each Level Appears by Layer

- **Services and policies**: use `DEBUG` for expected negative paths (validation failures, not-found lookups) and `INFO` for successful outcomes of state-mutating operations (create, update, delete, login). Read-only operations (listing, fetching) should not log. **Do not duplicate logs for the same event in both the service/policy and API layers—log only in the service or policy layer.**
- **Token provider / infrastructure**: use `DEBUG` for step-by-step tracing, `WARNING` for anomalies (malformed payloads), `ERROR` for unrecoverable processing failures.
- **API layer**: only use `ERROR` for the catch-all unexpected exception handler. Do not log expected domain exceptions (such as not found, validation errors, or business rule violations) in the API layer if they are already logged in the service or policy layer.

### What Not to Log

- Never log passwords, raw tokens, or any secret material.
- Do not log at `INFO` or above for every repository query — that belongs at `DEBUG`.
- Do not log read-only service operations (queries that do not mutate DB state). These have no audit value and add noise. Only log at `INFO` for operations that create, update, or delete records, or that represent a security-relevant event.
- Do not duplicate the exception traceback manually; Python's `logging.exception()` or `logging.error(..., exc_info=True)` can include it automatically if needed.

### Audit Trail — Persistent Record of Critical Operations

Runtime logging is not a substitute for a persistent audit record. For every critical state-changing operation (purchase confirmation/rejection, cashback crediting, withdrawal processing, admin overrides), the service must also call `AuditTrail.record(...)` **in addition** to emitting the regular log line.

The distinction:

| Concern | Tool | Storage | Use for |
| --- | --- | --- | --- |
| Debugging & alerting | `logging.info/warn/error` | stdout / log aggregator | Runtime diagnostics, performance, errors |
| Compliance & traceability | `AuditTrail.record(...)` | PostgreSQL `audit_logs` | Who did what, when, with what outcome — permanently |

See the `core/audit/` section above and [ADR-015](../design/adr/015-persistent-audit-trail.md) for full details. See [NFR-10](../specs/non-functional/10-logging-observability.md) for the complete list of operations that require an audit row.

---

## 7. Testing Conventions

For all testing patterns, fixture conventions, test levels, and checklists, see the authoritative reference: `docs/guidelines/unit-testing.md`.

---

## 8. Scaffolding a New Feature or Module

Step-by-step implementation guides live in the prompt files, which reference this document for conventions:

- `.github/prompts/new-feature.prompt.md` — implementing a single endpoint or operation within an existing module
- `.github/prompts/new-module.prompt.md` — scaffolding a complete new domain module with multiple endpoints

For guidelines on how to keep files at a readable size as modules grow, see `docs/guidelines/code-organization.md`.
