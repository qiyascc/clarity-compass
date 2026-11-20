import asyncio
import logging

from clarity_persistence.jobs import ANALYSIS_QUEUE
from clarity_worker.settings import get_settings
from clarity_worker.tasks import build_jobs


async def main() -> None:
    settings = get_settings()
    jobs = build_jobs(settings)
    async with jobs.open_async():
        await jobs.run_worker_async(queues=[ANALYSIS_QUEUE], concurrency=settings.concurrency)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    asyncio.run(main())
