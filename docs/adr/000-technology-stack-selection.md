# ADR 000: Technology Stack Selection

## Status

Accepted

## Context

Building a backend system requires selecting technologies that support the project's growth trajectory, team productivity, and code quality. Key considerations include:

- **Language:** Python offers rapid development, strong typing via type hints, and an excellent ecosystem for web APIs and data processing
- **Web framework:** Must support async I/O, automatic API documentation, and intuitive dependency injection
- **ORM:** Must provide type safety, composable queries, and robust migration support
- **Testing:** Must be easy to use, support mocking, and integrate well with the chosen framework
- **Ecosystem integration:** Components should work seamlessly together, not require extensive glue code

## Decision

We will use the following core technologies for the backend:

### Web Framework: FastAPI

**Why:** Native async/await support, automatic OpenAPI documentation, intuitive dependency injection built-in, excellent type safety through Pydantic integration.

### Data Validation: Pydantic

**Why:** Strong validation through type hints, automatic error response generation, JSON schema integration with OpenAPI.

### ORM: SQLAlchemy 2.0

**Why:** Modern type-annotated ORM, composable queries, excellent migration support via Alembic, largest community of Python web developers.

### Database Migrations: Alembic

**Why:** SQLAlchemy-integrated, auto-generates migrations from models, supports complex schema changes, widely adopted standard.

### Testing: pytest

**Why:** Extensive plugin ecosystem, fixtures for dependency injection, excellent mocking support, industry standard for Python testing.

## Consequences

- ✅ Rapid development velocity through Python's dynamic features and extensive libraries
- ✅ Strong type safety throughout (from Pydantic fields to SQLAlchemy models to pytest fixtures)
- ✅ Excellent developer experience: automatic API docs, interactive Swagger UI, clear error messages
- ✅ Seamless integration: FastAPI ↔ Pydantic ↔ SQLAlchemy all use type hints as the primary interface
- ✅ Large community and extensive documentation for rapid problem-solving
- ✅ Async-first design enables high throughput with minimal infrastructure
- ⚠️ Python deployment requires careful environment management (not a compiled binary)
- ⚠️ ORM abstraction adds a layer vs. raw SQL (though this is a feature for CRUD-heavy systems)

## Alternatives Considered

### Django + Django ORM

- **Pros:** Batteries-included, migrations, admin UI, large community
- **Cons:** Monolithic, opinionated, overkill for API-first services, slower development cycle
- **Rejected:** Over-engineered for our use case; FastAPI's modularity better aligns with domain-driven design

### Flask + SQLAlchemy (Manual DI)

- **Pros:** Lightweight, minimal magic
- **Cons:** No built-in async, manual dependency injection, no automatic API docs
- **Rejected:** More boilerplate; FastAPI provides same flexibility with better DX

### TypeScript/Node.js (Express + Typeorm)

- **Pros:** Single language across frontend/backend  
- **Cons:** JavaScript ecosystem fragmentation, debugging complexity, slower execution
- **Rejected:** Python's type safety through type hints rivals TypeScript without requiring compilation

### Go (Echo/Gin + GORM)

- **Pros:** Fast execution, simple concurrency model
- **Cons:** Steeper learning curve, verbose error handling, less suitable for data-heavy CRUD
- **Rejected:** Overkill for current project size; Python's rapid iteration speed higher priority than raw execution speed

## Rationale

This stack strikes a balance between **developer productivity**, **code quality**, and **operational simplicity**:

- **Type Safety:** FastAPI + Pydantic + SQLAlchemy is the most cohesive type-safe Python stack available. A single type annotation flows from database schema → ORM model → validation schema → API response.

- **Learning Curve:** Python syntax is readable even for junior developers. FastAPI's documentation is excellent. The ecosystem is mature and stable.

- **Real-World Adoption:** This stack is proven in production at Netflix, Uber, Stripe, and many others. It's the industry standard for Python APIs.

- **Future Flexibility:** If performance becomes critical, services can be extracted to Go/Rust with Python orchestration. The modular monolith approach (ADR 001) supports this.

- **Scalability:** Async I/O and connection pooling support high throughput. SQLAlchemy handles complex queries efficiently. Alembic supports zero-downtime migrations.

This choice enables us to move fast while maintaining code quality and providing a strong foundation for growth.
