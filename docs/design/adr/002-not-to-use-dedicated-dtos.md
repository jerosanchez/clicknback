# ADR 002: Not to Use Dedicated DTOs for Service Boundaries

## Status

Accepted

## Context

In a layered architecture, each boundary between layers could in principle have its own dedicated data transfer object (DTO), resulting in a mapping chain like:

```text
HTTP Request → RequestSchema → ServiceDTO → PersistenceDTO → ORM Model → DB
```

The question is: should ClickNBack adopt this full DTO pattern at every layer boundary, or apply it selectively only where it delivers concrete value?

### Option 1: Full DTO Pattern at Every Layer Boundary

Each domain entity is represented by a distinct class per layer: one for the API contract, one for the service layer, one for the persistence layer.

```python
# app/users/schemas.py — API layer contract
class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str

# app/users/dtos.py — Service layer DTO
@dataclass
class CreateUserDTO:
    email: str
    hashed_password: str  # Password is already hashed here

# app/users/persistence_dtos.py — Persistence layer DTO
@dataclass
class UserRecord:
    id: UUID
    email: str
    hashed_password: str
    created_at: datetime

# app/users/services.py — Manually maps between layers
class UserService:
    def create_user(self, request: CreateUserRequest) -> UserRecord:
        dto = CreateUserDTO(
            email=request.email,
            hashed_password=self.hash_password(request.password),
        )
        record = self.repository.save(dto)  # repo maps DTO → ORM model
        return UserRecord(...)              # repo maps ORM model → record DTO
```

- ✅ Maximum decoupling: each layer is fully independent of other layers' representations
- ✅ Schema changes in one layer do not automatically propagate to others
- ❌ 3–5× more model definitions per entity — a single `User` entity needs four classes
- ❌ Mapping boilerplate is mechanical and error-prone; every added field must be updated in every DTO class
- ❌ In Python, the runtime type system does not enforce these boundaries anyway — the indirection adds code without enforcement

### Option 2: Selective DTOs — Validate at the Boundary that Matters

Apply Pydantic schemas only at the API boundary (where validation and documentation are needed) and ORM models only at the persistence boundary (where database typing is needed). Omit a dedicated layer in the middle; services receive plain Python dicts or pass ORM models directly.

```python
# app/users/schemas.py — Pydantic schema only at the API boundary
class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: UUID
    email: str
    created_at: datetime

# app/users/services.py — Receives dict; no intermediate DTO
class UserService:
    def create_user(self, data: dict, db: Session) -> User:
        if self.user_repository.get_by_email(db, data["email"]):
            raise EmailAlreadyRegisteredException(data["email"])
        self.enforce_password_complexity(data["password"])
        user = User(
            email=data["email"],
            hashed_password=self.hash_password(data["password"]),
        )
        return self.user_repository.add(db, user)

# app/users/api.py — Pydantic validates input, service returns ORM model
@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(
    data: CreateUserRequest,
    service: UserService = Depends(get_user_service),
    db: Session = Depends(get_db),
):
    return service.create_user(data.model_dump(), db)
```

- ✅ Validation and OpenAPI documentation generated automatically at the API boundary
- ✅ ORM models provide typed, queryable objects at the persistence boundary
- ✅ Services focus on business logic, not mapping; adding a field requires one change, not four
- ✅ Consistent with how the FastAPI + Pydantic + SQLAlchemy stack is designed to work
- ❌ Services receive `dict` — less discoverable than typed objects for IDE autocompletion
- ❌ Weaker compile-time isolation between service and persistence layers; ORM model changes are visible to services

## Decision

Apply DTOs **selectively**, at the two boundaries where they provide measurable value:

1. **API layer → Service layer:** Pydantic schemas (`CreateUserRequest`, `UserResponse`) validate and document the HTTP contract. FastAPI invokes Pydantic automatically on every request and response. The schema's `.model_dump()` produces the `dict` passed to the service.

2. **Service layer → Repository layer:** SQLAlchemy `Mapped` ORM models carry typed, queryable objects. Repositories accept and return ORM model instances. FastAPI's `response_model=` parameter invokes Pydantic serialisation on the returned ORM model, so no explicit mapping is needed at the response path.

3. **Service layer itself:** Services receive `dict` from the API layer and return ORM model instances. No intermediate service DTO class is introduced. Business logic — validation rules, exception raising, data transformation — lives in the service method body, not in a mapping step.

This means the full transformation chain for a `POST /users` request is:

```text
HTTP JSON body → Pydantic validates → dict → UserService.create_user() → User ORM model → Pydantic serialises → HTTP JSON response
```

No DTO class exists between the `dict` and the `User` ORM model; the service constructs the `User` directly.

## Consequences

- ✅ One model definition per purpose: one Pydantic schema for API contracts, one SQLAlchemy model for persistence — not four classes per entity.
- ✅ Adding a new field requires updating the Pydantic schema and the SQLAlchemy model; no intermediate DTO update required.
- ✅ API contracts are explicit and automatically documented through Pydantic + FastAPI's OpenAPI generation.
- ✅ Business logic in services is readable: method bodies contain decisions and transformations, not mapping boilerplate.
- ⚠️ Services receive `dict` — field access via `data["email"]` is less IDE-discoverable than `data.email`; a typo is a `KeyError` at runtime rather than a type error at check time.
- ⚠️ ORM model fields are visible to the service layer — a database column rename is reflected in service code directly; this is considered acceptable given the scope of the project.
- ⚠️ If the service layer diverges significantly from both the API and persistence representations (e.g., complex aggregations or projections), a targeted service DTO may be introduced for that specific case without applying it universally.

## Alternatives Considered

### Full DTO Pattern at Every Layer Boundary

- **Pros:** Maximum layer decoupling; changes to the persistence schema do not automatically appear in the service interface.
- **Cons:** Requires maintaining 3–5 model classes per entity with mechanical mapping between them. In a codebase where the team is small and the domain evolves quickly, this mapping boilerplate degrades velocity and introduces mapping bugs without providing runtime enforcement — Python will not catch a missing field assignment.
- **Rejected:** The overhead is disproportionate at this stage. If the API and persistence representations diverge significantly for a specific entity, a targeted DTO for that entity can be introduced without adopting the pattern universally.

### Shared Model Across All Layers (Single Class)

- **Pros:** Absolute minimum boilerplate: one class used at the HTTP, service, and database levels.
- **Cons:** A class that serves all three purposes accumulates responsibilities: ORM annotations, Pydantic validators, and business methods all on the same object. A response field that must be hidden from the database (or vice versa) requires workarounds. FastAPI's `response_model` filtering provides some protection but is not sufficient for complex cases.
- **Rejected:** Conflating API contract, domain object, and database record into one class violates the single-responsibility principle in a way that compounds over time. Selective DTOs address this without the full overhead of the four-layer pattern.

## Rationale

Python's type system and FastAPI's design make the full DTO pattern largely unnecessary for the typical CRUD-heavy surface of a cashback management API. Pydantic schemas enforce and document the API contract. SQLAlchemy models enforce and document the persistence contract. The gap in between — the service layer — contains business decisions, not data mappings; a `dict` is the appropriate medium for passing raw validated inputs into a layer that will decide what to do with them.

The pattern can be revisited when a specific entity's service representation diverges meaningfully from both its API schema and its database record, at which point a localised service DTO is the right fix, not a universal policy change.
