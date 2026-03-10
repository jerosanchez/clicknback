from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from app.auth import api as auth_api
from app.core.errors.handlers import register_error_handlers
from app.core.health import router as health_router
from app.core.scheduler import InMemoryTaskScheduler
from app.merchants import api as merchants_api
from app.offers.api import admin_router as offers_admin_router
from app.offers.api import public_router as offers_public_router
from app.purchases.api import admin_router as purchases_admin_router
from app.purchases.api import public_router as purchases_public_router
from app.users import api as users_api

# ----- Lifespan and infrastructure

# Schedule background jobs and other infrastructure components here.
scheduler = InMemoryTaskScheduler()

# Example: schedule a job to verify pending purchases every 30 seconds.
# The job function is not implemented yet, but this shows where and how to schedule
# it in the composition root:

# scheduler.schedule("verify_purchases", verify_pending_purchases, interval_seconds=settings.verify_purchases_interval_seconds)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await scheduler.start()  # spawns background asyncio Tasks
    yield
    await scheduler.stop()  # cancels them cleanly on shutdown


app = FastAPI(lifespan=lifespan)

# Register custom error handlers to ensure all exceptions are handled consistently
register_error_handlers(app)

# ------ Middleware

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

# ------ API routers

# Health probes are registered without the /api/v1 prefix because they are
# infrastructure endpoints consumed by Docker, Nginx, and the CD pipeline.
app.include_router(health_router)

# API routers for `api/v1` endpoints.
app.include_router(users_api.router, prefix="/api/v1")
app.include_router(auth_api.router, prefix="/api/v1")
app.include_router(merchants_api.router, prefix="/api/v1")
app.include_router(offers_admin_router, prefix="/api/v1")
app.include_router(offers_public_router, prefix="/api/v1")
app.include_router(purchases_admin_router, prefix="/api/v1")
app.include_router(purchases_public_router, prefix="/api/v1")
