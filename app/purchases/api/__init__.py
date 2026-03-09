from app.purchases.api import admin, public

admin_router = admin.router
public_router = public.router

__all__ = ["admin_router", "public_router"]
