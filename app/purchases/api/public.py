from decimal import Decimal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.current_user import get_current_user
from app.core.database import get_async_db
from app.core.errors.builders import (
    business_rule_violation_error,
    forbidden_error,
    internal_server_error,
    not_found_error,
    unprocessable_entity_error,
)
from app.core.logging import logging
from app.purchases.composition import get_purchase_service
from app.purchases.errors import ErrorCode
from app.purchases.exceptions import (
    DuplicatePurchaseException,
    InvalidPurchaseStatusException,
    MerchantInactiveException,
    MerchantNotFoundException,
    OfferNotAvailableException,
    PurchaseNotFoundException,
    PurchaseOwnershipViolationException,
    PurchaseViewForbiddenException,
    UnsupportedCurrencyException,
    UserInactiveException,
    UserNotFoundException,
)
from app.purchases.schemas import (
    PaginatedUserPurchaseOut,
    PurchaseCreate,
    PurchaseDetailsOut,
    PurchaseOut,
    UserPurchaseOut,
)
from app.purchases.services import PurchaseService
from app.users.models import User

router = APIRouter(prefix="/purchases", tags=["purchases"])
users_router = APIRouter(prefix="/users", tags=["purchases"])


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    description=(
        "Ingest a new purchase. This endpoint is idempotent with respect to "
        "external_id: re-submitting the same external_id yields a 409 Conflict "
        "with details of the previously ingested purchase."
    ),
)
async def ingest_purchase(
    data: PurchaseCreate,
    service: PurchaseService = Depends(get_purchase_service),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
) -> PurchaseOut:
    try:
        purchase = await service.ingest_purchase(
            data.model_dump(), str(current_user.id), db
        )

    except PurchaseOwnershipViolationException:
        logging.debug(
            "Purchase ownership violation: user attempted to ingest for another user.",
            extra={"user_id": str(current_user.id)},
        )
        raise forbidden_error(
            message="You can only ingest purchases on your own behalf.",
            details={
                "reason": "The user_id in the request does not match the authenticated user."
            },
        )

    except DuplicatePurchaseException as exc:
        logging.debug(
            "Duplicate purchase rejected.",
            extra={"external_id": exc.external_id},
        )
        raise business_rule_violation_error(
            code=ErrorCode.DUPLICATE_PURCHASE,
            message=(
                f"A purchase with external ID '{exc.external_id}' has already been processed."
            ),
            details={
                "external_id": exc.external_id,
                "previously_created_at": exc.created_at.isoformat(),
                "previously_processed_amount": str(exc.amount),
                "action": (
                    "This request is idempotent and safe to retry. "
                    "You will receive the same result."
                ),
            },
        )

    except (UserNotFoundException, UserInactiveException) as exc:
        logging.debug(
            "User not eligible during purchase ingestion.",
            extra={"user_id": exc.user_id},
        )
        raise unprocessable_entity_error(
            code=ErrorCode.USER_NOT_ELIGIBLE,
            message="User is not eligible to ingest purchases.",
            details={
                "user_id": exc.user_id,
                "reason": "Purchase cannot be ingested for users who are non-existent or inactive.",
            },
        )

    except (MerchantNotFoundException, MerchantInactiveException) as exc:
        logging.debug(
            "Merchant not eligible during purchase ingestion.",
            extra={"merchant_id": exc.merchant_id},
        )
        raise unprocessable_entity_error(
            code=ErrorCode.MERCHANT_NOT_ELIGIBLE,
            message="Merchant is not eligible to process purchases.",
            details={
                "merchant_id": exc.merchant_id,
                "reason": "Purchases cannot be processed for merchants who are non-existent or inactive.",
            },
        )

    except OfferNotAvailableException as exc:
        logging.debug(
            "No active offer found for merchant during purchase ingestion.",
            extra={"merchant_id": exc.merchant_id},
        )
        raise unprocessable_entity_error(
            code=ErrorCode.OFFER_NOT_AVAILABLE,
            message=(f"No active offer is available for merchant '{exc.merchant_id}'."),
            details={
                "merchant_id": exc.merchant_id,
                "reason": (
                    "Purchases cannot be processed without a valid active offer for the merchant."
                ),
            },
        )

    except UnsupportedCurrencyException as exc:
        logging.debug(
            "Unsupported currency rejected during purchase ingestion.",
            extra={"currency": exc.currency},
        )
        raise unprocessable_entity_error(
            code=ErrorCode.UNSUPPORTED_CURRENCY,
            message=f"Currency '{exc.currency}' is not supported. Only EUR is accepted at this time.",
            details={
                "currency": exc.currency,
                "reason": "The platform currently processes purchases in EUR only.",
            },
        )

    except Exception as e:
        logging.error(
            "An unexpected error occurred while ingesting a purchase.",
            extra={"error": str(e)},
        )
        raise internal_server_error()

    return PurchaseOut(
        id=purchase.id,
        status=purchase.status,
        cashback_amount=Decimal("0"),
    )


@users_router.get(
    "/me/purchases",
    description="List the authenticated user's own purchases, enriched with merchant names.",
)
async def list_user_purchases(
    page: int = Query(1, ge=1, description="Page number (1-based)."),
    page_size: int = Query(
        10, ge=1, le=100, description="Number of results per page (max 100)."
    ),
    status: str | None = Query(
        None, description="Filter by status: pending, confirmed, or reversed."
    ),
    service: PurchaseService = Depends(get_purchase_service),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
) -> PaginatedUserPurchaseOut:
    try:
        purchases_with_merchants, total = await service.list_user_purchases(
            db,
            str(current_user.id),
            status=status,
            page=page,
            page_size=page_size,
        )
    except InvalidPurchaseStatusException as e:
        raise unprocessable_entity_error(ErrorCode.INVALID_PURCHASE_STATUS, str(e))
    except Exception as e:
        logging.error(
            "An unexpected error occurred while listing user purchases.",
            extra={"error": str(e)},
        )
        raise internal_server_error()

    # TODO: set real cashback fields once the cashback module is implemented
    return PaginatedUserPurchaseOut(
        items=[
            UserPurchaseOut(
                id=purchase.id,
                merchant_name=merchant_name,
                amount=purchase.amount,
                status=purchase.status,
                cashback_amount=Decimal("0"),
                cashback_status=None,
                created_at=purchase.created_at,
            )
            for purchase, merchant_name in purchases_with_merchants
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{purchase_id}",
    description="Get details of a specific purchase. Only accessible by the purchase owner.",
)
async def get_purchase_details(
    purchase_id: str,
    service: PurchaseService = Depends(get_purchase_service),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
) -> PurchaseDetailsOut:
    try:
        purchase, merchant_name = await service.get_purchase_details(
            purchase_id, str(current_user.id), db
        )

    except PurchaseNotFoundException as exc:
        raise not_found_error(
            message=f"Purchase with ID '{exc.purchase_id}' does not exist.",
            details={
                "resource_type": "purchase",
                "resource_id": exc.purchase_id,
            },
        )

    except PurchaseViewForbiddenException as exc:
        logging.debug(
            "Purchase view forbidden: user attempted to view another user's purchase.",
            extra={"user_id": str(current_user.id), "purchase_id": exc.purchase_id},
        )
        raise forbidden_error(
            message="You do not have permission to view this purchase. Purchase belongs to another user.",
            details={
                "purchase_id": exc.purchase_id,
                "resource_owner": exc.resource_owner_id,
                "current_user": exc.current_user_id,
            },
        )

    except Exception as e:
        logging.error(
            "An unexpected error occurred while retrieving purchase details.",
            extra={"error": str(e)},
        )
        raise internal_server_error()

    # cashback fields will be wired to the cashback module once it is implemented
    return PurchaseDetailsOut(
        id=purchase.id,
        merchant_name=merchant_name,
        amount=purchase.amount,
        status=purchase.status,
        cashback_amount=Decimal("0"),
        cashback_status=None,
        created_at=purchase.created_at,
    )
