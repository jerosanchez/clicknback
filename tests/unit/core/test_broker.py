from dataclasses import dataclass
from unittest.mock import AsyncMock

import pytest

from app.core.broker import InMemoryMessageBroker, MessageBrokerABC

# ---------------------------------------------------------------------------
# Lightweight event types used only in this test module.
# Using @dataclass keeps them simple and equality-comparable.
# ---------------------------------------------------------------------------


@dataclass
class EventA:
    value: str


@dataclass
class EventB:
    value: str


@pytest.fixture
def broker() -> InMemoryMessageBroker:
    return InMemoryMessageBroker()


# ──────────────────────────────────────────────────────────────────────────────
# InMemoryMessageBroker.subscribe / publish
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_publish_calls_subscribed_handler_on_matching_event(
    broker: InMemoryMessageBroker,
) -> None:
    # Arrange
    handler = AsyncMock()
    event = EventA(value="hello")
    broker.subscribe(EventA, handler)

    # Act
    await broker.publish(event)

    # Assert
    handler.assert_called_once_with(event)


@pytest.mark.asyncio
async def test_publish_calls_all_handlers_on_matching_event(
    broker: InMemoryMessageBroker,
) -> None:
    # Arrange
    handler_1 = AsyncMock()
    handler_2 = AsyncMock()
    event = EventA(value="hello")
    broker.subscribe(EventA, handler_1)
    broker.subscribe(EventA, handler_2)

    # Act
    await broker.publish(event)

    # Assert
    handler_1.assert_called_once_with(event)
    handler_2.assert_called_once_with(event)


@pytest.mark.asyncio
async def test_publish_does_not_call_handler_on_unrelated_event_type(
    broker: InMemoryMessageBroker,
) -> None:
    # Arrange
    handler = AsyncMock()
    broker.subscribe(EventA, handler)

    # Act
    await broker.publish(EventB(value="unrelated"))

    # Assert
    handler.assert_not_called()


@pytest.mark.asyncio
async def test_publish_passes_exact_event_object_to_handler(
    broker: InMemoryMessageBroker,
) -> None:
    # Arrange
    received: list[EventA] = []

    async def capture(event: EventA) -> None:
        received.append(event)

    expected_event = EventA(value="specific_value")
    broker.subscribe(EventA, capture)

    # Act
    await broker.publish(expected_event)

    # Assert
    assert received == [expected_event]


@pytest.mark.asyncio
async def test_publish_does_not_call_handler_when_no_subscribers(
    broker: InMemoryMessageBroker,
) -> None:
    # Arrange — no subscriptions registered
    # Act & Assert — must not raise
    await broker.publish(EventA(value="any"))


# ──────────────────────────────────────────────────────────────────────────────
# InMemoryMessageBroker.unsubscribe
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_unsubscribe_prevents_handler_from_being_called(
    broker: InMemoryMessageBroker,
) -> None:
    # Arrange
    handler = AsyncMock()
    broker.subscribe(EventA, handler)
    broker.unsubscribe(EventA, handler)

    # Act
    await broker.publish(EventA(value="hello"))

    # Assert
    handler.assert_not_called()


def test_unsubscribe_raises_on_unregistered_handler(
    broker: InMemoryMessageBroker,
) -> None:
    # Arrange
    handler = AsyncMock()

    # Act & Assert
    with pytest.raises(ValueError):
        broker.unsubscribe(EventA, handler)


@pytest.mark.asyncio
async def test_unsubscribe_calls_remaining_handlers_after_one_is_removed(
    broker: InMemoryMessageBroker,
) -> None:
    # Arrange
    handler_to_keep = AsyncMock()
    handler_to_remove = AsyncMock()
    event = EventA(value="hello")
    broker.subscribe(EventA, handler_to_keep)
    broker.subscribe(EventA, handler_to_remove)
    broker.unsubscribe(EventA, handler_to_remove)

    # Act
    await broker.publish(event)

    # Assert
    handler_to_keep.assert_called_once_with(event)
    handler_to_remove.assert_not_called()


# ──────────────────────────────────────────────────────────────────────────────
# InMemoryMessageBroker — multiple event types
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_publish_dispatches_independently_per_event_type(
    broker: InMemoryMessageBroker,
) -> None:
    # Arrange
    handler_a = AsyncMock()
    handler_b = AsyncMock()
    event_a = EventA(value="a")
    event_b = EventB(value="b")
    broker.subscribe(EventA, handler_a)
    broker.subscribe(EventB, handler_b)

    # Act
    await broker.publish(event_a)
    await broker.publish(event_b)

    # Assert
    handler_a.assert_called_once_with(event_a)
    handler_b.assert_called_once_with(event_b)


@pytest.mark.asyncio
async def test_handler_subscribed_to_event_a_not_called_when_event_b_published(
    broker: InMemoryMessageBroker,
) -> None:
    # Arrange
    handler_a = AsyncMock()
    broker.subscribe(EventA, handler_a)

    # Act
    await broker.publish(EventB(value="b"))

    # Assert
    handler_a.assert_not_called()


# ──────────────────────────────────────────────────────────────────────────────
# InMemoryMessageBroker — contract conformance
# ──────────────────────────────────────────────────────────────────────────────


def test_in_memory_broker_conforms_to_message_broker_abc() -> None:
    # Act & Assert
    assert isinstance(InMemoryMessageBroker(), MessageBrokerABC)
