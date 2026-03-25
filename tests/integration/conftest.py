"""
Shared fixtures for integration tests.

Requires a PostgreSQL instance reachable at TEST_DATABASE_URL (defaults to the
value in .env.test if present, otherwise falls back to the environment variable).

Isolation strategy
------------------
Each test runs inside an outer connection-level transaction that is rolled back
on teardown.  Services call ``uow.commit()`` which, via
``join_transaction_mode="create_savepoint"``, creates and releases a savepoint
rather than committing the outer transaction.  All writes stay visible within
the test but nothing persists after the test ends.
"""

import os
import uuid
from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

import app.models  # noqa: F401 — registers all ORM models with Base.metadata
from app.auth.models import TokenPayload
from app.auth.token_provider import JwtOAuth2TokenProvider
from app.core.database import Base, get_async_db
from app.main import app
from app.users.models import User, UserRoleEnum

# ---------------------------------------------------------------------------
# Engine — built once per process from TEST_DATABASE_URL
# ---------------------------------------------------------------------------

_TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://user:pass@localhost:5432/clicknback_test",
)

_engine = create_async_engine(_TEST_DATABASE_URL, echo=False)

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_token_provider = JwtOAuth2TokenProvider()

# ---------------------------------------------------------------------------
# Session-scoped table management
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_tables() -> AsyncGenerator[None, None]:
    """Create all tables once per test session; drop them on teardown."""
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await _engine.dispose()


# ---------------------------------------------------------------------------
# Function-scoped DB session with automatic rollback
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture()
async def db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yields an AsyncSession joined to an open connection-level transaction.

    ``join_transaction_mode="create_savepoint"`` ensures that calls to
    ``session.commit()`` inside the service layer create and release a
    savepoint instead of committing the outer transaction.  The outer
    transaction is rolled back on teardown, leaving the database clean.
    """
    async with _engine.connect() as conn:
        await conn.begin()
        session = AsyncSession(
            bind=conn,
            join_transaction_mode="create_savepoint",
            expire_on_commit=False,
        )
        yield session
        await session.close()
        await conn.rollback()


# ---------------------------------------------------------------------------
# Helper: create a user directly in the test session
# ---------------------------------------------------------------------------


async def create_user(
    db: AsyncSession,
    *,
    role: UserRoleEnum = UserRoleEnum.user,
    email: str | None = None,
    password: str = "ValidPass1!",
) -> tuple[User, str]:
    """
    Insert a User row into the test session and return (user, plain_password).

    The returned plain_password can be used in login requests.
    """
    user_id = str(uuid.uuid4())
    resolved_email = email or f"user-{user_id[:8]}@example.com"
    user = User(
        id=user_id,
        email=resolved_email,
        hashed_password=_pwd_context.hash(password),
        role=role,
        active=True,
    )
    db.add(user)
    await db.flush()
    return user, password


def make_token(user: User) -> str:
    """Generate a real JWT for the given user."""
    return _token_provider.create_access_token(
        TokenPayload(user_id=str(user.id), user_role=str(user.role.value))
    )


# ---------------------------------------------------------------------------
# Base HTTP client (unauthenticated)
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture()
async def http_client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Unauthenticated httpx.AsyncClient wired to the FastAPI app.

    Overrides get_async_db so every request uses the rolled-back test session.
    """

    async def _override_get_async_db() -> AsyncGenerator[AsyncSession, None]:
        yield db

    app.dependency_overrides[get_async_db] = _override_get_async_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Authenticated HTTP clients
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture()
async def user_http_client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Authenticated httpx.AsyncClient with a regular-user Bearer token.

    Creates a real user in the test session and attaches their JWT to every
    request via the Authorization header.
    """
    user, _ = await create_user(db, role=UserRoleEnum.user)
    token = make_token(user)

    async def _override_get_async_db() -> AsyncGenerator[AsyncSession, None]:
        yield db

    app.dependency_overrides[get_async_db] = _override_get_async_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as client:
        yield client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture()
async def admin_http_client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Authenticated httpx.AsyncClient with an admin Bearer token.

    Creates a real admin user in the test session and attaches their JWT to
    every request via the Authorization header.
    """
    user, _ = await create_user(db, role=UserRoleEnum.admin)
    token = make_token(user)

    async def _override_get_async_db() -> AsyncGenerator[AsyncSession, None]:
        yield db

    app.dependency_overrides[get_async_db] = _override_get_async_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as client:
        yield client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture()
async def user_http_client_with_user(
    db: AsyncSession,
) -> AsyncGenerator[tuple[AsyncClient, "User"], None]:
    """
    Like user_http_client but yields (client, user) so tests can access the
    user's ID (required e.g. when the request body must carry the user's own ID).
    """
    user, _ = await create_user(db, role=UserRoleEnum.user)
    token = make_token(user)

    async def _override_get_async_db() -> AsyncGenerator[AsyncSession, None]:
        yield db

    app.dependency_overrides[get_async_db] = _override_get_async_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as client:
        yield client, user
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Re-export helpers for use in test files
# ---------------------------------------------------------------------------

__all__ = [
    "create_tables",
    "db",
    "http_client",
    "user_http_client",
    "admin_http_client",
    "user_http_client_with_user",
    "create_user",
    "make_token",
]
