from fastapi import FastAPI

from app.auth import api as auth_api
from app.core.errors.handlers import register_error_handlers
from app.merchants import api as merchants_api
from app.users import api as users_api

app = FastAPI()

# Register custom error handlers to ensure all exceptions are handled consistently
register_error_handlers(app)

app.include_router(users_api.router)
app.include_router(auth_api.router)
app.include_router(merchants_api.router)
