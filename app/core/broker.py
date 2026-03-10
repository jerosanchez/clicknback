from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Callable, Coroutine
from typing import Any

# A handler is any async callable that accepts a single event object.
# Handlers must be async so they can perform awaitable work (DB writes, HTTP
# calls, etc.) without blocking the event loop.
EventHandler = Callable[[Any], Coroutine[Any, Any, None]]


class MessageBrokerABC(ABC):
    """Contract for publish/subscribe message broker implementations.

    Domain code must only depend on this interface, never on a concrete class.
    Swap InMemoryMessageBroker (see below) for a Kafka, RabbitMQ, or Redis Streams
    adapter simply by changing the binding in the composition root — no domain code
    changes required.

    Event routing is type-based: the class of the published object determines
    which handlers are invoked.  Handlers registered for EventA are never
    invoked when EventB is published.
    """

    @abstractmethod
    def subscribe(self, event_type: type, handler: EventHandler) -> None:
        """Register handler to be called whenever an event of event_type is published.

        The same handler may be registered more than once; it will be called
        once per registration on each publish.
        """

    @abstractmethod
    def unsubscribe(self, event_type: type, handler: EventHandler) -> None:
        """Remove one registration of handler for event_type.

        Raises:
            ValueError: if handler is not currently registered for event_type.
        """

    @abstractmethod
    async def publish(self, event: object) -> None:
        """Dispatch event to every handler registered for its concrete type.

        Handlers are awaited sequentially in registration order.  If a handler
        raises, the exception propagates and subsequent handlers are not called.
        """


class InMemoryMessageBroker(MessageBrokerABC):
    """Async in-memory pub/sub broker for single-process deployments.

    Dispatch model — handlers are awaited sequentially inside publish():
    - Transactional safety: the caller (typically a background job) knows all handlers
      completed before continuing, so a failed handler can be caught and the job can
      react accordingly (retry, rollback, alert) before moving on to the next event.
    - Simplicity: no concurrency or locking concerns within the broker itself,
      so the implementation is straightforward and easy to reason about.
    - Visibility: the caller has full visibility into handler execution and can react
      to failures immediately, rather than relying on out-of-band monitoring or error queues.

    Trade-off: slow handlers delay the job loop.  At MVP scale this is fine;
    replace with a Kafka or RabbitMQ adapter (binding MessageBrokerABC in the
    composition root) if independent handler concurrency becomes a requirement.
    """

    def __init__(self) -> None:
        self._handlers: dict[type, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_type: type, handler: Callable[[Any], Any]) -> None:
        self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: type, handler: Callable[[Any], Any]) -> None:
        # list.remove raises ValueError if handler is not present — intentional
        self._handlers[event_type].remove(handler)

    async def publish(self, event: object) -> None:
        # Iterate over a snapshot so handlers may safely unsubscribe during dispatch
        for handler in list(self._handlers[type(event)]):
            await handler(event)


# Module-level singleton — import and use directly in domain code.
# Override in tests by constructing a fresh InMemoryMessageBroker() per test.
broker: MessageBrokerABC = InMemoryMessageBroker()
