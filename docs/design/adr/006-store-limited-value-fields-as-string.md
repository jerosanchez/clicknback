# ADR 006: Store Limited-Value Fields as String, Not Enum

## Status

Accepted

## Context

ClickNBack has several fields that can only hold a small set of named values: user roles (`admin`, `user`, `merchant`), transaction statuses (`pending`, `confirmed`, `reversed`), and cashback states. The question is: where should the constraint on allowed values be enforced — at the database level through an ENUM type, or at the application level through code?

### Option 1: Database ENUM Type

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

### Option 2: Application-Level Validation (String Column)

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

Store limited-value fields as **VARCHAR strings in the database**, with **all constraint enforcement in application code** (Pydantic validators at the API boundary).

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

## Alternatives Considered

### PostgreSQL ENUM Type

- **Pros:** The database enforces valid values at the storage level; an invalid role can never be written even via a direct `psql` session or a buggy script.
- **Cons:** Adding or renaming a value requires a DDL migration (`ALTER TYPE ADD VALUE`). Removing a value requires creating a new type and migrating the column — a multi-step, potentially table-locking operation. PostgreSQL ENUM types cannot be altered inline in the same transaction as other DDL changes in some versions. For a young product iterating on its domain model, this migration overhead occurs frequently and carries real deployment risk.
- **Rejected:** The value of database-level constraint enforcement does not outweigh the migration cost during active product development. Application-level validation through Pydantic provides equivalent protection at the entry point where invalid values would originate.

### Python `enum.Enum` (Without Database ENUM)

```python
# Using Python's enum.Enum with a string column
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    MERCHANT = "merchant"

class User(Base):
    role: Mapped[str] = mapped_column(String(50))

class UserResponse(BaseModel):
    role: UserRole  # Pydantic validates against the enum
```

- **Pros:** Provides a typed Python constant for IDE autocompletion; `UserRole.ADMIN` is more discoverable than a plain string `"admin"`.
- **Cons:** `enum.Enum` in Python is less flexible than a plain constant class — adding a value requires modifying the enum, which in some serialisation libraries triggers strict validation on previously serialised `str` values that no longer match any member (e.g., data in the database that was written before a rename). Iterating over members for validation (`UserRole.ALL`) requires `.value` gymnastics.
- **Rejected:** A plain `UserRole` class with string constants and an `ALL` list provides all the discoverability benefits with none of the serialisation edge cases. Pydantic's `field_validator` on the `role` field provides the same constraint check more explicitly.

## Rationale

ClickNBack's domain model is actively evolving: new user roles, transaction statuses, and cashback states will be added, renamed, and deprecated as the product grows. Keeping constraint logic in application code rather than in the database schema means that deploying a new allowed value is a code change followed by a deployment — no migration, no downtime, no ALTER TYPE risk.

The trade-off is real: a direct database write bypassing the application can insert an invalid value. This risk is accepted because:

1. All writes in normal operation pass through the API layer, where Pydantic validation catches invalid values before they reach the database.
2. Direct database access (migrations, seed scripts) is performed by the development team and is covered by convention and code review.
3. If invalid data does appear, it is detectable via a simple query and correctable without schema changes.

The pattern should be revisited if invalid data from direct writes becomes a recurring operational problem — at that point a CHECK constraint (simpler than ENUM, migration-free for most changes) is the right escalation.
