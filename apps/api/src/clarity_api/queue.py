import uuid
from collections.abc import AsyncIterator
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from typing import Protocol

from procrastinate import App

from clarity_persistence.jobs import ANALYSIS_QUEUE, RUN_ANALYSIS


class RunQueue(Protocol):
    def lifespan(self) -> AbstractAsyncContextManager[None]: ...

    async def enqueue(self, run_id: uuid.UUID) -> None: ...


class JobQueue:
    def __init__(self, app: App) -> None:
        self.app = app

    @asynccontextmanager
    async def lifespan(self) -> AsyncIterator[None]:
        async with self.app.open_async():
            yield

    async def enqueue(self, run_id: uuid.UUID) -> None:
        task = self.app.configure_task(RUN_ANALYSIS, queue=ANALYSIS_QUEUE)
        await task.defer_async(run_id=str(run_id))


class RecordingQueue:
    def __init__(self) -> None:
        self.enqueued: list[uuid.UUID] = []

    @asynccontextmanager
    async def lifespan(self) -> AsyncIterator[None]:
        yield

    async def enqueue(self, run_id: uuid.UUID) -> None:
        self.enqueued.append(run_id)
