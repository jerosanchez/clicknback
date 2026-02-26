# ADR 000: Technology Stack Selection

## Status

Accepted

## Context

ClickNBack is a cashback-management API backend that must handle financial transactions, user authentication, and merchant integrations. The first major decision is: which language, web framework, ORM, and testing tooling should form the foundation of the codebase?

The choice must satisfy several concrete requirements:

- **Async-capable I/O** — the backend will serve concurrent requests from web and mobile clients.
- **Strong type safety** — financial logic must be explicit and verifiable through the tool chain.
- **Built-in API documentation** — OpenAPI / Swagger is expected by third-party integrators.
- **Composable dependency injection** — services, repositories, and policies must be wirable without a heavyweight DI framework.
- **Mature database migration tooling** — schema changes must be applied safely and consistently across environments.

### Option 1: Python / FastAPI / SQLAlchemy / pytest

```python
# A single type annotation flows through all layers
class UserResponse(BaseModel):   # Pydantic schema
    id: UUID
    email: str
    created_at: datetime

class User(Base):                # SQLAlchemy model
    __tablename__ = "users"
    id: Mapped[UUID] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: UUID, service: UserService = Depends()):
    return service.get_by_id(user_id)
```

- ✅ Native async/await support through Starlette/ASGI
- ✅ Automatic OpenAPI documentation and interactive Swagger UI
- ✅ Built-in dependency injection via `Depends()` — no external DI framework needed
- ✅ Type annotations shared across ORM model, validation schema, and API response
- ✅ Alembic generates and runs migrations directly from SQLAlchemy models
- ✅ pytest fixtures provide clean, composable dependency injection for tests
- ❌ Python is slower than compiled languages for CPU-intensive tasks
- ❌ Runtime environment management (venv, packaging) requires discipline

### Option 2: TypeScript / Node.js (Express + TypeORM + Jest)

```typescript
@Entity()
class User {
  @PrimaryGeneratedColumn("uuid") id: string;
  @Column({ unique: true }) email: string;
}

app.get("/users/:id", async (req, res) => {
  const user = await userRepo.findOneBy({ id: req.params.id });
  res.json(user);
});
```

- ✅ Single language across frontend and backend
- ✅ Strong static typing via TypeScript compiler
- ❌ No built-in DI or API documentation generation — requires additional libraries
- ❌ Ecosystem fragmentation (many competing ORM, validation, and test libraries)
- ❌ Async model (callbacks, promises, event loop) is harder to reason about for data-heavy CRUD

### Option 3: Go (Echo/Gin + GORM)

```go
type User struct {
    gorm.Model
    Email string `gorm:"uniqueIndex" json:"email"`
}

func GetUser(c echo.Context) error {
    var user User
    db.First(&user, c.Param("id"))
    return c.JSON(200, user)
}
```

- ✅ Compiled binary — very fast startup and execution
- ✅ Simple concurrency model with goroutines
- ❌ Verbose error handling (`if err != nil`) adds significant boilerplate for CRUD logic
- ❌ No automatic API documentation or built-in DI
- ❌ Slower iteration cycle for schema-heavy domains; GORM reflection is less ergonomic than SQLAlchemy

### Option 4: Python / Django + Django ORM

```python
class User(models.Model):
    email = models.EmailField(unique=True)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email"]
```

- ✅ Batteries-included: admin UI, auth, migrations, ORM in one package
- ✅ Massive community and documentation
- ❌ Monolithic and opinionated; domain-driven decomposition requires fighting the framework
- ❌ Synchronous by default; async support is bolted on and incomplete
- ❌ Django REST Framework adds a separate serializer layer, increasing mapping boilerplate

## Decision

Use **Python / FastAPI / SQLAlchemy 2.0 / Alembic / pytest** as the core technology stack.

1. **FastAPI** serves as the web framework — providing async routing, built-in dependency injection, and automatic OpenAPI documentation from type annotations alone.
2. **Pydantic v2** provides request/response validation and JSON schema generation; its model definitions are the single source of truth for API contracts.
3. **SQLAlchemy 2.0** with `Mapped` type annotations is the ORM — composable queries, explicit transactions, and full type-checker support.
4. **Alembic** manages database migrations, auto-generating them from SQLAlchemy model changes.
5. **pytest** with fixtures and `create_autospec()` is the testing framework — each layer is independently testable through dependency injection (see ADR 007).

The key architectural benefit is that **a single Python type annotation** flows from the database column through the ORM model, through the Pydantic schema, to the OpenAPI documentation — with no manual mapping at any boundary.

## Consequences

- ✅ Rapid development velocity: Python's expressiveness and FastAPI's ergonomics keep ceremony low.
- ✅ Type safety end-to-end: a field rename is caught by the type checker at every layer simultaneously.
- ✅ Automatic API documentation: Swagger UI is generated with zero additional code, which is essential for third-party merchant integrations.
- ✅ Async-first: ASGI + uvicorn supports high concurrency without thread-per-request overhead.
- ✅ One migration tool: Alembic's autogenerate removes the need to write SQL DDL manually for routine schema changes.
- ✅ Large hiring pool: FastAPI + SQLAlchemy is the dominant Python API stack; most Python engineers are familiar with it.
- ⚠️ Python is not a compiled language — deployment requires careful virtual environment management and Docker packaging.
- ⚠️ SQLAlchemy's ORM layer adds abstraction over raw SQL; complex analytical queries may require dropping to `text()` or raw SQL.

## Alternatives Considered

### Django + Django REST Framework

- **Pros:** Batteries-included, large community, built-in admin panel, mature migrations.
- **Cons:** Monolithic architecture fights ADR 001's modular domain structure; synchronous by default; DRF serializers duplicate Pydantic's role, adding a layer of boilerplate with no additional type safety.
- **Rejected:** FastAPI's modularity and native async are better aligned with the project's domain-driven approach and concurrency requirements.

### TypeScript / Node.js (Express + TypeORM + Jest)

- **Pros:** Shared language with any future frontend work; TypeScript static typing.
- **Cons:** No built-in DI or automatic API docs; fragmented ecosystem requires assembling and maintaining several competing libraries; async mental model (event loop, callbacks) is harder to reason about in data-heavy CRUD services.
- **Rejected:** Python's type-hint ecosystem achieves equivalent static analysis without compilation; FastAPI's DI and Pydantic provide what Node.js would require assembling manually.

### Go (Echo/Gin + GORM)

- **Pros:** Compiled binary; excellent execution speed and simple goroutine concurrency.
- **Cons:** Verbose error handling and lack of generics (prior to Go 1.18) make domain modelling tedious; no automatic API documentation; GORM's reflection-based mapping is less ergonomic than SQLAlchemy's `Mapped` annotations; smaller team familiarity.
- **Rejected:** The performance advantage does not justify the slower iteration speed and higher boilerplate for a CRUD-heavy financial management API at this stage; approach can be revisited if a specific hot path requires it.

### Flask + SQLAlchemy (Manual DI)

- **Pros:** Minimal magic; highly flexible.
- **Cons:** No built-in async support; dependency injection requires hand-rolled factories; no automatic API documentation; more boilerplate to achieve the same result as FastAPI.
- **Rejected:** FastAPI provides Flask's flexibility with async, built-in DI, and automatic OpenAPI — strictly better for this use case.

## Rationale

Python's `logging` principle applies here too: **choose the tool that is already doing the job well rather than assembling multiple tools to approximate it**. FastAPI, Pydantic, and SQLAlchemy 2.0 are the first Python trio where a type annotation written once is honoured by the web framework, the validator, the ORM, and the type checker simultaneously.

For a financial backend where correctness and auditability matter, this coherence is not merely a convenience — it reduces the class of bugs caused by mismatches between what the API promises and what the database stores. The stack is production-proven at scale (FastAPI powers parts of Netflix, Uber, and Stripe's Python services), has a large hiring pool, and is stable enough that the version choices made today will not require a major migration within the project's current horizon.
