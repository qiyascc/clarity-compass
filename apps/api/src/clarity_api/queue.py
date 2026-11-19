import uuid
from typing import Protocol


class RunQueue(Protocol):
    async def enqueue(self, run_id: uuid.UUID) -> None: ...


class RecordingQueue:
    def __init__(self) -> None:
        self.enqueued: list[uuid.UUID] = []

    async def enqueue(self, run_id: uuid.UUID) -> None:
        self.enqueued.append(run_id)
