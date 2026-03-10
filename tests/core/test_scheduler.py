import asyncio

import pytest

from app.core.scheduler import InMemoryTaskScheduler, TaskSchedulerABC


@pytest.fixture
def scheduler() -> InMemoryTaskScheduler:
    return InMemoryTaskScheduler()


# ──────────────────────────────────────────────────────────────────────────────
# InMemoryTaskScheduler.cancel — pre-start
# ──────────────────────────────────────────────────────────────────────────────


def test_cancel_raises_key_error_for_unknown_name(
    scheduler: InMemoryTaskScheduler,
) -> None:
    # Act & Assert
    with pytest.raises(KeyError):
        scheduler.cancel("nonexistent_task")


@pytest.mark.asyncio
async def test_task_cancelled_before_start_is_never_called(
    scheduler: InMemoryTaskScheduler,
) -> None:
    # Arrange
    called = asyncio.Event()

    async def task() -> None:
        called.set()

    scheduler.schedule("task", task, interval_seconds=0.0)
    scheduler.cancel("task")

    # Act
    await scheduler.start()
    # Yield to the event loop; the task must not run.
    await asyncio.sleep(0.05)

    # Assert
    assert not called.is_set()
    await scheduler.stop()


# ──────────────────────────────────────────────────────────────────────────────
# InMemoryTaskScheduler.start — task execution
#
# Note on interval accuracy: tests use interval_seconds=0.0 so they run
# without real-time delays.  The exact sleep duration is not asserted here
# because doing so would require either patching asyncio.sleep (coupling the
# test to the loop implementation) or introducing slow real-time waits.
# The correctness of asyncio.sleep's timing is trusted to the standard library.
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_task_is_called_after_start(
    scheduler: InMemoryTaskScheduler,
) -> None:
    # Arrange
    called = asyncio.Event()

    async def task() -> None:
        called.set()

    scheduler.schedule("task", task, interval_seconds=0.0)

    # Act
    await scheduler.start()

    # Assert — asyncio.wait_for protects against hangs if the task never runs
    await asyncio.wait_for(called.wait(), timeout=1.0)
    await scheduler.stop()


@pytest.mark.asyncio
async def test_task_is_called_repeatedly(
    scheduler: InMemoryTaskScheduler,
) -> None:
    # Arrange
    call_count = 0
    enough_calls = asyncio.Event()

    async def task() -> None:
        nonlocal call_count
        call_count += 1
        if call_count >= 3:
            enough_calls.set()

    scheduler.schedule("task", task, interval_seconds=0.0)

    # Act
    await scheduler.start()

    # Assert
    await asyncio.wait_for(enough_calls.wait(), timeout=1.0)
    await scheduler.stop()
    assert call_count >= 3


@pytest.mark.asyncio
async def test_multiple_tasks_run_independently(
    scheduler: InMemoryTaskScheduler,
) -> None:
    # Arrange
    task_a_called = asyncio.Event()
    task_b_called = asyncio.Event()

    async def task_a() -> None:
        task_a_called.set()

    async def task_b() -> None:
        task_b_called.set()

    scheduler.schedule("task_a", task_a, interval_seconds=0.0)
    scheduler.schedule("task_b", task_b, interval_seconds=0.0)

    # Act
    await scheduler.start()

    # Assert — both tasks must run
    await asyncio.wait_for(
        asyncio.gather(task_a_called.wait(), task_b_called.wait()),
        timeout=1.0,
    )
    await scheduler.stop()


# ──────────────────────────────────────────────────────────────────────────────
# InMemoryTaskScheduler.cancel — post-start
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cancel_after_start_stops_task_execution(
    scheduler: InMemoryTaskScheduler,
) -> None:
    # Arrange
    call_count = 0
    first_call = asyncio.Event()

    async def task() -> None:
        nonlocal call_count
        call_count += 1
        first_call.set()

    # Use a non-zero interval so the asyncio task spends time in sleep,
    # giving cancel() a reliable window to inject CancelledError before
    # the next invocation.
    scheduler.schedule("task", task, interval_seconds=0.01)

    # Act
    await scheduler.start()
    await asyncio.wait_for(first_call.wait(), timeout=1.0)
    scheduler.cancel("task")
    count_at_cancel = call_count

    # Yield to the event loop so the cancellation propagates, then confirm
    # no further calls were made.
    await asyncio.sleep(0.05)

    # Assert
    assert call_count == count_at_cancel


# ──────────────────────────────────────────────────────────────────────────────
# InMemoryTaskScheduler.stop
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_stop_halts_all_running_tasks(
    scheduler: InMemoryTaskScheduler,
) -> None:
    # Arrange
    calls: dict[str, int] = {"a": 0, "b": 0}
    task_a_called = asyncio.Event()
    task_b_called = asyncio.Event()

    async def task_a() -> None:
        calls["a"] += 1
        task_a_called.set()

    async def task_b() -> None:
        calls["b"] += 1
        task_b_called.set()

    scheduler.schedule("task_a", task_a, interval_seconds=0.0)
    scheduler.schedule("task_b", task_b, interval_seconds=0.0)
    await scheduler.start()
    await asyncio.wait_for(
        asyncio.gather(task_a_called.wait(), task_b_called.wait()),
        timeout=1.0,
    )

    # Act
    await scheduler.stop()
    count_a, count_b = calls["a"], calls["b"]

    # Yield and confirm both tasks have truly stopped.
    await asyncio.sleep(0.05)

    # Assert
    assert calls["a"] == count_a
    assert calls["b"] == count_b


# ──────────────────────────────────────────────────────────────────────────────
# InMemoryTaskScheduler — contract conformance
# ──────────────────────────────────────────────────────────────────────────────


def test_in_memory_task_scheduler_conforms_to_task_scheduler_abc() -> None:
    # Act & Assert
    assert isinstance(InMemoryTaskScheduler(), TaskSchedulerABC)
