# ADR 002: Not to Use Dedicated DTOs for Service Boundaries

## Status

Accepted

## Context

In layered architectures, full DTO patterns require multiple model definitions per entity:

```
Request → RequestDTO → ServiceDTO → PersistenceDTO → ORM Model
(API)    (API layer)  (Service)    (Repository)      (DB)
```

**Full DTO Pattern Costs/Benefits:**
- ✅ Maximum decoupling between layers
- ❌ 3-5x more code per entity
- ❌ Mapping boilerplate everywhere
- ❌ Hard to maintain when schemas change

**Python Pragmatism:**
Python's dynamic typing + Pydantic validation make strict DTO layers less necessary than statically-typed languages.

## Decision

Use **selective DTOs** with pragmatism:

### API Layer: Pydantic Schemas (✅ Use DTOs)

```python
# app/users/schemas.py - Validate at API boundary
from pydantic import BaseModel, EmailStr

class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Min 8 characters')
        return v

class UserResponse(BaseModel):
    id: str
    email: str
    created_at: datetime
```

**Why:** Pydantic provides validation, error messages, and OpenAPI documentation automatically.

### Service Layer: Plain Dicts (❌ Skip DTOs)

```python
# app/users/services.py - Services receive untyped dicts
class UserService:
    def create_user(self, data: dict, repo: UserRepository) -> User:
        # Business logic, not mapping
        if not policy.is_complex_enough(data['password']):
            raise PasswordNotComplexEnoughException()
        user = User(**data)
        return repo.add(user)
```

**Why:** Flexibility. Services don't care about schema details of API/DB layers.

### Repository Layer: ORM Models (✅ Use DTOs)

```python
# app/users/repositories.py - Return typed models
class UserRepository:
    def add(self, user: User) -> User:
        db.add(user)
        db.commit()
        db.refresh(user)
        return user  # Typed, queryable
```

**Why:** ORM models provide queryable, strongly-typed objects.

## Consequences

- ✅ Less boilerplate—one schema per endpoint, not 3+ per entity
- ✅ Faster feature development
- ✅ Type safety where it matters (API contracts)
- ✅ Flexibility in service layer
- ⚠️ Weaker decoupling between service and persistence
- ⚠️ Less IDE completion for dict[key] vs. obj.property
- ⚠️ Refactoring to strict DTOs is harder later

## What NOT to Do

### Anti-Pattern: Over-DTOing

Don't create 5 separate DTO classes per entity. Too much mapping boilerplate.

### Anti-Pattern: No Validation

Don't skip Pydantic schemas at the API boundary. Validation is essential.

## Rationale

**Pragmatism wins for this project stage:**

- **API Layer (Pydantic):** Validation and documentation are cheap and provide huge value
- **Service Layer (Dicts):** Simple, flexible, business-logic-focused
- **Repository Layer (ORM):** Typed, queryable, leverages SQLAlchemy's power

**Cost/Benefit:** Every service DTO would add ~50 LOC per entity. Benefit? Decoupling ORM details.
**Better way:** Use type hints and documentation instead.

**Revisit if:**
- Schema changes become painful (signals API design problem, not DTO problem)
- Business logic diverges dramatically from ORM structure
- Team grows and needs strict boundaries (time for DDD or microservices)
