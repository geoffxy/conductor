import pathlib
from typing import NamedTuple
from conductor.task_identifier import TaskIdentifier


class ExecuteTaskResponse(NamedTuple):
    start_timestamp: int
    end_timestamp: int


class MaestroInterface:
    """
    Captures the RPC interface for Maestro. We use this interface to separate
    the gRPC implementation details from Maestro.
    """

    async def unpack_bundle(self, bundle_path: pathlib.Path) -> str:
        raise NotImplementedError

    async def execute_task(
        self,
        workspace_name: str,
        project_root: pathlib.Path,
        task_identifier: TaskIdentifier,
    ) -> ExecuteTaskResponse:
        raise NotImplementedError

    async def shutdown(self, key: str) -> str:
        raise NotImplementedError
