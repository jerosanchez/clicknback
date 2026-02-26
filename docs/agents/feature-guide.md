# ClickNBack – Feature Development Guide

This document is the authoritative reference for adding new feature modules to ClickNBack. It covers module anatomy, layer responsibilities, application wiring, error handling, logging, and testing conventions.

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
  api.py               ← FastAPI router (HTTP layer only)
  api-requests/        ← Manual HTTP test files (VS Code REST Client)
    <verb>-<resource>.http   ← One file per route; all typical responses covered
```

Not every module needs all files (e.g., `auth` has no `repositories.py` — it delegates to `users` via a client).

### Layer Responsibilities

#### `models.py` – ORM Models

SQLAlchemy `Base` subclasses. UUIDs as string PKs, `server_default` for DB-side defaults.

```python
class Merchant(Base):
    __tablename__ = "merchants"
    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column()
    default_cashback_percentage: Mapped[float] = mapped_column()
    active: Mapped[bool] = mapped_column(server_default=text("true"))
```

All models must be imported in `app/models.py` so Alembic can detect them.

#### `schemas.py` – Pydantic Schemas

Three typical schema classes per entity:

- `<Entity>SchemaBase` – shared fields.
- `<Entity>Create` – for `POST` request body (extends base, adds write-only fields like `password`).
- `<Entity>Out` – for response bodies (extends base, adds `id`, `created_at`, excludes secrets). Always sets `model_config = {"from_attributes": True}` to allow ORM model → schema conversion.

#### `repositories.py` – Repository Layer

Two classes per repository:

- `<Entity>RepositoryABC` – abstract class defining the interface (enables mocking in tests).
- `<Entity>Repository` – concrete SQLAlchemy implementation.

The repository only performs DB queries. No business logic here.

```python
class UserRepositoryABC(ABC):
    @abstractmethod
    def get_user_by_email(self, db: Session, email: str) -> User | None: ...

class UserRepository(UserRepositoryABC):
    def get_user_by_email(self, db: Session, email: str) -> User | None:
        return db.query(User).filter(User.email == email).first()
```

#### `services.py` – Service Layer

Contains the `<Entity>Service` class. Dependencies (repository, policy callables, etc.) are injected via `__init__()` (the constructor) — never instantiated directly inside the service. This makes services fully unit-testable without touching the DB.

```python
class UserService:
    def __init__(
        self,
        enforce_password_complexity: Callable[[str], None],
        hash_password: Callable[[str], str],
        user_repository: UserRepositoryABC,
    ): ...
```

Services raise **domain exceptions** (from `exceptions.py`). They have no knowledge of HTTP status codes.

#### `policies.py` – Business Rule Functions

Pure functions that enforce a single business rule. They raise domain exceptions on violation. They do not return a value on success (implicit `None`).

```python
def enforce_cashback_percentage_validity(percentage: float) -> None:
    if not (0 <= percentage <= settings.max_cashback_percentage):
        raise CashbackPercentageNotValidException(...)
```

Policy functions are injected into services via `composition.py`, making them independently testable.

#### `exceptions.py` – Domain Exceptions

Plain Python exceptions. No FastAPI or HTTP knowledge. They carry context as attributes for use by the API layer.

```python
class EmailAlreadyRegisteredException(Exception):
    def __init__(self, email: str):
        super().__init__(f"Email '{email}' is already registered.")
        self.email = email  # <- carries context for the API layer
```

#### `errors.py` – Module Error Codes

A `str, Enum` class defining semantic error codes specific to the module's HTTP responses. These are separate from `core/errors/codes.py` which holds global codes.

```python
class ErrorCode(str, Enum):
    PASSWORD_NOT_COMPLEX_ENOUGH = "PASSWORD_NOT_COMPLEX_ENOUGH"
    EMAIL_ALREADY_REGISTERED = "EMAIL_ALREADY_REGISTERED"
```

#### `composition.py` – Dependency Wiring

Factory functions used with FastAPI's `Depends()` system. This is where concrete implementations are assembled and injected. Keeps `api.py` clean. This is also the seam for overriding dependencies in tests.

```python
def get_user_service():
    return UserService(
        get_enforce_password_complexity(),
        get_password_hasher(),
        get_user_repository(),
    )
```

#### `api.py` – HTTP Router

FastAPI `APIRouter`. Responsibilities:

1. Declare routes with request/response schemas.
2. Resolve dependencies via `Depends()`.
3. Call the service.
4. Catch domain exceptions and convert them to `HTTPException` using `core/errors/builders.py`.
5. Log unexpected errors and raise `internal_server_error()`.

```python
@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    create_data: UserCreate,
    user_service: UserService = Depends(get_user_service),
    db: Session = Depends(get_db),
) -> UserOut:
    try:
        return user_service.create_user(create_data.model_dump(), db)
    except EmailAlreadyRegisteredException as exc:
        raise business_rule_violation_error(ErrorCode.EMAIL_ALREADY_REGISTERED, str(exc), {"email": exc.email})
    except Exception as e:
        logging.error("Unexpected error", extra={"error": str(e)})
        raise internal_server_error()
```

**The API layer never contains business logic.** It only translates between HTTP and the service layer.

---

## 2. The `core` Module – Cross-Cutting Concerns

`app/core/` provides shared infrastructure used across all feature modules.

### `core/config.py`

`pydantic-settings` `Settings` class loaded from environment variables (or `.env`). All configuration lives here. Other modules import `settings` from this module.

```python
class Settings(BaseSettings):
    database_url: str
    oauth_hash_key: str
    oauth_algorithm: str
    oauth_token_ttl: int
    log_level: str = "INFO"
    max_cashback_percentage: float = 20.0
```

### `core/database.py`

SQLAlchemy engine, `SessionLocal`, and the ORM `Base`. The `get_db()` generator is a FastAPI dependency that yields a DB session and ensures it is closed after the request.

```python
Base = declarative_base()  # imported by all ORM models

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### `core/logging.py`

Configures the root Python logger with a custom `ExtraDictFormatter` that appends structured `extra=` keyword arguments to log messages. All modules import `logger` (or `logging`) from here.

```python
logger = logging.getLogger(__name__)
# Usage:
logger.info("Login successful.", extra={"email": email})
```

### `core/current_user.py`

Provides two FastAPI dependency functions:

- `get_current_user(token, db, token_provider, user_repository) -> User`: validates the Bearer token and returns the active user.
- `get_current_admin_user(current_user) -> User`: wraps `get_current_user` and additionally asserts `role == admin`.

Used in protected routes to implement Role-Based Access Control (RBAC):

```python
_current_user: User = Depends(get_current_admin_user)  # admin-only endpoint
```

Any route that needs authentication injects one of these dependencies. Routes that don't include them are public.

### `core/errors/codes.py`

Global `ErrorCode` enum for codes shared across modules (e.g., `INVALID_CREDENTIALS`, `INVALID_TOKEN`, `FORBIDDEN`, `INTERNAL_SERVER_ERROR`).

### `core/errors/builders.py`

Factory functions that build `HTTPException` objects with a consistent JSON error shape:

```json
{
  "error": {
    "code": "EMAIL_ALREADY_REGISTERED",
    "message": "Email 'x@y.com' is already registered.",
    "details": { "email": "x@y.com" }
  }
}
```

Available builders:

| Function | HTTP Status |
| --- | --- |
| `validation_error(code, message, details)` | 400 |
| `authentication_error(message, details)` | 401 |
| `forbidden_error(message, details)` | 403 |
| `business_rule_violation_error(code, message, details)` | 409 |
| `unprocessable_entity_error(code, message, details)` | 422 |
| `internal_server_error(message, details)` | 500 |

### `core/errors/handlers.py`

Registers global FastAPI exception handlers via `register_error_handlers(app)`. This ensures:

- `InvalidTokenException` → 401 JSON response.
- All `HTTPException`s → normalized JSON `{ "error": { ... } }` shape.

This is called once in `main.py`.

---

## 3. The `auth` Module

Authentication is a standalone module. It does **not** have its own ORM model or repository — instead, it accesses user data through a `UsersClient` abstraction. This might change in the future if needed, encapsulating auth-related information in its own DB table, and keeping the `users` table clean from this concern.

### Key Design: `clients.py`

`UsersClient` wraps `UserRepository` and exposes a minimal `get_user_by_email()` interface that returns an `auth.models.User` dataclass (not the ORM model). This is a **modular monolith boundary**: if `auth` were split into a microservice, only this client would need to change.

```python
class UsersClientABC(ABC):
    @abstractmethod
    def get_user_by_email(self, db: Session, email: str) -> Optional[User]: ...
```

### `auth/models.py`

Pure Python dataclasses (no ORM):

- `User(id, email, hashed_password, role)` – internal auth representation.
- `Token(access_token, token_type)` – login response model.
- `TokenPayload(user_id, user_role)` – decoded JWT payload.

### `auth/token_provider.py`

`OAuth2TokenProviderABC` interface with `create_access_token` and `verify_access_token`. The concrete `JwtOAuth2TokenProvider` uses `python-jose`. Switching token strategies only requires a new provider implementation.

### Login Flow

1. `POST /api/v1/login` → `auth/api.py`
2. Calls `AuthService.login(data, db)`
3. Service uses `UsersClient.get_user_by_email()` → raises `UserNotFoundException` if not found
4. Verifies password with injected `verify_password` callable → raises `PasswordVerificationException`
5. Creates JWT via `token_provider.create_access_token(TokenPayload(...))`
6. Returns `Token(access_token, token_type="bearer")`

---

## 4. Application Wiring – `main.py`

```python
app = FastAPI()
register_error_handlers(app)    # global error handlers from core
app.include_router(users_api.router)
app.include_router(auth_api.router)
app.include_router(merchants_api.router)
```

All routers use the prefix `/api/v1`. When adding a new feature module, its router must be included here.

### `app/models.py` – Alembic Discovery

```python
from app.merchants.models import Merchant
from app.users.models import User
```

Every new ORM model must be imported here so Alembic's `env.py` can detect schema changes.

---

## 5. Error Handling Convention

The full error handling chain:

```text
Domain Exception (exceptions.py)
  → caught in api.py
  → converted to HTTPException via core/errors/builders.py
  → normalized by core/errors/handlers.py
  → consistent JSON response: { "error": { "code", "message", "details" } }
```

Never raise `HTTPException` directly in a service or repository. Never let domain exceptions escape the API layer unhandled.

---

## 6. Logging Conventions

Logging is built on Python's standard `logging` module, configured centrally in `core/logging.py`. **Do not use FastAPI's or Uvicorn's built-in logging directly** — all modules route through the shared setup so that the formatter, level, and handler are applied consistently.

### Setting Up a Logger

The preferred approach in services, policies, and infrastructure code is to obtain a named logger via the module-level `logger` exported from `core/logging.py`:

```python
# Preferred: named logger (carries module name in output)
from app.core.logging import logger

logger.info("Login attempt successful.", extra={"email": email})
```

In API modules, the `logging` module itself is re-exported from `core/logging.py` and used directly:

```python
# API layer pattern
from app.core.logging import logging

logging.error("An unexpected error occurred.", extra={"error": str(e)})
```

Either approach routes through the same configured root logger and formatter. The named `logger` is preferred for richer output (the module name is included in the log line).

### Structured Context with `extra=`

`core/logging.py` installs a custom `ExtraDictFormatter` that appends any keyword arguments passed via `extra={}` to the end of the log line:

```text
2026-02-26 10:00:01 - INFO - app.auth.services - Login attempt successful. | extra={'email': 'alice@example.com'}
```

Always pass contextual data through `extra={}`, never by interpolating values into the message string. This keeps the message itself a stable, searchable key and the variable data structured:

```python
# Correct
logger.info("Login attempt successful.", extra={"email": email})

# Avoid
logger.info(f"Login attempt successful for {email}.")
```

### Log Levels and When to Use Them

| Level | When to use | Examples in the codebase |
| --- | --- | --- |
| `DEBUG` | Expected negative paths and step-by-step tracing. Safe to emit on every request. Should never surface in production unless diagnosing a specific issue. | Login with non-existent email; login with wrong password; password failing a complexity check; token verification steps |
| `INFO` | Successful significant domain events — things worth having a permanent audit trail for. | Successful login; merchant created; user registered |
| `WARNING` | Unexpected-but-handled anomalies: the system recovers, but the event is suspicious or abnormal. | Token payload missing required fields |
| `ERROR` | Unexpected exceptions that are caught at the API boundary (the catch-all `except Exception` block). The request fails; there is no domain explanation. | Any unhandled exception in `api.py` before raising `internal_server_error()` |

### Where Each Level Appears by Layer

- **Services and policies**: use `DEBUG` for negative paths (validation failures, not-found lookups) and `INFO` for successful outcomes of meaningful operations.
- **Token provider / infrastructure**: use `DEBUG` for step-by-step tracing, `WARNING` for anomalies (malformed payloads), `ERROR` for unrecoverable processing failures.
- **API layer**: use `DEBUG` for caught domain exceptions that are translated to HTTP responses, and `ERROR` for the catch-all unexpected exception handler.

### What Not to Log

- Never log passwords, raw tokens, or any secret material.
- Do not log at `INFO` or above for every repository query — that belongs at `DEBUG`.
- Do not duplicate the exception traceback manually; Python's `logging.exception()` or `logging.error(..., exc_info=True)` can include it automatically if needed.

---

## 7. Testing Conventions

### Test Structure

```text
tests/
  conftest.py          ← Shared fixtures (factories for User, Merchant, etc.)
  auth/
    test_auth_api.py          ← API-level (integration-style, HTTP)
    test_auth_services.py     ← Unit tests for AuthService
    test_token_providers.py   ← Unit tests for JwtOAuth2TokenProvider
  core/
    test_current_user.py      ← Unit tests for get_current_user / get_current_admin_user
    errors/
      test_builders.py        ← Unit tests for error builder functions
  merchants/
    test_merchants_api.py     ← API-level tests
    test_merchants_policies.py ← Unit tests for policy functions
    test_merchants_services.py ← Unit tests for MerchantService
  users/
    test_users_api.py         ← API-level tests
    test_users_policies.py    ← Unit tests for policy functions
    test_users_services.py    ← Unit tests for UserService
```

### Test Levels

| Level | What it tests | DB required | Mocking strategy |
| --- | --- | --- | --- |
| **Unit** (services, policies) | Pure business logic | No | Mock repositories/callables via `create_autospec` |
| **API-level** (api.py) | HTTP routing, error mapping, response shape | No | Override `get_db` and service dependencies via `app.dependency_overrides` |
| **Integration / E2E** | Full stack including DB | Yes | Real DB (test DB), minimal mocking |

### Key Patterns

**API tests** use `TestClient` with `app.dependency_overrides`:

```python
@pytest.fixture
def client(service_mock):
    app.dependency_overrides[get_db] = lambda: (yield Mock())
    app.dependency_overrides[get_user_service] = lambda: service_mock
    app.dependency_overrides[get_current_admin_user] = lambda: Mock()  # bypass auth
    yield TestClient(app)
    app.dependency_overrides.clear()
```

**Service tests** inject mocked dependencies directly into the service constructor:

```python
@pytest.fixture
def user_service(enforce_password_complexity, hash_password, user_repository):
    return UserService(enforce_password_complexity, hash_password, user_repository)
```

**Shared fixtures** in `tests/conftest.py` provide factory callables:

```python
@pytest.fixture
def user_factory() -> Callable[..., User]:
    def _make_user(**kwargs) -> User:
        defaults = { "id": "...", "email": "alice@example.com", ... }
        defaults.update(kwargs)
        return User(**defaults)
    return _make_user
```

Factories accept `**kwargs` to allow per-test customization without defining many fixtures.

---

## 8. How to Scaffold a New Feature Module

When adding a new feature (e.g., `purchases`), follow this checklist:

### Step 1 – Create the module directory

```text
app/purchases/
  __init__.py
  models.py
  schemas.py
  repositories.py
  services.py
  policies.py       (if business rules apply)
  exceptions.py
  errors.py
  composition.py
  api.py
  api-requests/
    create-purchase.http     ← one file per route, named <verb>-<resource>.http
```

### Step 2 – `models.py` – ORM model

```python
import uuid
from sqlalchemy import text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class Purchase(Base):
    __tablename__ = "purchases"
    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    # ... fields
```

Register in `app/models.py`:

```python
from app.purchases.models import Purchase
```

### Step 3 – `schemas.py` – Pydantic schemas

```python
class PurchaseCreate(PurchaseSchemaBase):
    ...

class PurchaseOut(PurchaseSchemaBase):
    id: UUID
    model_config = {"from_attributes": True}
```

### Step 4 – `repositories.py` – Repository

```python
class PurchaseRepositoryABC(ABC):
    @abstractmethod
    def add_purchase(self, db: Session, purchase: Purchase) -> Purchase: ...

class PurchaseRepository(PurchaseRepositoryABC):
    def add_purchase(self, db: Session, purchase: Purchase) -> Purchase:
        db.add(purchase)
        db.commit()
        db.refresh(purchase)
        return purchase
```

### Step 5 – `exceptions.py` and `errors.py`

```python
# exceptions.py
class PurchaseAlreadyExistsException(Exception):
    def __init__(self, external_id: str):
        super().__init__(f"Purchase '{external_id}' already exists.")
        self.external_id = external_id

# errors.py
class ErrorCode(str, Enum):
    DUPLICATE_PURCHASE = "DUPLICATE_PURCHASE"
```

### Step 6 – `policies.py` – Business rules

```python
def enforce_some_rule(value: ...) -> None:
    if not valid:
        raise SomeDomainException(...)
```

### Step 7 – `services.py` – Service

```python
class PurchaseService:
    def __init__(self, some_policy: Callable, repository: PurchaseRepositoryABC):
        self.some_policy = some_policy
        self.repository = repository

    def create_purchase(self, data: dict, db: Session) -> Purchase:
        self.some_policy(data["value"])
        # ... business logic
        return self.repository.add_purchase(db, Purchase(...))
```

### Step 8 – `composition.py` – Wiring

```python
def get_purchase_service():
    return PurchaseService(
        some_policy,
        PurchaseRepository(),
    )
```

### Step 9 – `api.py` – Router

```python
router = APIRouter(prefix="/api/v1")

@router.post("/purchases", response_model=PurchaseOut, status_code=201)
def create_purchase(
    data: PurchaseCreate,
    service: PurchaseService = Depends(get_purchase_service),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),  # or get_current_admin_user
) -> PurchaseOut:
    try:
        return service.create_purchase(data.model_dump(), db)
    except PurchaseAlreadyExistsException as exc:
        raise business_rule_violation_error(ErrorCode.DUPLICATE_PURCHASE, str(exc), {...})
    except Exception as e:
        logging.error("Unexpected error", extra={"error": str(e)})
        raise internal_server_error()
```

### Step 10 – `api-requests/` – Manual HTTP test files

Create one `.http` file per route inside `app/<module>/api-requests/`. Name each file after the operation it exercises, using an infinitive verb first: `create-purchase.http`, `list-purchases.http`, `get-purchase.http`, `delete-purchase.http`, etc.

Each file must contain sample requests that collectively cover every distinct HTTP response the endpoint can produce: a successful response, any validation errors (missing or malformed fields), and every domain/policy exception caught in `api.py`. The goal is to be able to smoke-test the full response surface of a single route without leaving the editor.

Extract repeating values into variables whenever possible (see example below).

These files are intended for use with the [VS Code REST Client](https://marketplace.visualstudio.com/items?itemName=humao.rest-client) extension.

Example:

```http
@baseUrl = http://localhost:8000/api/v1
# For authenticated endpoints, obtain a token via the login endpoint first
# and paste it below (short-lived, from local seed data only).
# @adminToken = Bearer <paste token here>
# @userToken  = Bearer <paste token here>

### Get a token for testing (admin)
POST {{baseUrl}}/login
Content-Type: application/json

{
  "email": "carol@example.com",
  "password": "Str0ng!Pass"
}

### 201 – Happy path: purchase created
POST {{baseUrl}}/purchases
Authorization: {{adminToken}}
Content-Type: application/json

{
  "merchant_id": "some-uuid",
  "amount": 50.0
}

### 401 – Missing authentication token
POST {{baseUrl}}/purchases
Content-Type: application/json

{
  "merchant_id": "some-uuid",
  "amount": 50.0
}

### 403 – Non-admin user
POST {{baseUrl}}/purchases
Authorization: {{userToken}}
Content-Type: application/json

{
  "merchant_id": "some-uuid",
  "amount": 50.0
}

### 409 – Duplicate purchase (policy exception)
POST {{baseUrl}}/purchases
Authorization: {{adminToken}}
Content-Type: application/json

{
  "merchant_id": "some-uuid",
  "amount": 50.0
}

### 422 – Validation error: negative amount
POST {{baseUrl}}/purchases
Authorization: {{adminToken}}
Content-Type: application/json

{
  "merchant_id": "some-uuid",
  "amount": -10.0
}
```

Guidelines:

- **One file per route.** `create-purchase.http` covers `POST /purchases`; `list-purchases.http` covers `GET /purchases`; and so on. Do not mix multiple routes in one file.
- **File naming:** infinitive verb first, then the resource, kebab-cased — `create-purchase.http`, `list-merchants.http`, `get-user.http`.
- **Coverage:** include one request per distinct HTTP response code the endpoint can return. Every `except` clause in `api.py` should have a corresponding request in the file.
- **Request comments:** prefix each request with `### <STATUS_CODE> – <description>` so the intent is visible in the REST Client sidebar.
- **Tokens:** always define `@baseUrl` at the top. Include a login request when auth is required so a token can be obtained without leaving the file. Never commit real long-lived tokens — use short-lived tokens from local seed data only.

### Step 11 – Register in `main.py`

```python
from app.purchases import api as purchases_api
app.include_router(purchases_api.router)
```

### Step 12 – Create an Alembic migration

```bash
alembic revision --autogenerate -m "add purchases table"
alembic upgrade head
```

### Step 13 – Tests

```text
tests/purchases/
  test_purchases_api.py
  test_purchases_policies.py   (if applicable)
  test_purchases_services.py
```

Follow the same patterns: mock repository in service tests, override `app.dependency_overrides` in API tests, add factories to `conftest.py`.

### Step 14 – Verify quality gates

After completing all the steps above, run the full quality gate suite and fix every reported issue before considering the task done:

```bash
make lint && make format && make test
```

All three commands must exit with code 0. Do **not** mark the feature as finished until they do. For a full breakdown of what each gate checks, how to diagnose failures, and the mandatory workflow, see `docs/agents/quality-gates.md`.
