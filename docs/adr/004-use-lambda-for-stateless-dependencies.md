# ADR 004: Use Lambda Injection for Stateless Dependencies

## Status

Accepted

## Context

Services frequently need utility dependencies: password hashers, validation policies, encryption functions. How should these be provided?

**Option 1: Inject Objects/Classes**
```python
class PasswordHasher:
    def hash(self, password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

class UserService:
    def __init__(self, hasher: PasswordHasher):
        self.hasher = hasher
    
    def create_user(self, data: dict) -> User:
        hashed = self.hasher.hash(data['password'])
        return User(hashed_password=hashed)
```

**Cost:** Extra object overhead for stateless utilities. More boilerplate.

**Option 2: Inject Callables (Functions/Lambdas)**
```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"])

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

class UserService:
    def __init__(self, hash_password: Callable[[str], str]):
        self.hash_password = hash_password
    
    def create_user(self, data: dict) -> User:
        hashed = self.hash_password(data['password'])
        return User(hashed_password=hashed)
```

**Benefits:** Simple, Pythonic, testable, no unnecessary classes.

## Decision

For **stateless dependencies**, inject as functions/callables, not objects:

### Example: Password Policy

```python
# app/users/policies.py
def enforce_password_complexity(password: str) -> None:
    \"\"\"Raises PasswordNotComplexEnoughException if weak\"\"\"
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
        # Use the injected functions
        self.enforce_password_complexity(data['password'])
        hashed_pw = self.hash_password(data['password'])
        
        user = User(
            email=data['email'],
            hashed_password=hashed_pw
        )
        return self.repository.add_user(db, user)

# app/users/api.py - Wire up dependencies
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"])

def get_user_service(repository: UserRepository = Depends(...)) -> UserService:
    return UserService(
        enforce_password_complexity=enforce_password_complexity,
        hash_password=lambda pw: pwd_context.hash(pw),
        user_repository=repository,
    )

@router.post("/")
async def create_user(
    data: CreateUserRequest,
    service: UserService = Depends(get_user_service),
):
    return service.create_user(data.model_dump())
```

### Testing with Mocked Functions

```python
# tests/users/test_users_services.py

@pytest.fixture
def enforce_password_complexity() -> Callable[[str], None]:
    return Mock()  # No-op for tests

@pytest.fixture
def hash_password() -> Callable[[str], str]:
    return Mock(return_value="hashed_pw")

def test_create_user_complex_password_required(
    enforce_password_complexity, hash_password, user_service
):
    # Arrange
    enforce_password_complexity.side_effect = PasswordNotComplexEnoughException()
    
    # Act & Assert
    with pytest.raises(PasswordNotComplexEnoughException):
        user_service.create_user({...})
```

## Consequences

- ✅ Pythonic: leverages Python's first-class functions
- ✅ Simple: no unnecessary class boilerplate
- ✅ Testable: easy to mock or swap implementations
- ✅ Decoupled: service isolated from infrastructure details
- ✅ Consistent with FastAPI idioms
- ⚠️ If dependency needs state later, must refactor to object

## What NOT to Do

### Anti-Pattern: Class for Everything

Don't create a class for a single function:

```python
# BAD
class PasswordComplexityEnforcer:
    def enforce(self, password: str) -> None:
        if len(password) < 8:
            raise Exception()

# GOOD
def enforce_password_complexity(password: str) -> None:
    if len(password) < 8:
        raise Exception()
```

### Anti-Pattern: Skip Injection Entirely

Don't hardcode dependencies:

```python
# BAD
class UserService:
    def create_user(self, data: dict):
        bcrypt.hashpw(...)  # Not testable
        send_email(...)     # Hard to mock
```

## Rationale

This approach aligns with **Pythonic principles**:

- **Explicit is better than implicit:** Functions make dependencies obvious
- **Simple is better than complex:** No unnecessary class indirection
- **Practicality beats purity:** Testability and flexibility without boilerplate

**Cost/Benefit:**
- Cost of injecting functions: Zero additional code vs. classes
- Benefit: Easier testing, simpler code, fewer objects in memory

**When to use objects instead:**
- Dependency has state (configuration, cached values)
- Dependency has multiple related functions (strategy pattern)
- Dependency needs lifecycle management (close connections, cleanup)

**Example of when NOT to use functions:**
```python
class DatabaseConnection:
    def __init__(self, connection_string: str):
        self.conn = psycopg2.connect(connection_string)
    
    def query(self, sql: str):
        return self.conn.execute(sql)
    
    def close(self):
        self.conn.close()

# This HAS STATE and LIFECYCLE -> use class, don't use function
```

