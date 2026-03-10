import asyncio
from abc import ABC, abstractmethod
from collections.abc import Callable, Coroutine
from typing import Any

# A scheduled task is any async callable that takes no arguments and returns None.
ScheduledTask = Callable[[], Coroutine[Any, Any, None]]


class TaskSchedulerABC(ABC):
    """Contract for periodic background task schedulers.

    Domain code must only depend on this interface, never on a concrete class.
    Swap InMemoryTaskScheduler for an APScheduler, Celery Beat, or cloud
    scheduler adapter by changing the binding in the composition root.

    Lifecycle:
        1. Call schedule() for each recurring task before startup.
        2. Call start() once the event loop is running (e.g., in the FastAPI
           lifespan on_startup handler).
        3. Call stop() at shutdown (on_shutdown handler) to cancel all tasks
           cleanly.

    Example (FastAPI lifespan)::

        scheduler = InMemoryTaskScheduler()
        scheduler.schedule("verify_purchases", verify_pending_purchases, interval_seconds=30)

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            await scheduler.start()
            yield
            await scheduler.stop()
    """

    @abstractmethod
    def schedule(
        self,
        name: str,
        task: ScheduledTask,
        interval_seconds: float,
    ) -> None:
        """Register an async callable to run on a fixed interval.

        The task is not started immediately; call start() to begin execution.

        Args:
            name:             Unique identifier for this task (used by cancel).
            task:             Async callable with signature ``async def task() -> None``.
            interval_seconds: Wait time between consecutive executions.
        """

    @abstractmethod
    def cancel(self, name: str) -> None:
        """Unregister a task and, if already running, cancel its asyncio Task.

        Raises:
            KeyError: if no task is registered under name.
        """

    @abstractmethod
    async def start(self) -> None:
        """Begin executing all registered tasks on their configured intervals.

        Must be called from inside a running asyncio event loop.
        """

    @abstractmethod
    async def stop(self) -> None:
        """Cancel all running asyncio tasks and clear internal state."""


class InMemoryTaskScheduler(TaskSchedulerABC):
    """asyncio-based in-memory periodic task scheduler.

    Each scheduled task runs inside its own asyncio.Task in a continuous loop:

        while True:
            await task()
            await asyncio.sleep(interval_seconds)

    The loop starts on ``start()`` and is cancelled on ``stop()`` or
    ``cancel(name)``.

    Replace with APScheduler or Celery Beat for production deployments that
    require distributed scheduling, persistence across restarts, or cron
    expressions.
    """

    def __init__(self) -> None:
        self._registered: dict[str, tuple[ScheduledTask, float]] = {}
        self._running: dict[str, asyncio.Task[None]] = {}

    def schedule(
        self,
        name: str,
        task: ScheduledTask,
        interval_seconds: float,
    ) -> None:
        self._registered[name] = (task, interval_seconds)

    def cancel(self, name: str) -> None:
        if name not in self._registered:
            raise KeyError(f"No task registered with name '{name}'.")
        del self._registered[name]
        if name in self._running:
            self._running.pop(name).cancel()

    async def start(self) -> None:
        for name, (task, interval) in self._registered.items():
            self._running[name] = asyncio.create_task(
                self._run_loop(task, interval),
                name=name,
            )

    async def stop(self) -> None:
        for asyncio_task in self._running.values():
            asyncio_task.cancel()
        self._running.clear()

    async def _run_loop(
        self,
        task: ScheduledTask,
        interval_seconds: float,
    ) -> None:
        while True:
            await task()
            await asyncio.sleep(interval_seconds)
