from app.purchases.api import admin, public

admin_router = admin.router
user_router = public.router
users_router = public.users_router

__all__ = ["admin_router", "user_router", "users_router"]
