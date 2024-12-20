import asyncio
import logging
import pathlib
import time

from conductor.envs.maestro.interface import MaestroInterface, ExecuteTaskResponse
from conductor.config import MAESTRO_WORKSPACE_LOCATION, MAESTRO_WORKSPACE_NAME_FORMAT
from conductor.context import Context
from conductor.task_identifier import TaskIdentifier
from conductor.errors import InternalError

logger = logging.getLogger(__name__)


class Maestro(MaestroInterface):
    """
    Maestro is Conductor's remote daemon. It runs within a user-defined
    environment and executes tasks when requested by the main Conductor process.
    """

    def __init__(self, maestro_root: pathlib.Path) -> None:
        self._maestro_root = maestro_root

    async def unpack_bundle(self, bundle_path: pathlib.Path) -> str:
        bundle_name = bundle_path.stem
        workspace_name = MAESTRO_WORKSPACE_NAME_FORMAT.format(
            name=bundle_name, timestamp=str(int(time.time()))
        )
        abs_workspace_path = (
            self._maestro_root / MAESTRO_WORKSPACE_LOCATION / workspace_name
        )
        abs_workspace_path.mkdir(parents=True, exist_ok=True)
        abs_bundle_path = self._maestro_root / bundle_path
        # N.B. Good practice to use async versions here, but we intend to have
        # only one caller.
        clone_args = ["git", "clone", str(abs_bundle_path), str(abs_workspace_path)]
        logger.debug("Running args: %s", str(clone_args))
        process = await asyncio.create_subprocess_exec(*clone_args)
        await process.wait()
        if process.returncode != 0:
            raise RuntimeError("Failed to unpack the bundle.")
        return workspace_name

    async def execute_task(
        self,
        workspace_name: str,
        project_root: pathlib.Path,
        task_identifier: TaskIdentifier,
    ) -> ExecuteTaskResponse:
        workspace_path = (
            self._maestro_root / MAESTRO_WORKSPACE_LOCATION / workspace_name
        )
        if not workspace_path.exists():
            raise InternalError(details=f"Workspace {workspace_name} does not exist.")

        full_project_root = workspace_path / project_root
        if not full_project_root.exists():
            raise InternalError(
                details=f"Project root {project_root} does not exist in workspace {workspace_name}."
            )

        _ctx = Context(full_project_root)
        start_timestamp = int(time.time())
        # NOTE: Implement task execution.
        end_timestamp = int(time.time())
        return ExecuteTaskResponse(
            start_timestamp=start_timestamp, end_timestamp=end_timestamp
        )

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
