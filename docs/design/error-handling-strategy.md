# Error Handling Strategy

## 1. Overview

ClickNBack is a financial system where errors carry significant consequences—incorrect balance updates, race conditions, or ambiguous failure states can corrupt data integrity. This document outlines our approach to error handling across three dimensions:

1. **Client communication:** How errors are reported via HTTP responses
2. **Backend propagation:** How errors flow through layers and are handled
3. **Recovery and observability:** How we ensure consistency and diagnose issues

The strategy balances **clarity and specificity for clients** (enabling smart retries and informed error recovery) with **internal robustness** (preventing data corruption and maintaining financial correctness).

---

## 2. Design Principles

### 2.1 Errors Are Business Logic

Financial operations have well-defined failure modes: duplicate purchases (idempotency violations), invalid offers, insufficient balances, concurrency conflicts. These are not exceptions—they are *expected business states* that clients must understand and handle.

**Implication:** Domain errors (e.g., `EmailAlreadyRegisteredException`) are first-class domain concepts, not runtime surprises.

### 2.2 Be Specific for Clients

Generic "500 Internal Server Error" messages are useless. Clients need to know:

- **What failed:** Which business rule was violated?
- **Why it failed:** What condition caused the failure?
- **What to do:** Should they retry? Submit different data? Contact support?

**Implication:** Each error type maps to a specific HTTP status and a structured response containing the error code and explanation.

### 2.3 Fail Fast at Boundaries

Authorization, validation, and precondition checks happen **before** business logic executes. A request that violates rules is rejected immediately, preventing partial state changes and wasted database work.

**Implication:** Invalid requests never reach service layers; errors are caught at API boundary.

### 2.4 Preserve Data Integrity

Under concurrent load, race conditions and partial updates can corrupt financial state. All business operations execute within database transactions, and errors trigger rollbacks automatically. No operation can leave the database in an inconsistent state.

**Implication:** Transaction boundaries are non-negotiable; errors must never escape a transaction without rolling back.

---

## 3. Client Error Communication

### 3.1 Standard Response Format

All API responses use a consistent error structure to enable predictable client handling:

```json
{
  "error": {
    "code": "EMAIL_ALREADY_REGISTERED",
    "message": "Email 'user@example.com' is already registered. Use a different email or recover your account.",
    "details": {
      "email": "user@example.com",
      "timestamp": "2026-02-17T14:33:22Z"
    }
  }
}
```

**Components:**

- **`code`:** Machine-readable error identifier (uppercase, snake_case). Enables client-side error routing (e.g., show form validation UI for `VALIDATION_ERROR`, show login prompt for `UNAUTHORIZED`).
- **`message`:** Human-readable explanation of what happened and what the user might try next.
- **`details`:** Optional structured context (field names, values, constraints). Varies by error type but always JSON-serializable.

### 3.2 HTTP Status Codes

ClickNBack uses a focused set of HTTP status codes corresponding to error categories:

| Status | Code | Scenario | Client Action |
| -------- | ------ | ---------- | ------------- |
| **400** | `BAD_REQUEST` | Malformed input (invalid JSON, missing fields) | Fix request and retry |
| **400** | `VALIDATION_ERROR` | Input validation failed (weak password, invalid email) | Correct input per error details and retry |
| **401** | `UNAUTHORIZED` | Missing or invalid authentication token | Include valid token or re-authenticate |
| **403** | `FORBIDDEN` | Authenticated but insufficient permissions (non-admin accessing admin endpoint) | Use authorized account |
| **404** | `NOT_FOUND` | Resource not found (user, offer, merchant, etc. does not exist) | Check resource identifier or existence; may need to refresh or contact support |
| **409** | `CONFLICT` | Business rule violation (email already exists, duplicate purchase) | Resolve conflict (use different email) or contact support |
| **422** | `UNPROCESSABLE_ENTITY` | Request is syntactically valid but semantically invalid (offer inactive, user account disabled) | Verify resource state and retry or contact support |
| **500** | `INTERNAL_SERVER_ERROR` | Unexpected error (database unavailable, code bug) | Retry with exponential backoff; contact support if persistent |

**Note on 409 vs. 422:**

- **409 Conflict:** Resource state conflicts with request (e.g., email already registered, idempotency key already processed).
- **422 Unprocessable Entity:** Request is invalid *for the current system state* but not due to resource duplication (e.g., offer not active, user not confirmed).

**Note:** For 500 errors, we never expose implementation details (stack traces, database errors) to clients. Instead, we include a `request_id` for support teams to correlate logs.

---

## 4. Backend Error Propagation

### 4.1 Exception Hierarchy

ClickNBack uses a layered exception model matching the modular monolith architecture:

```text
Exception (Python base)
├── DomainException (Base for all ClickNBack errors)
│   ├── EmailAlreadyRegisteredException
│   ├── PasswordNotComplexEnoughException
│   ├── InactiveOfferException
│   ├── InsufficientBalanceException
│   ├── DuplicatePurchaseException
│   └── ...
```

**Rationale:**

- **Single `DomainException` root:** Enables catching "all expected errors" at the API boundary in a try-catch.
- **Category exceptions:** Group related errors for handling logic (e.g., `ConflictError` → 409, `UnprocessableError` → 422).
- **Domain-specific exceptions:** Represent concrete business failures, caught and converted to responses at API level.

### 4.2 Exception Design

Each domain exception is minimal but complete:

```python
# app/users/exceptions.py
class EmailAlreadyRegisteredException(Exception):
    """Raised when user registration attempts to use a duplicate email."""
    pass

class PasswordNotComplexEnoughException(Exception):
    """Raised when password fails complexity policy (min length, required chars, etc.)."""
    pass

# app/shared/exceptions.py
class DomainException(Exception):
    """Base class for all expected ClickNBack domain errors."""
    http_status_code: int = 500
    error_code: str = "UNKNOWN_ERROR"

class ConflictError(DomainException):
    """Resource already exists or state conflicts with request."""
    http_status_code = 409
    error_code = "CONFLICT"

class UnprocessableError(DomainException):
    """Request is valid but cannot be processed given current state."""
    http_status_code = 422
    error_code = "UNPROCESSABLE_ENTITY"
```

**Design notes:**

- Exceptions are simple; they encode the **what**, not the **how to respond**. Response formatting happens at the API layer.
- Each exception can include minimal context (e.g., email address, field name) but avoids implementation details.
- The error message is user-friendly and suggests a resolution path.

### 4.3 Layered Error Handling

Errors flow through layers. Each layer makes decisions about whether to catch, transform, or propagate errors.

#### Repository Layer

Catches database-level errors and converts to domain exceptions:

```python
# app/users/repositories.py
class UserRepository:
    def add_user(self, db: Session, user: User) -> User:
        try:
            db.add(user)
            db.commit()
            return user
        except IntegrityError as e:
            db.rollback()
            if "email" in str(e).lower():
                raise EmailAlreadyRegisteredException(
                    f"Email '{user.email}' is already registered."
                )
            raise  # Unexpected constraint violation; propagate for logging
```

Why: Database errors are technical details; we translate them to domain language.

#### Service Layer

Catches and propagates domain exceptions; implements business logic:

```python
# app/users/services.py
class UserService:
    def create_user(self, data: dict, db: Session) -> User:
        email = data["email"]
        password = data["password"]

        # Enforce business rules
        if self.user_repository.get_user_by_email(db, email):
            raise EmailAlreadyRegisteredException(
                f"Email '{email}' is already registered."
            )

        self.enforce_password_complexity(password)  # Raises if invalid

        hashed = self.hash_password(password)
        user = User(email=email, hashed_password=hashed, active=True)
        return self.user_repository.add_user(db, user)
```

Why: Services orchestrate business logic and let domain exceptions propagate; they don't catch and hide errors.

#### API Layer

Catches domain exceptions and converts to HTTP responses:

```python
# app/users/api.py
@router.post("/users", response_model=UserOut, status_code=201)
async def create_user(
    data: UserCreate,
    service: UserService = Depends(get_user_service),
    db: Session = Depends(get_db),
) -> UserOut:
    try:
        return service.create_user(data.model_dump(), db)
    except EmailAlreadyRegisteredException as e:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "EMAIL_ALREADY_REGISTERED",
                "message": str(e),
                "details": {"email": data.email}
            }
        )
    except PasswordNotComplexEnoughException as e:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "VALIDATION_ERROR",
                "message": str(e),
                "details": {"field": "password"}
            }
        )
    except Exception as e:
        # Unexpected error; log for investigation
        logger.exception("Unexpected error creating user", extra={"request_id": request.state.request_id})
        raise HTTPException(
            status_code=500,
            detail={
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred.",
                "details": {"request_id": request.state.request_id}
            }
        )
```

Why: APIs are the boundary; they translate domain errors to HTTP protocol. Catch-all for unexpected errors logs for investigation.

---

## 5. Idempotency and Error Recovery

### 5.1 Idempotent Operations

In a financial system, retry logic is essential—networks fail, timeouts occur, clients retry. ClickNBack makes critical operations **idempotent** so retries are safe.

**Strategy:** External IDs as idempotency keys.

```python
# Purchase ingestion: external_purchase_id (from merchant) must be unique
class Purchase(Base):
    __table_args__ = (
        UniqueConstraint("external_purchase_id", name="uq_external_purchase_id"),
    )
    external_purchase_id: str  # From merchant system; immutable
    user_id: int
    amount: Decimal
    ...

# API accepts repeated requests with same external_id
@router.post("/purchases")
async def ingest_purchase(request: PurchaseRequest, db: Session = Depends(get_db)):
    try:
        purchase = service.create_purchase(request, db)
        return PurchaseSuccessResponse(purchase)
    except DuplicatePurchaseException as e:
        # Same external_id already processed; safe to return prior result
        prior_purchase = db.query(Purchase).filter(
            Purchase.external_purchase_id == request.external_purchase_id
        ).first()
        return PurchaseSuccessResponse(prior_purchase)
    except Exception as e:
        ...
```

**Client implication:** If a purchase creation times out, the client can safely re-submit with the same `external_purchase_id` and know it will be idempotent (either a new record or the duplicate is detected).

### 5.2 Error-Driven Retries

Clients should retry based on error type:

| Error Code | Retry Strategy |
| ----------- | --- |
| `CONFLICT` (409) | No automatic retry; user must resolve (different email, etc.) |
| `UNPROCESSABLE_ENTITY` (422) | No automatic retry; state mismatch or incorrect input |
| `INTERNAL_SERVER_ERROR` (500) | Exponential backoff: 1s, 2s, 4s, 8s (max 3 retries) |
| `UNAVAILABLE` (503) | Exponential backoff; operation safe to retry (idempotent) |

**Note:** Only `5xx` errors are retryable. Retrying a `4xx` error wastes resources and won't succeed.

---

## 6. Database Transaction Boundaries

### 6.1 Transaction Scope

All financial operations execute within a single database transaction:

```python
def create_purchase(self, request: PurchaseRequest, db: Session) -> Purchase:
    """
    Creates a purchase and associated cashback transaction.

    Entire operation is atomic:
    - If cashback calculation or insert fails, purchase creation is rolled back.
    - If user wallet update fails, both purchase and cashback are rolled back.
    - Constraint violations (duplicate external_id) are caught and converted to domain exceptions.
    """
    try:
        # 1. Validate merchant and offer
        merchant = db.query(Merchant).filter(Merchant.id == request.merchant_id).first()
        if not merchant:
            raise MerchantNotFoundException(f"Merchant {request.merchant_id} not found.")

        # 2. Create purchase
        purchase = Purchase(
            external_purchase_id=request.external_purchase_id,
            user_id=request.user_id,
            merchant_id=merchant.id,
            amount=request.amount,
            status=PurchaseStatus.PENDING,
        )
        db.add(purchase)
        db.flush()  # Enforce unique constraint; raises IntegrityError if duplicate

        # 3. Calculate and create cashback
        cashback_amount = calculate_cashback(merchant, purchase.amount)
        cashback = CashbackTransaction(
            purchase_id=purchase.id,
            user_id=request.user_id,
            amount=cashback_amount,
            status=CashbackStatus.PENDING,
        )
        db.add(cashback)

        # 4. Update wallet
        wallet = db.query(Wallet).filter(Wallet.user_id == request.user_id).with_for_update().first()
        wallet.pending_balance += cashback_amount

        db.commit()
        return purchase
    except IntegrityError as e:
        db.rollback()
        if "external_purchase_id" in str(e):
            raise DuplicatePurchaseException(...)
        raise
    except Exception as e:
        db.rollback()
        raise
```

**Key points:**

- All updates (purchase, cashback, wallet) happen in one transaction.
- If any step fails, `db.rollback()` reverts all changes.
- Constraint violations are caught and converted to domain exceptions.
- Intentional use of `with_for_update()` to lock wallet rows during concurrent updates.

### 6.2 Preventing Partial Updates

Never perform manual rollback checks; instead, rely on transaction atomicity:

```python
# ❌ WRONG: Manual state tracking
def process_purchase(purchase_id, db):
    purchase = db.query(Purchase).get(purchase_id)
    try:
        purchase.status = PurchaseStatus.PROCESSING
        db.commit()

        result = call_external_service()  # Can fail!

        purchase.status = PurchaseStatus.COMPLETED
        db.commit()
    except Exception:
        purchase.status = PurchaseStatus.FAILED
        db.commit()  # Partial state left in database

# ✅ CORRECT: Transaction covers all or nothing
def process_purchase(purchase_id, db):
    try:
        purchase = db.query(Purchase).get(purchase_id)
        result = call_external_service()
        purchase.status = PurchaseStatus.COMPLETED
        purchase.external_response = result
        db.commit()  # All updates or nothing
    except Exception:
        db.rollback()  # No partial state
        raise
```

---

## 7. Logging and Observability

### 7.1 What to Log

Log decisions at each layer:

```python
# Repository: Data access outcomes
logger.info("Purchase created", extra={
    "purchase_id": purchase.id,
    "user_id": purchase.user_id,
    "merchant_id": purchase.merchant_id,
    "amount": str(purchase.amount),
    "request_id": request_id,
})

# Service: Business logic decisions
logger.info("Cashback calculated", extra={
    "purchase_id": purchase.id,
    "cashback_amount": str(cashback_amount),
    "offer_id": offer.id,
    "request_id": request_id,
})

# API: Error outcomes and unexpected paths
logger.error("Email already registered", extra={
    "email": masked_email,  # Mask sensitive data
    "user_agent": request.headers.get("user-agent"),
    "request_id": request_id,
})

logger.exception("Unexpected error processing purchase", extra={
    "purchase_id": purchase.id,
    "request_id": request_id,
})
```

**Principles:**

- **Include `request_id`:** Correlate all logs for a single request across layers.
- **Avoid sensitive data:** Never log passwords, tokens, full PII. Use masking (first letter + `***@example.com`).
- **Use structured logging:** Log as JSON with key-value pairs, enabling indexing and aggregation.
- **Log at the right level:**
  - `DEBUG`: Detailed tracing (parameter values, internal state transitions).
  - `INFO`: Significant business events (user created, purchase confirmed).
  - `WARNING`: Recoverable anomalies (retry attempt 3 of 3, slow query).
  - `ERROR`: Errors that require investigation (unexpected constraint violation, external service timeout).

### 7.2 Observability in Error Paths

When an error occurs, logs must provide enough context to diagnose:

```python
except DuplicatePurchaseException as e:
    logger.warning("Duplicate purchase detected", extra={
        "external_purchase_id": request.external_purchase_id,
        "prior_purchase_id": prior_purchase.id,
        "retry": True,  # Clients can safely retry
        "request_id": request_id,
    })
    # Return prior result
```

```python
except Exception as e:
    logger.exception("Unexpected error processing purchase", extra={
        "merchant_id": request.merchant_id,
        "user_id": request.user_id,
        "amount": str(request.amount),
        "error_type": type(e).__name__,
        "request_id": request_id,
    })
    # Raise 500 response
```

---

## 8. Error Testing Strategy

### 8.1 Test Each Error Path

For critical operations, test both success and failure:

```python
# test_users_api.py

def test_create_user_success(client, db):
    """Happy path: user created successfully."""
    response = client.post("/api/v1/users", json={
        "email": "alice@example.com",
        "password": "SecureP@ss123"
    })
    assert response.status_code == 201
    assert response.json()["email"] == "alice@example.com"

def test_create_user_duplicate_email(client, db):
    """Error path: duplicate email."""
    create_test_user(db, "alice@example.com")
    response = client.post("/api/v1/users", json={
        "email": "alice@example.com",
        "password": "SecureP@ss123"
    })
    assert response.status_code == 409
    body = response.json()
    assert body["error"]["code"] == "EMAIL_ALREADY_REGISTERED"
    assert "already registered" in body["error"]["message"]

def test_create_user_weak_password(client):
    """Error path: password too weak."""
    response = client.post("/api/v1/users", json={
        "email": "bob@example.com",
        "password": "weak"
    })
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "password" in body["error"]["details"]["violations"][0]["field"]

def test_create_user_invalid_email(client):
    """Error path: malformed email."""
    response = client.post("/api/v1/users", json={
        "email": "not-an-email",
        "password": "SecureP@ss123"
    })
    assert response.status_code == 400
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
```

### 8.2 Test Transaction Rollback

Ensure partial updates don't leak:

```python
def test_purchase_creation_rolls_back_on_error(db):
    """If cashback calculation fails, purchase is not created."""
    user = create_test_user(db)
    merchant = create_test_merchant(db)

    with pytest.raises(CashbackCalculationException):
        service.create_purchase(
            PurchaseRequest(
                external_purchase_id="ext_123",
                user_id=user.id,
                merchant_id=merchant.id,
                amount=Decimal("-100"),  # Invalid: triggers error
            ),
            db
        )

    # Verify purchase was not created
    purchase = db.query(Purchase).filter(
        Purchase.external_purchase_id == "ext_123"
    ).first()
    assert purchase is None

    # Verify wallet was not updated
    wallet = db.query(Wallet).filter(Wallet.user_id == user.id).first()
    assert wallet.pending_balance == Decimal("0")
```

### 8.3 Test Idempotency

```python
def test_duplicate_purchase_is_idempotent(db):
    """Re-submitting with same external_id returns same result."""
    user = create_test_user(db)
    merchant = create_test_merchant(db)

    # First request
    request = PurchaseRequest(
        external_purchase_id="ext_123",
        user_id=user.id,
        merchant_id=merchant.id,
        amount=Decimal("50.00"),
    )
    purchase_1 = service.create_purchase(request, db)

    # Second request (retry with same external_id)
    response = client.post("/purchases", json=request.model_dump())
    assert response.status_code == 200  # Success, not 409 Conflict
    purchase_2 = response.json()

    # Same result
    assert purchase_1.id == purchase_2["id"]
    assert purchase_1.external_purchase_id == purchase_2["external_purchase_id"]
```

---

## 9. Implementation Roadmap

### 9.1 Phase 1: Foundation (Current)

- ✅ Domain exceptions hierarchy
- ✅ API layer error handling and conversion
- ✅ Standard error response format and HTTP status codes

### 9.2 Phase 2: Robustness

- [ ] Global exception handler in FastAPI (catch-all for unexpected errors)
- [ ] Request ID injection and correlation logging
- [ ] Database transaction wrappers to ensure rollback on error
- [ ] Comprehensive error tests (happy paths + error paths for each operation)

### 9.3 Phase 3: Observability

- [ ] Structured logging with JSON output
- [ ] Error metrics (count by error code, rate of 5xx errors)
- [ ] Error tracing in logs (request_id → all related events)
- [ ] Alerting on unexpected error patterns (spikes in 5xx, database constraint violations)

### 9.4 Phase 4: Resilience

- [ ] Idempotency key framework (centralized handling of external ID duplicates)
- [ ] Retry logic in clients with exponential backoff
- [ ] Circuit breaker pattern for external service calls
- [ ] Graceful degradation (fallback responses when dependencies are unavailable)
