from fastapi import APIRouter

from app.offers.api import (
    create_offer,
    get_offer_details,
    list_active_offers,
    list_offers,
    set_offer_status,
)

admin_router = APIRouter()
admin_router.include_router(create_offer.router)
admin_router.include_router(set_offer_status.router)

user_router = APIRouter()
user_router.include_router(list_offers.router)
user_router.include_router(list_active_offers.router)
user_router.include_router(get_offer_details.router)

__all__ = ["admin_router", "user_router"]
