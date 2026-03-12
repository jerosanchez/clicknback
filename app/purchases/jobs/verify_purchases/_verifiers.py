"""Purchase verification strategies.

``PurchaseVerifierABC`` is the contract for deciding the outcome of a single
verification attempt: ``confirmed``, ``rejected``, or ``pending`` (soft-fail).
No retry logic lives here — the runner owns retries.  Swap
``SimulatedPurchaseVerifier`` for a real bank-gateway adapter without touching
any orchestration code.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

from app.purchases.models import Purchase


@dataclass(frozen=True)
class VerificationResult:
    """Outcome of a single verification attempt for one purchase.

    Attributes:
        disposition:  ``"confirmed"`` – bank approved the purchase.
                      ``"rejected"``  – hard decline; do not retry (set ``reason``).
                      ``"pending"``   – soft failure; the framework will retry.
        reason:       Human-readable decline reason.  Required when
                      ``disposition == "rejected"``.
    """

    disposition: Literal["confirmed", "rejected", "pending"]
    reason: str | None = None


class PurchaseVerifierABC(ABC):
    """Strategy contract for verifying a pending purchase with the bank.

    Each call to ``verify`` represents one discrete attempt.  The method must
    not perform its own retries or sleep — return ``"pending"`` to signal that
    the framework should retry after ``retry_interval_seconds``.
    """

    @abstractmethod
    async def verify(self, purchase: Purchase, attempt: int) -> VerificationResult:
        """Try to verify one purchase with the bank.

        Args:
            purchase:  The pending purchase to verify.
            attempt:   1-indexed attempt number (1 = first try).

        Returns:
            ``"confirmed"`` if the bank approved the purchase.
            ``"rejected"``  on a hard decline (populate ``reason``).
            ``"pending"``   on a soft failure; the framework will retry.
        """


class SimulatedPurchaseVerifier(PurchaseVerifierABC):
    """Simulates bank reconciliation for development and testing.

    - **Normal merchants**: returns ``"confirmed"`` on every attempt.
    - **Rejection merchant** (``rejection_merchant_id``): always returns
      ``"pending"`` — simulating a bank that never reconciles the transaction.
      The framework retries up to ``max_attempts`` times and then force-rejects.
      Set ``rejection_merchant_id`` to an empty string to disable simulation.
    """

    def __init__(self, *, rejection_merchant_id: str) -> None:
        self._rejection_merchant_id = rejection_merchant_id

    async def verify(self, purchase: Purchase, attempt: int) -> VerificationResult:
        if not (
            self._rejection_merchant_id
            and purchase.merchant_id == self._rejection_merchant_id  # noqa: W503
        ):
            return VerificationResult(disposition="confirmed")

        # Rejection merchant — always soft-fails so the framework exercises retries.
        return VerificationResult(disposition="pending")
