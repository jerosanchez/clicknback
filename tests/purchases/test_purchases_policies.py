import pytest

from app.purchases.clients import MerchantDTO, OfferDTO, UserDTO
from app.purchases.exceptions import (
    MerchantInactiveException,
    MerchantNotFoundException,
    OfferNotAvailableException,
    PurchaseOwnershipViolationException,
    UnsupportedCurrencyException,
    UserInactiveException,
    UserNotFoundException,
)
from app.purchases.policies import (
    enforce_currency_eur,
    enforce_merchant_active,
    enforce_offer_available,
    enforce_purchase_ownership,
    enforce_user_active,
)

# ──────────────────────────────────────────────────────────────────────────────
# enforce_purchase_ownership
# ──────────────────────────────────────────────────────────────────────────────


def test_enforce_purchase_ownership_raises_nothing_on_matching_ids() -> None:
    # Arrange
    user_id = "b7e2c1a2-4f3a-4e2b-9c1a-8d2e3f4b5c6d"

    # Act & Assert — should not raise
    enforce_purchase_ownership(user_id, user_id)


def test_enforce_purchase_ownership_raises_on_mismatched_user_ids() -> None:
    # Arrange
    current_user_id = "b7e2c1a2-4f3a-4e2b-9c1a-8d2e3f4b5c6d"
    other_user_id = "00000000-0000-0000-0000-000000000099"

    # Act & Assert
    with pytest.raises(PurchaseOwnershipViolationException) as exc_info:
        enforce_purchase_ownership(current_user_id, other_user_id)

    assert exc_info.value.current_user_id == current_user_id
    assert exc_info.value.requested_user_id == other_user_id


# ──────────────────────────────────────────────────────────────────────────────
# enforce_user_active
# ──────────────────────────────────────────────────────────────────────────────


def test_enforce_user_active_raises_nothing_on_active_user() -> None:
    # Arrange
    user = UserDTO(id="b7e2c1a2-4f3a-4e2b-9c1a-8d2e3f4b5c6d", active=True)
    user_id = "b7e2c1a2-4f3a-4e2b-9c1a-8d2e3f4b5c6d"

    # Act & Assert — should not raise
    enforce_user_active(user, user_id)


def test_enforce_user_active_raises_on_user_not_found() -> None:
    # Arrange
    user_id = "00000000-0000-0000-0000-000000000001"

    # Act & Assert
    with pytest.raises(UserNotFoundException) as exc_info:
        enforce_user_active(None, user_id)

    assert exc_info.value.user_id == user_id


def test_enforce_user_active_raises_on_inactive_user() -> None:
    # Arrange
    user = UserDTO(id="b7e2c1a2-4f3a-4e2b-9c1a-8d2e3f4b5c6d", active=False)
    user_id = "b7e2c1a2-4f3a-4e2b-9c1a-8d2e3f4b5c6d"

    # Act & Assert
    with pytest.raises(UserInactiveException) as exc_info:
        enforce_user_active(user, user_id)

    assert exc_info.value.user_id == user_id


# ──────────────────────────────────────────────────────────────────────────────
# enforce_merchant_active
# ──────────────────────────────────────────────────────────────────────────────


def test_enforce_merchant_active_raises_nothing_on_active_merchant() -> None:
    # Arrange
    merchant = MerchantDTO(id="a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d", active=True)
    merchant_id = "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"

    # Act & Assert — should not raise
    enforce_merchant_active(merchant, merchant_id)


def test_enforce_merchant_active_raises_on_merchant_not_found() -> None:
    # Arrange
    merchant_id = "00000000-0000-0000-0000-000000000002"

    # Act & Assert
    with pytest.raises(MerchantNotFoundException) as exc_info:
        enforce_merchant_active(None, merchant_id)

    assert exc_info.value.merchant_id == merchant_id


def test_enforce_merchant_active_raises_on_inactive_merchant() -> None:
    # Arrange
    merchant = MerchantDTO(id="a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d", active=False)
    merchant_id = "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"

    # Act & Assert
    with pytest.raises(MerchantInactiveException) as exc_info:
        enforce_merchant_active(merchant, merchant_id)

    assert exc_info.value.merchant_id == merchant_id


# ──────────────────────────────────────────────────────────────────────────────
# enforce_offer_available
# ──────────────────────────────────────────────────────────────────────────────


def test_enforce_offer_available_raises_nothing_on_offer_present() -> None:
    # Arrange
    from datetime import date

    offer = OfferDTO(
        id="f0e1d2c3-b4a5-4678-9012-3456789abcde",
        merchant_id="a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
        active=True,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
    )
    merchant_id = "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"

    # Act & Assert — should not raise
    enforce_offer_available(offer, merchant_id)


def test_enforce_offer_available_raises_on_no_offer() -> None:
    # Arrange
    merchant_id = "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"

    # Act & Assert
    with pytest.raises(OfferNotAvailableException) as exc_info:
        enforce_offer_available(None, merchant_id)

    assert exc_info.value.merchant_id == merchant_id


# ──────────────────────────────────────────────────────────────────────────────
# enforce_currency_eur
# ──────────────────────────────────────────────────────────────────────────────


def test_enforce_currency_eur_raises_nothing_for_eur() -> None:
    # Act & Assert — should not raise
    enforce_currency_eur("EUR")


def test_enforce_currency_eur_is_case_insensitive() -> None:
    # Act & Assert — lowercase and mixed-case should not raise
    enforce_currency_eur("eur")
    enforce_currency_eur("Eur")


@pytest.mark.parametrize("currency", ["USD", "ZZZ", "   ", ""])
def test_enforce_currency_eur_raises_on_unsupported_currency(
    currency: str,
) -> None:
    with pytest.raises(UnsupportedCurrencyException) as exc_info:
        enforce_currency_eur(currency)

    assert exc_info.value.currency == currency
