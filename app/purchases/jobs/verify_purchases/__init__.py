"""Purchase verification background job.

Periodically discovers pending purchases and verifies them via bank
reconciliation, confirming or rejecting each one asynchronously.

Implements the Fan-Out Dispatcher + Per-Item Runner pattern documented in
ADR-016.  The public entry point is ``make_verify_purchases_task``; everything
else is internal to the package.

Wiring lives in ``app/purchases/composition.py``::

    from app.purchases.jobs.verify_purchases import (
        make_verify_purchases_task,
        SimulatedPurchaseVerifier,
    )
"""

from ._task import make_verify_purchases_task
from ._verifiers import (
    PurchaseVerifierABC,
    SimulatedPurchaseVerifier,
    VerificationResult,
)

__all__ = [
    "make_verify_purchases_task",
    "PurchaseVerifierABC",
    "SimulatedPurchaseVerifier",
    "VerificationResult",
]
