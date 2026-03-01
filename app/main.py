from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth import api as auth_api
from app.core.errors.handlers import register_error_handlers
from app.merchants import api as merchants_api
from app.users import api as users_api

app = FastAPI()

# Register custom error handlers to ensure all exceptions are handled consistently
register_error_handlers(app)

# CORS: allow the production origin explicitly; localhost variants are permitted
# during local development via regex. Wildcard origins are never used.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://clicknback.com"],
    allow_origin_regex=r"http://localhost(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers for `api/v1` endpoints. Each router corresponds to a specific
# domain of functionality (users, auth, merchants, etc.).
app.include_router(users_api.router, prefix="/api/v1")
app.include_router(auth_api.router, prefix="/api/v1")
app.include_router(merchants_api.router, prefix="/api/v1")
