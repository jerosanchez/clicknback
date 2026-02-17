# ADR-006: Store Limited-Value Fields as String, Not Enum

## Status

Accepted

## Context

For limited-value fields (role, status, type), two strategies exist:

### Strategy 1: Database ENUM Type

```sql
CREATE TYPE user_role AS ENUM ('admin', 'user', 'merchant');

CREATE TABLE users (
  id UUID PRIMARY KEY,
  role user_role NOT NULL
);
```

- ✅ Strong database constraints
- ❌ Schema migration required for every value change
- ❌ Migration downtime and complexity
- ❌ Hard to deprecate old values

### Strategy 2: Application-Level Validation (String Column)

```sql
CREATE TABLE users (
  id UUID PRIMARY KEY,
  role VARCHAR(50) NOT NULL
);
```

- ✅ Change valid values in code, no DB migration
- ✅ Easier to add/deprecate/rename values
- ✅ Flexible (list values can evolve dynamically)
- ❌ Database doesn't enforce constraints
- ❌ Requires discipline in application code

## Decision

Store limited-value fields as **strings in the database**, with **validation in application code**.

### Example: User Roles

```python
# app/users/models.py - ORM model
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

class User(Base):
    __tablename__ = \"users\"
    role: Mapped[str] = mapped_column(String(50), nullable=False)  # Just a string

# app/users/constants.py - Define allowed values
class UserRole:
    ADMIN = \"admin\"
    USER = \"user\"
    MERCHANT = \"merchant\"
    
    ALL = [ADMIN, USER, MERCHANT]  # Easy to iterate, extend

# app/users/schemas.py - Validate at API boundary
from pydantic import Field, field_validator

class UserResponse(BaseModel):
    role: str = Field(..., description=\"User role\")
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        if v not in UserRole.ALL:
            raise ValueError(f'Invalid role: {v}. Must be one of {UserRole.ALL}')
        return v

# app/users/api.py - Use in endpoints
@router.get(\"/users/{user_id}\", response_model=UserResponse)
async def get_user(user_id: str, service: UserService = Depends()):
    user = service.get_user(user_id)
    return user  # Pydantic validates on response
```

### Adding a New Role Later (Minimal Change)

```python
# Before: schema/db are unchanged
class UserRole:
    ADMIN = \"admin\"
    USER = \"user\"\n    MERCHANT = \"merchant\"  # Existing
    # NEW: just add a new value
    MODERATOR = \"moderator\"
    
    ALL = [ADMIN, USER, MERCHANT, MODERATOR]
```

No database migration needed. Code deployment = done.

## Consequences

- ✅ Add/remove/rename values without database migrations
- ✅ Faster iteration and deployment
- ✅ Can deprecate old values gradually
- ✅ Works for dynamic lists (roles per organization, capabilities, etc.)
- ⚠️ Database cannot enforce constraints natively
- ⚠️ Risk of invalid values if validation skipped
- ⚠️ Requires discipline: validation must happen at API layer

## What NOT to Do

### Anti-Pattern: Trusting Only Database Constraints

❌ **DON'T**

```python
# If you only rely on DB constraint, you can't change values without migration
class User(Base):
    role: str  # String column, but Pydantic never validates it
    
@router.get(\"/users/{user_id}\")
def get_user(user_id):
    user = db.query(User).get(user_id)
    return user  # Could have invalid value from direct DB update!
```

**Problem:** Database integrity is no longer guaranteed. One bad migration or direct query breaks everything.

### Anti-Pattern: Skip Validation Entirely

❌ **DON'T** Accept any string for role:

```python
@router.put(\"/users/{user_id}\")
def update_user(user_id: str, data: dict):
    user.role = data['role']  # No validation!
    db.add(user)
```

**Problem:** Invalid values sneak in. Hard to debug later.

## Rationale

**Flexibility > Database Constraints:**

For a young product, the ability to iterate quickly on enum values outweighs database enforcement. When requirements change (\"add a new role\", \"deprecate admin\"), you shouldn't need a database migration.

**Validation Still Required:** Just because constraints are in application code doesn't mean you skip validation. The API layer (Pydantic) must validate all inputs.

**Cost/Benefit:**

- Cost of application validation: Trivial—a few lines of Pydantic code
- Benefit of not needing DB migrations: Huge—deploy instantly, no downtime

**Revisit Triggers:**

- If invalid data becomes a frequent problem (signals testing gaps)
- If you need true row-level permissioning per value (may warrant a lookup table)
- If the system grows to many teams, each needing custom roles (might need a more flexible solution like a capabilities matrix)
