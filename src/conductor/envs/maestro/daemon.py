import asyncio
import logging
import subprocess
from conductor.envs.maestro.interface import MaestroInterface

logger = logging.getLogger(__name__)


class Maestro(MaestroInterface):
    """
    Maestro is Conductor's remote daemon. It runs within a user-defined
    environment and executes tasks when requested by the main Conductor process.
    """

    def __init__(self, maestro_root: str) -> None:
        self._maestro_root = maestro_root

    async def ping(self, message: str) -> str:
        logger.info("Received ping message: %s", message)
        result = subprocess.run(["uname", "-a"], capture_output=True)
        return result.stdout.decode("utf-8").strip()

    async def shutdown(self, key: str) -> str:
        logger.info("Received shutdown message with key %s", key)
        loop = asyncio.get_running_loop()
        loop.create_task(_orchestrate_shutdown())
        return "OK"


async def _orchestrate_shutdown() -> None:
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
