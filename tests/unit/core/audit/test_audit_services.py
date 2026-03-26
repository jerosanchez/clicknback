from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, create_autospec, patch

import pytest

from app.core.audit.enums import AuditAction, AuditActorType, AuditOutcome
from app.core.audit.models import AuditLog
from app.core.audit.repositories import AuditTrailRepositoryABC
from app.core.audit.services import AuditTrail

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def audit_repository() -> MagicMock:
    return create_autospec(AuditTrailRepositoryABC)


@pytest.fixture
def audit_trail(audit_repository: MagicMock) -> AuditTrail:
    return AuditTrail(
        repository=audit_repository,
        datetime_provider=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
    )


@pytest.fixture
def db() -> AsyncMock:
    return AsyncMock()


# ---------------------------------------------------------------------------
# AuditTrail.record — happy paths
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_record_calls_repository_add_exactly_once(
    audit_trail: AuditTrail,
    audit_repository: MagicMock,
    db: AsyncMock,
) -> None:
    # Arrange
    audit_repository.add = AsyncMock()

    # Act
    await audit_trail.record(
        db=db,
        actor_type=AuditActorType.system,
        actor_id=None,
        action=AuditAction.PURCHASE_CONFIRMED,
        resource_type="purchase",
        resource_id="purchase-uuid-123",
        outcome=AuditOutcome.success,
    )

    # Assert
    audit_repository.add.assert_called_once()


@pytest.mark.asyncio
async def test_record_passes_correct_db_to_repository(
    audit_trail: AuditTrail,
    audit_repository: MagicMock,
    db: AsyncMock,
) -> None:
    # Arrange
    audit_repository.add = AsyncMock()

    # Act
    await audit_trail.record(
        db=db,
        actor_type=AuditActorType.system,
        actor_id=None,
        action=AuditAction.PURCHASE_CONFIRMED,
        resource_type="purchase",
        resource_id="purchase-uuid-123",
        outcome=AuditOutcome.success,
    )

    # Assert
    positional_args = audit_repository.add.call_args.args
    # db is the first positional argument
    assert positional_args[0] is db


@pytest.mark.asyncio
async def test_record_builds_audit_log_with_correct_fields(
    audit_trail: AuditTrail,
    audit_repository: MagicMock,
    db: AsyncMock,
) -> None:
    # Arrange
    audit_repository.add = AsyncMock()
    details = {"amount": "99.99", "merchant_id": "merchant-uuid"}

    # Act
    await audit_trail.record(
        db=db,
        actor_type=AuditActorType.admin,
        actor_id="admin-uuid-456",
        action=AuditAction.MERCHANT_ACTIVATED,
        resource_type="merchant",
        resource_id="merchant-uuid-789",
        outcome=AuditOutcome.success,
        details=details,
    )

    # Assert
    _, audit_log = audit_repository.add.call_args.args
    assert isinstance(audit_log, AuditLog)
    assert audit_log.actor_type == AuditActorType.admin.value
    assert audit_log.actor_id == "admin-uuid-456"
    assert audit_log.action == AuditAction.MERCHANT_ACTIVATED.value
    assert audit_log.resource_type == "merchant"
    assert audit_log.resource_id == "merchant-uuid-789"
    assert audit_log.outcome == AuditOutcome.success.value
    assert audit_log.details == details


@pytest.mark.asyncio
async def test_record_sets_actor_id_none_for_system_operations(
    audit_trail: AuditTrail,
    audit_repository: MagicMock,
    db: AsyncMock,
) -> None:
    # Arrange
    audit_repository.add = AsyncMock()

    # Act
    await audit_trail.record(
        db=db,
        actor_type=AuditActorType.system,
        actor_id="random-actor-id-that-should-be-ignored",
        action=AuditAction.PURCHASE_REJECTED,
        resource_type="purchase",
        resource_id="purchase-uuid-999",
        outcome=AuditOutcome.failure,
        details={"reason": "verification_timeout"},
    )

    # Assert
    _, audit_log = audit_repository.add.call_args.args
    assert audit_log.actor_type == AuditActorType.system.value
    assert audit_log.actor_id is None


@pytest.mark.asyncio
async def test_record_sets_occurred_at_as_naive_utc_datetime_with_tz_conversion(
    audit_repository: MagicMock,
    db: AsyncMock,
) -> None:
    from datetime import datetime, timedelta, timezone

    # Simulate a datetime in UTC+2
    # Arrange
    tz = timezone(timedelta(hours=2))
    fake_now = datetime(2023, 1, 1, 12, 0, 0, tzinfo=tz)

    def non_utc_datetime_provider():
        return fake_now

    audit_trail = AuditTrail(
        repository=audit_repository,
        datetime_provider=non_utc_datetime_provider,
    )
    audit_repository.add = AsyncMock()

    # Act
    await audit_trail.record(
        db=db,
        actor_type=AuditActorType.system,
        actor_id=None,
        action=AuditAction.CASHBACK_CREDITED,
        resource_type="wallet",
        resource_id="wallet-uuid-111",
        outcome=AuditOutcome.success,
    )

    # Assert
    _, audit_log = audit_repository.add.call_args.args
    assert isinstance(audit_log.occurred_at, datetime)
    assert audit_log.occurred_at.tzinfo is None

    # The stored value should be the UTC equivalent, naive
    expected_utc = fake_now.astimezone(timezone.utc).replace(tzinfo=None)
    assert audit_log.occurred_at == expected_utc


@pytest.mark.asyncio
async def test_record_stores_details_none_when_not_provided(
    audit_trail: AuditTrail,
    audit_repository: MagicMock,
    db: AsyncMock,
) -> None:
    # Arrange
    audit_repository.add = AsyncMock()

    # Act
    await audit_trail.record(
        db=db,
        actor_type=AuditActorType.system,
        actor_id=None,
        action=AuditAction.PURCHASE_CONFIRMED,
        resource_type="purchase",
        resource_id="purchase-uuid-222",
        outcome=AuditOutcome.success,
    )

    # Assert
    _, audit_log = audit_repository.add.call_args.args
    assert audit_log.details is None


@pytest.mark.asyncio
async def test_record_emits_info_log_with_structured_extra(
    audit_trail: AuditTrail,
    audit_repository: MagicMock,
    db: AsyncMock,
) -> None:
    # Arrange
    audit_repository.add = AsyncMock()

    # Act
    with patch("app.core.audit.services.logger") as mock_logger:
        await audit_trail.record(
            db=db,
            actor_type=AuditActorType.admin,
            actor_id="admin-uuid-456",
            action=AuditAction.WITHDRAWAL_PROCESSED,
            resource_type="payout",
            resource_id="payout-uuid-321",
            outcome=AuditOutcome.success,
            details={"amount": "150.00"},
        )

    # Assert
    mock_logger.info.assert_called_once()
    _, log_kwargs = mock_logger.info.call_args
    extra = log_kwargs["extra"]
    assert extra["actor_type"] == AuditActorType.admin.value
    assert extra["actor_id"] == "admin-uuid-456"
    assert extra["action"] == AuditAction.WITHDRAWAL_PROCESSED.value
    assert extra["resource_type"] == "payout"
    assert extra["resource_id"] == "payout-uuid-321"
    assert extra["outcome"] == AuditOutcome.success.value
    assert extra.get("details") is None  # details are not included in log extra
