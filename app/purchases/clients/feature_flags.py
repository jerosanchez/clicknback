"""Feature flags client for purchase auto-confirmation eligibility.

Encapsulates cross-module dependency on the feature_flags module. Hides the
logic for evaluating whether a purchase is eligible for automatic confirmation
based on user-scoped and merchant-scoped feature flags.
"""

from abc import ABC, abstractmethod
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.feature_flags.services import FeatureFlagService
from app.purchases.models import Purchase


class FeatureFlagClientABC(ABC):
    """Abstract interface for feature flag client operations on purchases."""

    @abstractmethod
    async def filter_eligible_purchases(
        self, db: AsyncSession, purchases: List[Purchase]
    ) -> tuple[List[Purchase], int]:
        """Filter purchases eligible for automatic confirmation.

        Evaluates the global, user-scoped, and merchant-scoped
        "purchase_auto_confirm" flags efficiently in a single batch query.
        A purchase is eligible if BOTH user and merchant scopes are enabled
        (or absent, defaulting to True).

        Args:
            db: AsyncSession for database queries
            purchases: List of Purchase models to filter

        Returns:
            (eligible_purchases, ineligible_count) tuple. Logs reasons for
            ineligibility.
        """


class FeatureFlagClient(FeatureFlagClientABC):
    """Modular-monolith implementation — queries feature flags from the shared DB.

    Replace with an HTTP client if the feature_flags module is ever extracted
    to a separate service.
    """

    def __init__(self, feature_flag_service: FeatureFlagService) -> None:
        self._service = feature_flag_service

    async def filter_eligible_purchases(
        self, db: AsyncSession, purchases: List[Purchase]
    ) -> tuple[List[Purchase], int]:
        """Filter purchases eligible for automatic confirmation.

        Returns (eligible_purchases, ineligible_count).
        """
        if not purchases:
            return [], 0

        # Build scope specs: collect all unique (scope_type, scope_id) pairs
        scope_specs = set()
        for purchase in purchases:
            scope_specs.add(("user", str(purchase.user_id)))
            scope_specs.add(("merchant", str(purchase.merchant_id)))

        # Evaluate all scopes in a single batch query
        # Resolution: scoped flag > global flag > fail-open True
        scope_results = await self._service.evaluate_scopes(
            "purchase_auto_confirm", db, list(scope_specs)
        )

        # Evaluate each purchase
        eligible = []
        ineligible = 0
        for purchase in purchases:
            user_scope = ("user", str(purchase.user_id))
            merchant_scope = ("merchant", str(purchase.merchant_id))

            user_enabled = scope_results[user_scope]
            merchant_enabled = scope_results[merchant_scope]

            # Both must be enabled for purchase to be eligible
            if user_enabled and merchant_enabled:
                eligible.append(purchase)
            else:
                ineligible += 1
                if not user_enabled:
                    reason = "user_flag_disabled"
                elif not merchant_enabled:
                    reason = "merchant_flag_disabled"
                else:
                    reason = "unknown"
                logger.debug(
                    "purchase_auto_confirm: purchase ineligible.",
                    extra={"purchase_id": purchase.id, "reason": reason},
                )

        return eligible, ineligible
