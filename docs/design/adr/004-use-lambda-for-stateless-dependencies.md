# ADR 004: Use Callable Injection for Stateless Dependencies

## Status

Accepted

## Context

Services in ClickNBack routinely depend on utility functions: hashing passwords, enforcing complexity rules, generating tokens. These utilities are pure functions — they hold no state and require no lifecycle management. The question is: should these be wrapped in objects and injected as class instances, or injected directly as callables?

### Option 1: Wrap in a Class and Inject the Object

```python
# app/users/password_utils.py
class PasswordHasher:
    def hash(self, password: str) -> str:
        return pwd_context.hash(password)

class PasswordComplexityPolicy:
    def enforce(self, password: str) -> None:
        if len(password) < 8:
            raise PasswordNotComplexEnoughException("Min 8 chars")
        if not any(c.isupper() for c in password):
            raise PasswordNotComplexEnoughException("Need uppercase")

# app/users/services.py
class UserService:
    def __init__(
        self,
        hasher: PasswordHasher,
        policy: PasswordComplexityPolicy,
        user_repository: UserRepository,
    ):
        self.hasher = hasher
        self.policy = policy
        self.repository = user_repository

    def create_user(self, data: dict, db: Session) -> User:
        self.policy.enforce(data["password"])
        hashed_pw = self.hasher.hash(data["password"])
        ...

# Tests must instantiate throwaway objects just to mock one method
mock_hasher = Mock(spec=PasswordHasher)
mock_hasher.hash.return_value = "hashed_pw"
```

- ✅ Familiar pattern from Java/C# codebases; easy to understand for OOP-trained developers
- ✅ Can carry configuration state if needed later (e.g., `PasswordHasher(rounds=12)`)
- ❌ Extra class definitions for what is conceptually a single function
- ❌ Two-level call syntax: `self.hasher.hash(pw)` vs. `self.hash_password(pw)`
- ❌ Test mocks require `Mock(spec=ClassName)` and method-level setup even for a trivial function

### Option 2: Inject Callables Directly (Functions or Lambdas)

```python
# app/users/policies.py
def enforce_password_complexity(password: str) -> None:
    """Raises PasswordNotComplexEnoughException if the password is too weak."""
    if len(password) < 8:
        raise PasswordNotComplexEnoughException("Min 8 chars")
    if not any(c.isupper() for c in password):
        raise PasswordNotComplexEnoughException("Need uppercase")

# app/users/services.py
class UserService:
    def __init__(
        self,
        enforce_password_complexity: Callable[[str], None],
        hash_password: Callable[[str], str],
        user_repository: UserRepository,
    ):
        self.enforce_password_complexity = enforce_password_complexity
        self.hash_password = hash_password
        self.repository = user_repository

    def create_user(self, data: dict, db: Session) -> User:
        self.enforce_password_complexity(data["password"])
        hashed_pw = self.hash_password(data["password"])
        user = User(email=data["email"], hashed_password=hashed_pw)
        return self.repository.add(db, user)

# Tests replace each callable with a Mock — no class setup required
mock_enforce = Mock()  # No-op by default
mock_hash = Mock(return_value="hashed_pw")
```

- ✅ Direct, Pythonic: Python treats functions as first-class values; wrapping them in classes adds no value
- ✅ Flat call syntax: `self.hash_password(pw)` reads as natural prose
- ✅ Fast to mock: `Mock()` replaces the callable directly; no spec class or method-level stub needed
- ✅ Consistent with FastAPI's own idioms — `Depends()` already accepts plain functions
- ❌ If a utility later requires configuration state, it must be converted to a partial, closure, or class — a one-time refactor, but a refactor nonetheless

## Decision

For **stateless dependencies** — those with no configuration state and no lifecycle requirements — inject as plain callables (`Callable[[ArgType], ReturnType]`), never as class instances.

The wiring in `api.py` (the composition root per ADR 003) constructs the callable from infrastructure:

```python
# app/users/api.py
from passlib.context import CryptContext
from app.users.policies import enforce_password_complexity

pwd_context = CryptContext(schemes=["bcrypt"])

def get_user_service(
    user_repository: UserRepository = Depends(get_user_repository),
) -> UserService:
    return UserService(
        enforce_password_complexity=enforce_password_complexity,
        hash_password=lambda pw: pwd_context.hash(pw),
        user_repository=user_repository,
    )
```

The `lambda` at the composition root is the only place that knows about `passlib`. The service knows only that it receives something callable with signature `(str) -> str`.

### Testing with Injected Callables

```python
# tests/users/test_user_service.py
import pytest
from unittest.mock import Mock
from app.users.services import UserService
from app.users.exceptions import PasswordNotComplexEnoughException

@pytest.fixture
def enforce_password_complexity():
    return Mock()  # No-op — does not raise by default

@pytest.fixture
def hash_password():
    return Mock(return_value="hashed_pw")

@pytest.fixture
def user_service(user_repository, enforce_password_complexity, hash_password):
    return UserService(
        enforce_password_complexity=enforce_password_complexity,
        hash_password=hash_password,
        user_repository=user_repository,
    )

def test_create_user_raises_when_password_too_weak(
    user_service, enforce_password_complexity
):
    enforce_password_complexity.side_effect = PasswordNotComplexEnoughException("Min 8 chars")

    with pytest.raises(PasswordNotComplexEnoughException):
        user_service.create_user({"email": "a@b.com", "password": "weak"}, db=Mock())
```

## Consequences

- ✅ No unnecessary wrapper classes — each policy or utility is a single named function in a well-named module.
- ✅ Services are trivially testable: replace any callable with a `Mock()` fixture in one line, no `spec=` or method setup.
- ✅ The composition root is the only module that imports third-party hashing libraries; services are isolated from infrastructure details.
- ✅ Clean type annotations: `Callable[[str], str]` documents both the intent and the interface without a class hierarchy.
- ⚠️ If a callable dependency later needs to carry configuration (e.g., `bcrypt_rounds` from `settings`), it must be converted to a closure, `functools.partial`, or a class with `__call__`. This is a localised change in `policies.py` and `api.py` only.
- ⚠️ IDEs provide less autocomplete for `data["password"]` than for a typed class attribute; this is mitigated by using `Callable` type annotations everywhere.

## Alternatives Considered

### Inject Class Instances (Strategy Pattern)

- **Pros:** Familiar in OOP-heavy codebases; easy to extend with multiple implementations (e.g., `BcryptHasher`, `Argon2Hasher`); can carry configuration state without refactoring.
- **Cons:** Unnecessary indirection for a function that has exactly one implementation at any given time; doubles the definition cost (class + method vs. function); test mocks require more setup; violates "simple is better than complex" for this use case.
- **Rejected:** Python's first-class functions are the idiomatic mechanism for this pattern. A class wrapping a single method is a deferred complication, not a design improvement. If multiple implementations or state are needed, refactoring to a class at that point is the right trigger — not anticipating it prematurely.

### Hardcode Dependencies Inside the Service

- **Pros:** Zero wiring code — the service just calls `bcrypt.hash(pw)` directly.
- **Cons:** The service is coupled to the concrete library; the hashing implementation cannot be swapped without modifying the service; unit tests either run the real bcrypt (slow) or patch at the module level (fragile).
- **Rejected:** Hardcoded dependencies violate the testability and decoupling goals of the modular architecture. Even if the implementation never changes, the ability to inject a `Mock()` in tests is worth the minimal wiring cost.

## Rationale

Python's `Callable` type is the correct abstraction for a pure function dependency. A function that takes a `str` and returns a `str` does not need a class to describe it — its signature is its contract. Injecting the function directly keeps the service's `__init__` honest: the names (`enforce_password_complexity`, `hash_password`) document what each dependency does, and the `Callable` type annotation documents the expected signature.

This decision is consistent with how FastAPI's own `Depends()` mechanism works — it accepts plain functions, not objects — and with ClickNBack's broader principle of preferring explicit, minimal constructs over speculative abstraction.
