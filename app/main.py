from fastapi import FastAPI

from app.core.error_handlers import register_error_handlers
from app.users import api as users_api

app = FastAPI()

# Register custom error handlers to ensure all exceptions are handled consistently
register_error_handlers(app)

app.include_router(users_api.router)
